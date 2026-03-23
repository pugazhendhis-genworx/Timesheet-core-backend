from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.timesheet_model import TimeEntryRaw


async def create_time_entry(db: AsyncSession, entry: TimeEntryRaw):
    db.add(entry)
    await db.flush()
    return entry


async def get_entries_by_timesheet_id(db: AsyncSession, timesheet_id: UUID):
    result = await db.execute(
        select(TimeEntryRaw).where(TimeEntryRaw.timesheet_id == timesheet_id)
    )
    return result.scalars().all()


async def get_entry_by_id(db: AsyncSession, timeentry_id: UUID):
    result = await db.execute(
        select(TimeEntryRaw).where(TimeEntryRaw.timeentry_id == timeentry_id)
    )
    return result.scalar_one_or_none()


async def update_entry_employee(
    db: AsyncSession, timeentry_id: UUID, employee_id: UUID
):
    entry = await get_entry_by_id(db, timeentry_id)
    if not entry:
        return None
    entry.employee_id = employee_id
    await db.flush()
    return entry


async def fetch_time_sheet_entry_for_rule_violations():
    pass
