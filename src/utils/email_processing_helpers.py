async def _handle_non_timesheet(email, classification, processed, db):
    email.processed_status = "COMPLETED"
    await db.flush()
    processed.append(
        {
            "email_id": str(email.email_message_id),
            "classification": classification,
            "status": "COMPLETED",
        }
    )
