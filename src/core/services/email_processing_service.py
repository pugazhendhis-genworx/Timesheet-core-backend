import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.control.agents.email_graph import email_processing_graph
from src.core.services.employee_matching_service import (
    match_employees_for_timesheet,
    validate_client_for_timesheet,
)
from src.core.services.timesheet_service import (
    create_review_for_timesheet,
    create_timesheet_from_extraction,
)
from src.data.models.postgres.email_model import EmailMessage, EmailThread
from src.data.repositories.email_repository import (
    get_email_message_ingested,
)

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

                # ── Step 3: Handle non-timesheet ──
                if classification != "TIMESHEET":
                    email.processed_status = "COMPLETED"
                    await db.flush()
                    processed.append(
                        {
                            "email_id": str(email.email_message_id),
                            "classification": classification,
                            "status": "COMPLETED",
                        }
                    )
                    continue

                # ── Step 4: Mark as EXTRACTING ──
                email.processed_status = "EXTRACTING"
                await db.flush()

                timesheet_data = output.get("timesheet_data")
                if not timesheet_data:
                    raise RuntimeError(
                        "LangGraph returned TIMESHEET but no extraction data"
                    )

                # Resolve client_id from the LangGraph output or email thread
                client_id = output.get("client_id")
                if not client_id and email.thread_id:
                    # Fallback: query thread's client_id via FK
                    result = await db.execute(
                        select(EmailThread.client_id).where(
                            EmailThread.thread_id == email.thread_id
                        )
                    )
                    thread_client_id = result.scalar_one_or_none()
                    if thread_client_id:
                        client_id = str(thread_client_id)

                if not client_id:
                    raise RuntimeError("Could not resolve client_id for timesheet")

                # ── Step 5: Create timesheet + time entries ──
                timesheet = await create_timesheet_from_extraction(
                    db=db,
                    email_message_id=email.email_message_id,
                    client_id=UUID(client_id),
                    timesheet_data=timesheet_data,
                )

                # ── Step 6: Employee matching ──
                await match_employees_for_timesheet(
                    db=db,
                    timesheet_id=timesheet.timesheet_id,
                    raw_extraction=timesheet_data,
                )

                # ── Step 6.5: Client validation ──
                await validate_client_for_timesheet(
                    db=db,
                    timesheet_id=timesheet.timesheet_id,
                    raw_extraction=timesheet_data,
                )

                # ── Step 7: Create manual review ──
                await create_review_for_timesheet(db, timesheet.timesheet_id)

                # ── Step 8: Mark email as COMPLETED ──
                email.processed_status = "COMPLETED"
                await db.flush()

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
    result = await db.execute(
        select(EmailMessage).where(EmailMessage.processed_status == "FAILED")
    )
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
