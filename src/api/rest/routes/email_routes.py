from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from src.api.rest.dependencies import DBSession
from src.core.services.email_services import (
    get_all_emails_service,
    get_email_by_id_service,
)
from src.core.services.gmail_service import (
    fetch_new_emails,
    get_message_detail,
    mark_as_read,
    save_attachments,
)
from src.schemas.email_schemas import EmailMessageResponse

email_router = APIRouter(
    tags=["email"],
)


@email_router.get("/get-emails", response_model=list[EmailMessageResponse])
async def get_emails(
    db: DBSession,
    classification: Annotated[
        str | None,
        Query(
            description="Optional filter, e.g. 'timesheet' to return only timesheet "
            "emails."
        ),
    ] = None,
):
    emails = await get_all_emails_service(db)
    if classification:
        classification_lower = classification.lower()
        return [
            e
            for e in emails
            if (e.classification or "").lower() == classification_lower
        ]
    return emails


@email_router.get("/get-email/{email_id}", response_model=EmailMessageResponse)
async def get_email_by_id(email_id: UUID, db: DBSession):
    """Fetch a single email by its UUID, with attachments."""
    return await get_email_by_id_service(email_id, db)


@email_router.get("/fetch-emails")
def fetch_emails():
    messages = fetch_new_emails()

    for msg in messages:
        detail = get_message_detail(msg["id"])
        save_attachments(detail)
        mark_as_read(msg["id"])
        print(detail)

    return {"status": "Processed", "count": len(messages)}
