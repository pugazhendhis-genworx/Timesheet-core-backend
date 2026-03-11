from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.timesheet_model import Timesheet


async def create_timesheet(db: AsyncSession, timesheet: Timesheet):
    db.add(timesheet)
    await db.flush()
    return timesheet


async def get_timesheet_by_id(db: AsyncSession, timesheet_id: UUID):
    result = await db.execute(
        select(Timesheet).where(Timesheet.timesheet_id == timesheet_id)
    )
    return result.scalar_one_or_none()


async def get_all_timesheets(db: AsyncSession):
    result = await db.execute(select(Timesheet))
    return result.scalars().all()


async def get_timesheets_by_client_id(db: AsyncSession, client_id: UUID):
    result = await db.execute(select(Timesheet).where(Timesheet.client_id == client_id))
    return result.scalars().all()


async def get_timesheets_by_status(db: AsyncSession, status: str):
    result = await db.execute(select(Timesheet).where(Timesheet.status == status))
    return result.scalars().all()


async def update_timesheet_status(db: AsyncSession, timesheet_id: UUID, status: str):
    timesheet = await get_timesheet_by_id(db, timesheet_id)
    if not timesheet:
        return None
    timesheet.status = status
    await db.flush()
    return timesheet
