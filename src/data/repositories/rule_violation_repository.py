from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.data.models.postgres.client_rule_model import RuleViolation
from src.data.models.postgres.timesheet_model import Timesheet


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

    subq = select(RuleViolation.timesheet_id).distinct().subquery()

    stmt = (
        select(Timesheet)
        .options(joinedload(Timesheet.email_message))
        .join(subq, Timesheet.timesheet_id == subq.c.timesheet_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_flagged_timesheets_summary_with_latest_violation_repo(
    db: AsyncSession,
):
    """
    Returns rows of (Timesheet, latest_violation_created_at) for each
    timesheet that has at least one rule violation.
    """
    latest_subq = (
        select(
            RuleViolation.timesheet_id,
            func.max(RuleViolation.created_at).label(
                "latest_violation_created_at"
            ),
        )
        .group_by(RuleViolation.timesheet_id)
        .subquery()
    )

    stmt = (
        select(Timesheet, latest_subq.c.latest_violation_created_at)
        .options(joinedload(Timesheet.email_message))
        .join(latest_subq, Timesheet.timesheet_id == latest_subq.c.timesheet_id)
    )

    result = await db.execute(stmt)
    return result.all()
