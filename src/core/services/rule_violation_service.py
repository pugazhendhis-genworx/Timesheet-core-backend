from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.timesheet_model import TimeEntryRaw, Timesheet
from src.data.repositories.rule_violation_repository import (
    get_flagged_timesheets_summary_with_latest_violation_repo,
    get_rule_violations_by_timesheet_id_repo,
)


async def get_flagged_timesheets_list_service(db: AsyncSession):
    rows = await get_flagged_timesheets_summary_with_latest_violation_repo(db)
    summary_list = []

    for ts, latest_created_at in rows:
        summary_list.append(
            {
                "timesheet_id": ts.timesheet_id,
                "week_ending": ts.week_ending,
                "status": ts.status,
                "email": ts.email_message.sender_email
                if ts.email_message
                else "Unknown",
                "source": ts.source,
                "latest_violation_created_at": latest_created_at,
                "email_received_at": ts.email_message.received_at
                if ts.email_message
                else None,
            }
        )

    return summary_list


async def get_flagged_timesheet_summary_service(db: AsyncSession, timesheet_id: UUID):
    # Fetch violations natively hooked from DB limits
    violations = await get_rule_violations_by_timesheet_id_repo(db, timesheet_id)

    # Fetch parent timesheet metadata
    stmt_ts = select(Timesheet).where(Timesheet.timesheet_id == timesheet_id)
    result_ts = await db.execute(stmt_ts)
    timesheet = result_ts.scalar_one_or_none()

    if not timesheet:
        return None

    # Fetch corresponding raw boundaries prior to engine sync
    stmt_entries = select(TimeEntryRaw).where(TimeEntryRaw.timesheet_id == timesheet_id)
    result_entries = await db.execute(stmt_entries)
    entries = result_entries.scalars().all()

    return {
        "status": "FLAGGED_WITH_VIOLATIONS" if violations else "CLEAN",
        "timesheet": timesheet,
        "time_entries_raw": entries,
        "violations": violations,
    }
