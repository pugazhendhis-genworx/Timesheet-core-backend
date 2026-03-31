from src.core.services.gmail_service import mark_as_unread


async def _handle_non_timesheet(email, classification, processed, db):
    email.processed_status = "COMPLETED"
    await db.flush()
    mark_as_unread(email.message_id)
    processed.append(
        {
            "email_id": str(email.email_message_id),
            "classification": classification,
            "status": "COMPLETED",
        }
    )
