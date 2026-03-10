from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.review_model import Approval


async def create_approval(db: AsyncSession, approval: Approval):
    db.add(approval)
    await db.flush()
    return approval


async def get_approval_by_id(db: AsyncSession, approval_id: UUID):
    result = await db.execute(
        select(Approval).where(Approval.approval_id == approval_id)
    )
    return result.scalar_one_or_none()


async def get_all_approvals(db: AsyncSession):
    result = await db.execute(select(Approval))
    return result.scalars().all()


async def get_approvals_by_timesheet_id(db: AsyncSession, timesheet_id: UUID):
    result = await db.execute(
        select(Approval).where(Approval.timesheet_id == timesheet_id)
    )
    return result.scalars().all()
