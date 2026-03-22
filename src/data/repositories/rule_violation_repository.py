from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.client_rule_model import RuleViolation


async def get_rule_violations_by_timesheet_id_repo(
    db: AsyncSession, timesheet_id: UUID
) -> Sequence[RuleViolation]:
    stmt = select(RuleViolation).where(RuleViolation.timesheet_id == timesheet_id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_timesheets_with_violations_repo(db: AsyncSession) -> Sequence[UUID]:
    stmt = select(RuleViolation.timesheet_id).distinct()
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_flagged_timesheets_summary_repo(db: AsyncSession):
    from sqlalchemy.orm import joinedload
    from src.data.models.postgres.timesheet_model import Timesheet

    subq = select(RuleViolation.timesheet_id).distinct().subquery()
    
    stmt = (
        select(Timesheet)
        .options(joinedload(Timesheet.email_message))
        .join(subq, Timesheet.timesheet_id == subq.c.timesheet_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
