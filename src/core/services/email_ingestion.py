from src.core.services.gcs_service import upload_to_gcs
from src.core.services.gmail_service import extract_email_metadata
from src.data.models.postgres.email_model import (
    EmailAttachment,
    EmailMessage,
    EmailThread,
    ProcessedStatus,
)
from src.data.repositories.client_repository import (
    get_client_by_client_id,
    get_client_by_client_id_sync,
)
from src.data.repositories.email_repository import (
    commit_session,
    commit_session_sync,
    create_email_attachment,
    create_email_attachment_sync,
    create_email_message,
    create_email_message_sync,
    create_email_thread,
    create_email_thread_sync,
    get_email_message_by_message_id,
    get_email_message_by_message_id_sync,
    get_email_thread_by_gmail_id,
    get_email_thread_by_gmail_id_sync,
    get_first_message_by_thread_id,
    get_first_message_by_thread_id_sync,
)
from src.data.repositories.email_whitelist_repository import (
    get_whitelisted_client,
    get_whitelisted_client_sync,
)
from src.observability.logging.logging import get_logger
from src.utils.email_helper import _extract_sender, _resolve_body

logger = get_logger(__name__)


def _build_gcs_lookup(gcs_attachments: list[dict] | None) -> dict[str, dict]:
    """
    Build a filename → {gcs_url, mime_type} mapping from the list
    returned by ``save_attachments``.
    """
    if not gcs_attachments:
        return {}
    return {att["filename"]: att for att in gcs_attachments}


async def ingest_email(detail, db, *, gcs_attachments: list[dict] | None = None):
    """Async version — used by FastAPI."""
    logger.info("Starting async email ingestion")

    try:
        email_data = extract_email_metadata(detail)
        sender = _extract_sender(email_data)

        logger.info(
            f"Processing email message_id={email_data['message_id']}"
            " from sender={sender}"
        )

        # Check whitelist
        client_id = await get_whitelisted_client(sender, db)
        if not client_id:
            logger.warning(f"Sender not whitelisted: {sender}")
            return

        # Fetch client
        client = await get_client_by_client_id(client_id, db)
        logger.info(f"Mapped sender={sender} to client_id={client.client_id}")

        # Get or create thread
        thread = await get_email_thread_by_gmail_id(email_data["thread_id"], db)
        if not thread:
            logger.info(
                f"Creating new thread for gmail_thread_id={email_data['thread_id']}"
            )
            thread = await create_email_thread(
                EmailThread(
                    gmail_thread_id=email_data["thread_id"],
                    subject=email_data["subject"],
                    client_id=client.client_id,
                ),
                db,
            )

        # Prevent duplicate message
        if await get_email_message_by_message_id(email_data["message_id"], db):
            logger.warning(
                f"Duplicate message ignored: message_id={email_data['message_id']}"
            )
            return

        # Detect reply
        is_reply_flag = bool(await get_first_message_by_thread_id(thread.thread_id, db))
        logger.info(
            f"is_reply={is_reply_flag} for message_id={email_data['message_id']}"
        )

        # Save message
        message = await create_email_message(
            EmailMessage(
                thread_id=thread.thread_id,
                message_id=email_data["message_id"],
                sender_email=sender,
                subject=email_data["subject"],
                body=_resolve_body(email_data),
                is_reply=is_reply_flag,
                processed_status=ProcessedStatus.INGESTED,
            ),
            db,
        )

        logger.info(f"Email message saved: id={message.email_message_id}")

        # ── Save attachments (GCS URLs or upload on the fly) ──
        gcs_lookup = _build_gcs_lookup(gcs_attachments)

        for attachment in email_data["attachments"]:
            filename = attachment["filename"]
            mime_type = attachment.get("mimeType", "application/octet-stream")

            if filename in gcs_lookup:
                # GCS URLs already available (worker pre-uploaded)
                file_path = gcs_lookup[filename]["gcs_url"]
                mime_type = gcs_lookup[filename].get("mime_type", mime_type)
            else:
                # Fallback: upload inline (shouldn't happen in normal flow)
                file_path = upload_to_gcs(b"", filename, mime_type)

            logger.debug(f"Saving attachment: {filename} → {file_path}")
            await create_email_attachment(
                EmailAttachment(
                    email_message_id=message.email_message_id,
                    file_name=filename,
                    file_type=mime_type,
                    file_path=file_path,
                ),
                db,
            )

        await commit_session(db)
        logger.info(
            f"""Email ingestion completed successfully:
            message_id={email_data["message_id"]}"""
        )

    except Exception:
        logger.error("Error during async email ingestion", exc_info=True)
        raise


def ingest_email_sync(detail, db, *, gcs_attachments: list[dict] | None = None):
    """Sync version — used by Celery processor worker."""
    logger.info("Starting sync email ingestion")
    try:
        email_data = extract_email_metadata(detail)
        sender = _extract_sender(email_data)

        logger.info(f"""Processing email message_id={email_data["message_id"]}
                     from sender={sender}""")

        # Check whitelist
        client_id = get_whitelisted_client_sync(sender, db)
        if not client_id:
            logger.warning(f"Sender not whitelisted: {sender}")
            return False

        # Fetch client
        client = get_client_by_client_id_sync(client_id, db)
        logger.info(f"[SYNC] Mapped sender={sender} to client_id={client.client_id}")

        # Get or create thread
        thread = get_email_thread_by_gmail_id_sync(email_data["thread_id"], db)
        if not thread:
            logger.info(f"""[SYNC] Creating new thread for
                         gmail_thread_id={email_data["thread_id"]}""")
            thread = create_email_thread_sync(
                EmailThread(
                    gmail_thread_id=email_data["thread_id"],
                    subject=email_data["subject"],
                    client_id=client.client_id,
                ),
                db,
            )

        # Prevent duplicate message
        if get_email_message_by_message_id_sync(email_data["message_id"], db):
            logger.warning(f"""[SYNC] Duplicate message ignored:
                               message_id={email_data["message_id"]}""")
            return False

        # Detect reply
        is_reply_flag = bool(get_first_message_by_thread_id_sync(thread.thread_id, db))
        logger.info(f""" is_reply={is_reply_flag}
                     for message_id={email_data["message_id"]}""")

        # Save message
        message = create_email_message_sync(
            EmailMessage(
                thread_id=thread.thread_id,
                message_id=email_data["message_id"],
                sender_email=sender,
                subject=email_data["subject"],
                body=_resolve_body(email_data),
                is_reply=is_reply_flag,
                processed_status=ProcessedStatus.INGESTED,
            ),
            db,
        )
        logger.info(f"Email message saved: id={message.email_message_id}")

        # ── Save attachments (GCS URLs) ──
        gcs_lookup = _build_gcs_lookup(gcs_attachments)

        for attachment in email_data["attachments"]:
            filename = attachment["filename"]
            mime_type = attachment.get("mimeType", "application/octet-stream")

            if filename in gcs_lookup:
                file_path = gcs_lookup[filename]["gcs_url"]
                mime_type = gcs_lookup[filename].get("mime_type", mime_type)
            else:
                file_path = upload_to_gcs(b"", filename, mime_type)

            logger.debug(f" Saving attachment: {filename} → {file_path}")
            create_email_attachment_sync(
                EmailAttachment(
                    email_message_id=message.email_message_id,
                    file_name=filename,
                    file_type=mime_type,
                    file_path=file_path,
                ),
                db,
            )

        commit_session_sync(db)
        logger.info(f"""Email ingestion completed successfully:
                    message_id={email_data["message_id"]}""")
        return True
    except Exception:
        logger.error("Error during sync email ingestion", exc_info=True)
        return False
