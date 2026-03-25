import logging
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.review_model import ManualReview
from src.data.models.postgres.timesheet_model import TimeEntryRaw, Timesheet
from src.data.repositories.audit_log_repository import create_audit_log
from src.data.repositories.manual_review_repository import (
    create_manual_review,
    get_reviews_by_timesheet_id,
)
from src.data.repositories.paycode_repository import get_paycode_by_code
from src.data.repositories.payroll_repository import update_payroll_approval_status
from src.data.repositories.time_entry_repository import (
    create_time_entry,
    get_entries_by_timesheet_id,
)
from src.data.repositories.timesheet_repository import (
    create_timesheet,
    get_all_timesheets,
    get_timesheet_by_id,
    get_timesheets_by_client_id,
    get_timesheets_by_status,
    get_timesheets_with_full_context,
    get_timesheets_with_full_context_by_id,
    get_timesheets_with_full_context_by_status,
    update_timesheet_status,
)
from src.schemas.timesheet_update_schemas import TimesheetUpdate
from src.utils.date_formating import _resolve_entry_date, _resolve_week_ending
from src.utils.payroll_ready_format import _build_payroll_ready_timesheet
from src.utils.time_formatting import _build_datetime
from src.utils.time_sheet_display_formatting import (
    _build_extracted_display,
    _build_extracted_display_list,
)

logger = logging.getLogger(__name__)


async def create_timesheet_from_extraction(
    db: AsyncSession,
    email_message_id: UUID,
    client_id: UUID,
    timesheet_data: dict,
) -> Timesheet:
    """Create a Timesheet record and its associated TimeEntryRaw records."""

    week_ending_str = timesheet_data.get("week_ending")
    week_ending = _resolve_week_ending(week_ending_str) if week_ending_str else None
    if week_ending_str and not week_ending:
        logger.warning("Could not parse week_ending: %s", week_ending_str)

    timesheet = Timesheet(
        email_message_id=email_message_id,
        client_id=client_id,
        week_ending=week_ending,
        status="RECEIVED",
        source="EMAIL",
        extraction_status="EXTRACTED",
        raw_extraction=timesheet_data,
    )
    timesheet = await create_timesheet(db, timesheet)

    entries = timesheet_data.get("entries", [])
    for entry_data in entries:
        actual_date = _resolve_entry_date(entry_data.get("date", ""), week_ending)
        start_time = _build_datetime(actual_date, entry_data.get("start_time"))
        end_time = _build_datetime(actual_date, entry_data.get("end_time"))

        paycode_id = None
        paycode_str = entry_data.get("paycode")
        if paycode_str:
            paycode_obj = await get_paycode_by_code(db, paycode_str)
            if paycode_obj:
                paycode_id = paycode_obj.paycode_id

        time_entry = TimeEntryRaw(
            timesheet_id=timesheet.timesheet_id,
            client_id=client_id,
            start_time=start_time,
            end_time=end_time,
            regular_hours=entry_data.get("total_hours", 0),
            overtime_hours=0,
            double_time_hours=0,
            paycode_id=paycode_id,
        )
        await create_time_entry(db, time_entry)

    logger.info(
        "Created timesheet %s with %d entries",
        timesheet.timesheet_id,
        len(entries),
    )
    return timesheet


async def create_review_for_timesheet(db: AsyncSession, timesheet_id: UUID):
    """Create a ManualReview record in PENDING status for a timesheet."""
    review = ManualReview(
        timesheet_id=timesheet_id,
        status="PENDING",
    )
    return await create_manual_review(db, review)


async def get_all_timesheets_service(db: AsyncSession):
    try:
        logger.info("Fetching all timesheets")
        result = await get_all_timesheets(db)
        logger.info("Fetched %d timesheets", len(result) if result else 0)
        return result
    except Exception:
        logger.exception("Error in get_all_timesheets_service")
        raise


async def get_timesheet_by_id_service(db: AsyncSession, timesheet_id: UUID):
    return await get_timesheet_by_id(db, timesheet_id)


async def get_timesheets_by_client_service(db: AsyncSession, client_id: UUID):
    return await get_timesheets_by_client_id(db, client_id)


async def get_timesheets_by_status_service(db: AsyncSession, status: str):
    return await get_timesheets_by_status(db, status)


async def get_timesheet_entries_service(db: AsyncSession, timesheet_id: UUID):
    return await get_entries_by_timesheet_id(db, timesheet_id)


async def update_status_service(db: AsyncSession, timesheet_id: UUID, status: str):
    return await update_timesheet_status(db, timesheet_id, status)


