from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.payroll_model import PayrollReadyEntry


async def create_payroll_ready_entries_repo(
    db: AsyncSession, entries: list[PayrollReadyEntry]
) -> list[PayrollReadyEntry]:
    db.add_all(entries)
    await db.commit()
    return entries


async def get_payroll_ready_entries_by_timesheet_repo(
    db: AsyncSession, timesheet_id: UUID
) -> Sequence[PayrollReadyEntry]:
    stmt = select(PayrollReadyEntry).where(
        PayrollReadyEntry.timesheet_id == timesheet_id
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_payroll_ready_by_id_repo(
    db: AsyncSession, payroll_entry_id: UUID
) -> PayrollReadyEntry | None:
    stmt = select(PayrollReadyEntry).where(
        PayrollReadyEntry.payroll_entry_id == payroll_entry_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_payroll_ready_repo(db: AsyncSession) -> Sequence[PayrollReadyEntry]:
    stmt = select(PayrollReadyEntry)
    result = await db.execute(stmt)
    return result.scalars().all()
