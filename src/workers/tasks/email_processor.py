import logging

# mypy: ignore-errors
from celery import shared_task

from src.core.services.email_ingestion import ingest_email_sync
from src.core.services.gmail_service import (
    get_message_detail,
    mark_as_read,
    save_attachments,
)
from src.data.clients.database import SyncSessionLocal

logger = logging.getLogger(__name__)


@shared_task(
    name="src.workers.tasks.email_processor.process_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def process_email(self, gmail_message_id: str):
    """
    Event-driven Celery task — triggered instantly by the watcher.
    Processes a SINGLE email using SYNC DB (psycopg2):
      Gmail detail → upload attachments to GCS → DB ingestion → mark read

    Sits idle when queue is empty. No polling.
    """
    logger.info(f"Processing email — gmail_message_id={gmail_message_id}")

    try:
        # 1. Fetch full message detail from Gmail API
        detail = get_message_detail(gmail_message_id)

        # 2. Upload attachments to GCS (returns list of {filename, gcs_url, mime_type})
        gcs_attachments = save_attachments(detail)

        # 3. Ingest into DB using sync session (with GCS URLs)
        db = SyncSessionLocal()
        try:
            ingested = ingest_email_sync(detail, db, gcs_attachments=gcs_attachments)
        finally:
            db.close()

        # Only mark read if email was actually ingested
        if ingested:
            # 4. Mark as read in Gmail
            mark_as_read(gmail_message_id)

        logger.info(f"Successfully processed — gmail_message_id={gmail_message_id}")
        return {"status": "ok", "gmail_message_id": gmail_message_id}

    except Exception as e:
        logger.error(f"Error processing email {gmail_message_id}: {e}")
        raise self.retry(exc=e) from e