async def update_timesheet_service(
    db: AsyncSession,
    timesheet_id: UUID,
    payload: TimesheetUpdate,
):
    """Apply partial updates to a timesheet."""
    timesheet = await get_timesheet_by_id(db, timesheet_id)
    if not timesheet:
        msg = "Timesheet not found"
        raise ValueError(msg)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(timesheet, field, value)

    await db.commit()
    await db.refresh(timesheet)
    return timesheet


# Valid statuses that can be submitted for approval
_SUBMITTABLE_STATUSES = {"MATCHED", "UNMATCHED", "RECEIVED", "EXTRACTED"}


async def submit_for_approval_service(db: AsyncSession, timesheet_id: UUID):
    """
    Move a timesheet to READY_FOR_APPROVAL.
    Only timesheets that have been extracted/matched can be submitted.
    """
    timesheet = await get_timesheet_by_id(db, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    if timesheet.status in ("READY_FOR_APPROVAL", "APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=400,
            detail=f"Timesheet is already in status: {timesheet.status}",
        )

    if timesheet.status not in _SUBMITTABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot submit timesheet with status '{timesheet.status}'. "
                f"Must be one of: {', '.join(_SUBMITTABLE_STATUSES)}"
            ),
        )

    timesheet.status = "READY_FOR_APPROVAL"
    await db.flush()

    # Create a ManualReview only if one doesn't already exist for this timesheet
    existing_reviews = await get_reviews_by_timesheet_id(db, timesheet_id)
    if not existing_reviews:
        await create_review_for_timesheet(db, timesheet_id)

    await db.commit()
    await db.refresh(timesheet)
    logger.info("Timesheet %s submitted for approval", timesheet_id)

    await create_audit_log(
        db,
        action="MOVED_TO_APPROVAL",
        entity_type="TIMESHEET",
        entity_id=str(timesheet.timesheet_id),
        metadata_json={
            "previous_status": "EXTRACTED/RECEIVED",
            "new_status": "READY_FOR_APPROVAL",
        },
    )

    return timesheet


# ── Display services (with denormalized names) ──────────────────────────────
async def get_extracted_timesheets_for_display(db: AsyncSession) -> list[dict]:
    """
    Get all extracted timesheets with full context for auditor/admin review.
    Includes employee names, client names, email sender, timestamp.
    """
    timesheets = await get_timesheets_with_full_context(db)
    return _build_extracted_display_list(timesheets)


async def get_extracted_timesheet_by_id_for_display(
    db: AsyncSession, timesheet_id: UUID
) -> dict | None:
    timesheet = await get_timesheets_with_full_context_by_id(db, timesheet_id)
    if not timesheet:
        return None
    return _build_extracted_display(timesheet)


async def decide_timesheet_approval_service(
    db: AsyncSession,
    timesheet_id: UUID,
    decision: str,
    comment: str | None = None,
) -> dict:
    """
    Approve or reject a timesheet that is ready for approval.
    decision: 'APPROVED' or 'REJECTED'
    comment: Optional reviewer comment
    Returns: Updated timesheet display dict
    """

    if decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'APPROVED' or 'REJECTED'",
        )

    timesheet = await get_timesheet_by_id(db, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    if timesheet.status not in ("READY_FOR_APPROVAL", "RECEIVED", "EXTRACTED"):
        raise HTTPException(
            status_code=400,
            detail=(f"Cannot approve/reject timesheet in status: {timesheet.status}"),
        )

    timesheet.status = decision
    if comment:
        timesheet.raw_extraction = timesheet.raw_extraction or {}
        timesheet.raw_extraction["reviewer_comment"] = comment
    timesheet.updated_at = datetime.now()

    # Mirror the decision onto all linked ManualReview records
    reviews = await get_reviews_by_timesheet_id(db, timesheet_id)
    for review in reviews:
        review.status = decision

    if decision == "APPROVED":
        await update_payroll_approval_status(db, True)

    await db.refresh(timesheet)

    logger.info(
        "Timesheet %s %s by reviewer. Comment: %s",
        timesheet_id,
        decision,
        comment,
    )

    await create_audit_log(
        db,
        action=decision,
        entity_type="TIMESHEET",
        entity_id=str(timesheet.timesheet_id),
        metadata_json={"comment": comment},
    )

    return await get_extracted_timesheet_by_id_for_display(db, timesheet_id)


async def get_payroll_ready_timesheets(
    db: AsyncSession,
    status_filter: str | None = None,
) -> list[dict]:
    """
    Get all approved timesheets in payroll-ready format.
    Includes all time entries with calculated totals.
    status_filter: Filter by timesheet status (default: APPROVED)
    """
    if not status_filter:
        status_filter = "APPROVED"

    timesheets = await get_timesheets_with_full_context_by_status(db, status_filter)

    payroll_timesheets = []
    for ts in timesheets:
        pt = _build_payroll_ready_timesheet(ts)
        if pt:
            payroll_timesheets.append(pt)

    return payroll_timesheets
