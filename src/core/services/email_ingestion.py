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


def _extract_sender(email_data: dict) -> str:
    """Extract clean sender email from email metadata."""
    sender = email_data["from"]
    if "<" in sender:
        sender = sender.split("<")[1].replace(">", "").strip()
    return sender


def _resolve_body(email_data: dict) -> str:
    """Resolve email body with fallback: plain → html → snippet."""
    return (
        email_data["body_plain"]
        or email_data["body_html"]
        or email_data.get("snippet", "")
    )


async def ingest_email(detail, db):
    """Async version — used by FastAPI."""
    email_data = extract_email_metadata(detail)
    sender = _extract_sender(email_data)

    # Check whitelist
    client_id = await get_whitelisted_client(sender, db)
    if not client_id:
        print(" Sender not whitelisted:", sender)
        return

    # Fetch client
    client = await get_client_by_client_id(client_id, db)

    # Get or create thread
    thread = await get_email_thread_by_gmail_id(email_data["thread_id"], db)
    if not thread:
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
        print("Duplicate message ignored")
        return

    # Detect reply
    is_reply_flag = bool(await get_first_message_by_thread_id(thread.thread_id, db))

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

    # Save attachments
    for attachment in email_data["attachments"]:
        await create_email_attachment(
            EmailAttachment(
                email_message_id=message.email_message_id,
                file_name=attachment["filename"],
                file_type=attachment["mimeType"],
                file_path=f"attachments/{attachment['filename']}",
            ),
            db,
        )

    await commit_session(db)
    print("Email ingested successfully")


def ingest_email_sync(detail, db):
    """Sync version — used by Celery processor worker."""
    email_data = extract_email_metadata(detail)
    sender = _extract_sender(email_data)

    # Check whitelist
    client_id = get_whitelisted_client_sync(sender, db)
    if not client_id:
        print(" Sender not whitelisted:", sender)
        return False

    # Fetch client
    client = get_client_by_client_id_sync(client_id, db)

    # Get or create thread
    thread = get_email_thread_by_gmail_id_sync(email_data["thread_id"], db)
    if not thread:
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
        print("Duplicate message ignored")
        return False

    # Detect reply
    is_reply_flag = bool(get_first_message_by_thread_id_sync(thread.thread_id, db))

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

    # Save attachments
    for attachment in email_data["attachments"]:
        create_email_attachment_sync(
            EmailAttachment(
                email_message_id=message.email_message_id,
                file_name=attachment["filename"],
                file_type=attachment["mimeType"],
                file_path=f"attachments/{attachment['filename']}",
            ),
            db,
        )

    commit_session_sync(db)
    print("Email ingested successfully (sync)")
    return True
