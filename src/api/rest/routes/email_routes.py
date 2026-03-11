from fastapi import APIRouter, Depends, Query

from src.api.rest.dependencies import get_pg_session
from src.core.services.email_services import get_all_emails_service
from src.core.services.gmail_service import (
    fetch_new_emails,
    get_message_detail,
    mark_as_read,
    save_attachments,
)
from src.schemas.email_schemas import EmailMessageResponse

email_router = APIRouter(tags=["email"])


@email_router.get("/get-emails", response_model=list[EmailMessageResponse])
async def get_emails(
    classification: str | None = Query(
        default=None,
        description=(
            "Optional filter, e.g. 'timesheet' "
            "to return only timesheet emails."
        ),
    ),
    db=Depends(get_pg_session),
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


@email_router.get("/fetch-emails")
def fetch_emails():
    messages = fetch_new_emails()

    for msg in messages:
        detail = get_message_detail(msg["id"])
        save_attachments(detail)
        mark_as_read(msg["id"])
        print(detail)

    return {"status": "Processed", "count": len(messages)}
