from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.rule_violation_repository import (
    get_flagged_timesheets_summary_with_latest_violation_repo,
    get_rule_violations_by_timesheet_id_repo,
)
from src.data.repositories.time_entry_repository import get_entries_by_timesheet_id
from src.data.repositories.timesheet_repository import get_timesheet_by_id


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
    timesheet = get_timesheet_by_id(db, timesheet_id)

    if not timesheet:
        return None

    # Fetch corresponding raw boundaries prior to engine sync
    entries = await get_entries_by_timesheet_id(db, timesheet_id)

    return {
        "status": "FLAGGED_WITH_VIOLATIONS" if violations else "CLEAN",
        "timesheet": timesheet,
        "time_entries_raw": entries,
        "violations": violations,
    }
