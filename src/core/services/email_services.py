from fastapi import HTTPException

from src.data.repositories.email_repository import (
    get_all_emailmessages,
    get_attachments,
    get_email_message_ingested,
)
from src.observability.logging.logging import get_logger
from src.schemas.email_schemas import EmailAttachmentResponse, EmailMessageResponse

logger = get_logger(__name__)


async def get_all_emails_service(db):
    logger.info("Fetching all emails with attachments")

    try:
        emails = await get_all_emailmessages(db)
        logger.info(f"Fetched {len(emails)} emails")

        enriched: list[EmailMessageResponse] = []

        for email in emails:
            logger.debug(f"Enriching email_id={email.email_message_id}")

            attachments = await get_attachments(email.email_message_id, db)

            logger.debug(
                f"""Found {len(attachments)} attachments
                for email_id={email.email_message_id}"""
            )

            enriched.append(
                EmailMessageResponse(
                    **email.__dict__,
                    attachments=[
                        EmailAttachmentResponse(**att.__dict__) for att in attachments
                    ],
                )
            )

        logger.info(f"Successfully enriched {len(enriched)} emails")
        return enriched

    except Exception as e:
        logger.error("Error fetching all emails", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_ingested_emails_service(db):
    logger.info("Fetching INGESTED emails")
    try:
        emails = await get_email_message_ingested(db)

        logger.info(f"Fetched {len(emails)} INGESTED emails")
        return emails
    except Exception as e:
        logger.error("Error fetching INGESTED emails", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
