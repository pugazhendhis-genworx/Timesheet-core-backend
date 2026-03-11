import logging
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.data.models.postgres.review_model import ManualReview
from src.data.models.postgres.timesheet_model import TimeEntryRaw, Timesheet
from src.data.repositories.manual_review_repository import (
    create_manual_review,
    get_reviews_by_timesheet_id,
)
from src.data.repositories.paycode_repository import get_paycode_by_code
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
    update_timesheet_status,
)
from src.schemas.timesheet_update_schemas import TimesheetUpdate

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
            regular_hours=entry_data.get("regular_hours", 0),
            overtime_hours=entry_data.get("overtime_hours", 0),
            double_time_hours=entry_data.get("double_time_hours", 0),
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
    return await get_all_timesheets(db)


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
    from fastapi import HTTPException

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
    await db.commit()
    await db.refresh(timesheet)
    logger.info("Timesheet %s submitted for approval", timesheet_id)
    return timesheet


_DAY_NAME_INDEX: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%m-%d-%Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
)

_TIME_FORMATS = ("%I:%M %p", "%H:%M", "%I:%M%p", "%H:%M:%S", "%I %p")


def _resolve_week_ending(date_str: str) -> date | None:
    """Parse a week_ending string across multiple common formats."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _resolve_entry_date(date_str: str, week_ending: date | None) -> date | None:
    """
    Resolve an entry date string to an actual calendar date.
    Handles day names ('Monday') by anchoring to week_ending,
    and explicit date strings ('2026-03-03') by direct parsing.
    """
    if not date_str:
        return None
    key = date_str.strip().lower()
    if key in _DAY_NAME_INDEX:
        if week_ending is None:
            return None
        # Find Monday of the week that contains week_ending
        monday = week_ending - timedelta(days=week_ending.weekday())
        return monday + timedelta(days=_DAY_NAME_INDEX[key])
    return _resolve_week_ending(date_str)


def _parse_time(time_str: str) -> datetime | None:
    """Parse time strings like '8:00 AM', '07:30 AM', '17:00'."""
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(time_str.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _build_datetime(actual_date: date | None, time_str: str | None) -> datetime | None:
    """Combine a resolved date with a time string into a timezone-naive datetime."""
    if not actual_date or not time_str or not time_str.strip():
        return None
    parsed = _parse_time(time_str.strip())
    if parsed is None:
        return None
    return datetime.combine(actual_date, parsed.time())


# ── Display services (with denormalized names) ──────────────────────────────
async def get_extracted_timesheets_for_display(db: AsyncSession) -> list[dict]:
    """
    Get all extracted timesheets with full context for auditor/admin review.
    Includes employee names, client names, email sender, timestamp.
    """
    stmt = (
        select(Timesheet)
        .options(
            joinedload(Timesheet.email_message),
            joinedload(Timesheet.client),
            joinedload(Timesheet.entries).joinedload(TimeEntryRaw.employee),
            joinedload(Timesheet.entries).joinedload(TimeEntryRaw.paycode),
        )
        .where(Timesheet.extraction_status == "EXTRACTED")
    )
    result = await db.execute(stmt)
    timesheets = result.unique().scalars().all()
    return _build_extracted_display_list(timesheets)


async def get_extracted_timesheet_by_id_for_display(
    db: AsyncSession, timesheet_id: UUID
) -> dict | None:
    """Get a single extracted timesheet with full display context."""
    stmt = (
        select(Timesheet)
        .options(
            joinedload(Timesheet.email_message),
            joinedload(Timesheet.client),
            joinedload(Timesheet.entries).joinedload(TimeEntryRaw.employee),
            joinedload(Timesheet.entries).joinedload(TimeEntryRaw.paycode),
        )
        .where(Timesheet.timesheet_id == timesheet_id)
    )
    result = await db.execute(stmt)
    timesheet = result.unique().scalar_one_or_none()
    if not timesheet:
        return None
    return _build_extracted_display(timesheet)


def _build_extracted_display(timesheet: Timesheet) -> dict:
    """Build display dict for a single extracted timesheet."""
    email = timesheet.email_message
    client = timesheet.client

    entries_display = []
    for entry in timesheet.entries:
        emp = entry.employee
        pc = entry.paycode
        entries_display.append(
            {
                "timeentry_id": str(entry.timeentry_id),
                "employee_id": str(entry.employee_id) if entry.employee_id else None,
                "employee_name": f"{emp.first_name} {emp.last_name}" if emp else None,
                "client_id": str(entry.client_id),
                "client_name": client.client_name if client else "—",
                "start_time": entry.start_time.isoformat()
                if entry.start_time
                else None,
                "end_time": entry.end_time.isoformat() if entry.end_time else None,
                "regular_hours": float(entry.regular_hours)
                if entry.regular_hours
                else 0,
                "overtime_hours": float(entry.overtime_hours)
                if entry.overtime_hours
                else 0,
                "double_time_hours": float(entry.double_time_hours)
                if entry.double_time_hours
                else 0,
                "paycode_id": str(entry.paycode_id) if entry.paycode_id else None,
                "paycode_code": pc.paycode if pc else None,
                # Matching outcome fields
                "matching_status": entry.matching_status or "MATCHED",
                "employee_unmatched_reason": entry.employee_unmatched_reason,
                "client_unmatched_reason": entry.client_unmatched_reason,
                "match_confidence": float(entry.match_confidence)
                if entry.match_confidence
                else None,
            }
        )

    return {
        "timesheet_id": str(timesheet.timesheet_id),
        "email_message_id": str(timesheet.email_message_id),
        "sender_email": email.sender_email if email else "—",
        "received_at": email.received_at.isoformat() if email else None,
        "client_id": str(timesheet.client_id),
        "client_name": client.client_name if client else "—",
        "week_ending": (
            timesheet.week_ending.isoformat() if timesheet.week_ending else None
        ),
        "status": timesheet.status,
        "extraction_status": timesheet.extraction_status,
        "extraction_confidence": (
            float(timesheet.extraction_confidence)
            if timesheet.extraction_confidence
            else None
        ),
        "entries": entries_display,
        "updated_at": (
            timesheet.updated_at.isoformat() if timesheet.updated_at else None
        ),
    }


def _build_extracted_display_list(timesheets: list[Timesheet]) -> list[dict]:
    """Build display list for multiple extracted timesheets."""
    return [_build_extracted_display(ts) for ts in timesheets]


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
    from fastapi import HTTPException

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

    await db.commit()
    await db.refresh(timesheet)

    logger.info(
        "Timesheet %s %s by reviewer. Comment: %s",
        timesheet_id,
        decision,
        comment,
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

    stmt = (
        select(Timesheet)
        .options(
            joinedload(Timesheet.email_message),
            joinedload(Timesheet.client),
            joinedload(Timesheet.entries).joinedload(TimeEntryRaw.employee),
            joinedload(Timesheet.entries).joinedload(TimeEntryRaw.paycode),
        )
        .where(Timesheet.status == status_filter)
    )
    result = await db.execute(stmt)
    timesheets = result.unique().scalars().all()

    payroll_timesheets = []
    for ts in timesheets:
        pt = _build_payroll_ready_timesheet(ts)
        if pt:
            payroll_timesheets.append(pt)

    return payroll_timesheets


def _build_payroll_ready_timesheet(timesheet: Timesheet) -> dict | None:
    """
    Build payroll-ready timesheet with all entries and totals.
    """
    if not timesheet.entries:
        return None  # Skip timesheets with no entries

    entries_data = []
    total_regular = 0
    total_overtime = 0
    total_double_time = 0

    for entry in timesheet.entries:
        emp = entry.employee
        if not emp:
            continue  # Skip entries without employee

        regular_hours = float(entry.regular_hours or 0)
        overtime_hours = float(entry.overtime_hours or 0)
        double_time_hours = float(entry.double_time_hours or 0)

        total_regular += regular_hours
        total_overtime += overtime_hours
        total_double_time += double_time_hours

        # Use default rates if not specified in entry
        regular_rate = float(entry.regular_rate or 0)
        overtime_rate = float(entry.overtime_rate or 0)
        double_time_rate = float(entry.double_time_rate or 0)

        entry_total = (
            regular_hours * regular_rate
            + overtime_hours * overtime_rate
            + double_time_hours * double_time_rate
        )

        entries_data.append(
            {
                "timeentry_id": str(entry.timeentry_id),
                "employee_name": f"{emp.first_name} {emp.last_name}",
                "employee_email": emp.emp_email,
                "date": (entry.start_time.isoformat() if entry.start_time else None),
                "regular_hours": regular_hours,
                "regular_rate": regular_rate,
                "regular_total": regular_hours * regular_rate,
                "overtime_hours": overtime_hours,
                "overtime_rate": overtime_rate,
                "overtime_total": overtime_hours * overtime_rate,
                "double_time_hours": double_time_hours,
                "double_time_rate": double_time_rate,
                "double_time_total": double_time_hours * double_time_rate,
                "entry_total": entry_total,
            }
        )

    grand_total = sum(e["entry_total"] for e in entries_data)

    return {
        "timesheet_id": str(timesheet.timesheet_id),
        "week_ending": (
            timesheet.week_ending.isoformat() if timesheet.week_ending else None
        ),
        "client_name": (timesheet.client.client_name if timesheet.client else "—"),
        "entries": entries_data,
        "totals": {
            "regular_hours": total_regular,
            "overtime_hours": total_overtime,
            "double_time_hours": total_double_time,
            "total_hours": (total_regular + total_overtime + total_double_time),
            "grand_total": grand_total,
        },
    }
