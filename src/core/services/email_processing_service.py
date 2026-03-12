import logging

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.control.agents.email_graph import email_processing_graph
from src.core.services.process_timesheet_service import process_timesheet
from src.data.repositories.email_repository import (
    get_email_message_ingested,
    get_failed_processed_emails,
)
from src.utils.email_processing_helpers import _handle_non_timesheet

logger = logging.getLogger(__name__)


async def process_unprocessed_emails(db: AsyncSession):
    """
    Process all INGESTED emails through the full pipeline:
    1. Run LangGraph (load → extract attachments → classify → extract timesheet)
    2. If TIMESHEET: create timesheet, match employees, create review
    3. If OTHER: mark as COMPLETED
    """

    try:
        emails = await get_email_message_ingested(db)
        processed = []
        failed = []

        for email in emails:
            try:
                # ── Step 1: Mark as CLASSIFYING ──
                email.processed_status = "CLASSIFYING"
                email.last_error = None
                await db.flush()

                # ── Step 2: Run LangGraph ──
                output = await email_processing_graph.ainvoke(
                    {"email_id": str(email.email_message_id), "db": db}
                )

                # Check for agent errors
                if output.get("error"):
                    raise RuntimeError(output["error"])

                classification = output.get("classification", "OTHER")
                email.classification = classification

                # ──  Handle non-timesheet ──
                if classification != "TIMESHEET":
                    await _handle_non_timesheet(email, classification, processed, db)
                    continue

                # ----Handle timesheet ---
                timesheet = process_timesheet(email, output, db)

                processed.append(
                    {
                        "email_id": str(email.email_message_id),
                        "classification": "TIMESHEET",
                        "timesheet_id": str(timesheet.timesheet_id),
                        "timesheet_status": timesheet.status,
                    }
                )

            except Exception as e:
                logger.exception(
                    "Processing failed for email %s", email.email_message_id
                )
                email.processed_status = "FAILED"
                email.last_error = str(e)
                email.retry_count = (email.retry_count or 0) + 1
                await db.flush()
                failed.append(
                    {
                        "email_id": str(email.email_message_id),
                        "error": str(e),
                    }
                )

        await db.commit()

        return {
            "processed_count": len(processed),
            "failed_count": len(failed),
            "processed": processed,
            "failed": failed,
        }

    except Exception:
        logger.exception("Bulk processing failed")
        raise


async def reprocess_failed_emails(db: AsyncSession):
    """
    Reset all FAILED emails to INGESTED and re-run the full pipeline.
    Returns same structure as process_unprocessed_emails.
    """
    try:
        result = await get_failed_processed_emails(db)
        failed_emails = result.scalars().all()

        if not failed_emails:
            return {
                "processed_count": 0,
                "failed_count": 0,
                "processed": [],
                "failed": [],
                "message": "No failed emails found to reprocess",
            }

        # Reset to INGESTED so process_unprocessed_emails picks them up
        for email in failed_emails:
            email.processed_status = "INGESTED"
            email.last_error = None
        await db.flush()

        logger.info("Reprocessing %d failed emails", len(failed_emails))
        return await process_unprocessed_emails(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
