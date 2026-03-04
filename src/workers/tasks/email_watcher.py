import logging

from celery import shared_task

from src.core.services.gmail_service import fetch_new_emails

logger = logging.getLogger(__name__)


@shared_task(name="src.workers.tasks.email_watcher.watch_emails")
def watch_emails():
    """
    Celery Beat periodic task (runs every N seconds):
    - Polls Gmail for new emails via History API
    - For each new email, dispatches a process_email task to the processor queue
    - The processor worker picks it up IMMEDIATELY (event-driven, no polling)
    """
    from src.workers.tasks.email_processor import (
        process_email,  # lazy import to avoid circular
    )

    logger.info("Watching for new emails...")

    try:
        messages = fetch_new_emails()
    except Exception as e:
        logger.error(f"Failed to fetch new emails: {e}")
        return {"status": "error", "detail": str(e)}

    if not messages:
        logger.info("No new emails found.")
        return {"status": "ok", "dispatched": 0}

    dispatched = 0

    for msg in messages:
        try:
            gmail_message_id = msg["id"]

            # Dispatch a Celery task — routed to 'processor' queue via celery_app config
            process_email.delay(gmail_message_id)

            logger.info(
                f"Dispatched process_email — gmail_message_id={gmail_message_id}"
            )
            dispatched += 1

        except Exception as e:
            logger.error(f"Error dispatching message {msg.get('id')}: {e}")

    logger.info(f"Done. Dispatched {dispatched} email(s) to processor queue.")
    return {"status": "ok", "dispatched": dispatched}
