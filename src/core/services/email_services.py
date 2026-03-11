from fastapi import HTTPException
from sqlalchemy import select

from src.data.models.postgres.email_model import EmailMessage
from src.data.repositories.email_repository import (
    get_attachments,
    get_email_message_ingested,
)
from src.schemas.email_schemas import EmailAttachmentResponse, EmailMessageResponse


async def get_all_emails_service(db):
    try:
        result = await db.execute(select(EmailMessage))
        emails = result.scalars().all()
        enriched: list[EmailMessageResponse] = []
        for email in emails:
            attachments = await get_attachments(email.email_message_id, db)
            enriched.append(
                EmailMessageResponse(
                    **email.__dict__,
                    attachments=[
                        EmailAttachmentResponse(**att.__dict__) for att in attachments
                    ],
                )
            )
        return enriched
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_ingested_emails_service(db):
    try:
        return await get_email_message_ingested(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
