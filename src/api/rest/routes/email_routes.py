from fastapi import APIRouter

from src.core.services.gmail_service import fetch_new_emails, get_message_detail, mark_as_read, save_attachments


email_router = APIRouter(tags=["email"])


@email_router.get("/fetch-emails")
def fetch_emails():
    messages = fetch_new_emails()

    for msg in messages:
        detail = get_message_detail(msg["id"])
        save_attachments(detail)
        mark_as_read(msg["id"])
        print(detail)

    return {"status": "Processed", "count": len(messages)}