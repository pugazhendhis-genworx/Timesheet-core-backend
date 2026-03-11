from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.review_model import ManualReview


async def create_manual_review(db: AsyncSession, review: ManualReview):
    db.add(review)
    await db.flush()
    return review


async def get_review_by_id(db: AsyncSession, review_id: UUID):
    result = await db.execute(
        select(ManualReview).where(ManualReview.review_id == review_id)
    )
    return result.scalar_one_or_none()


async def get_all_reviews(db: AsyncSession):
    result = await db.execute(select(ManualReview))
    return result.scalars().all()


async def get_pending_reviews(db: AsyncSession):
    result = await db.execute(
        select(ManualReview).where(ManualReview.status == "PENDING")
    )
    return result.scalars().all()


async def get_reviews_by_timesheet_id(db: AsyncSession, timesheet_id: UUID):
    result = await db.execute(
        select(ManualReview).where(ManualReview.timesheet_id == timesheet_id)
    )
    return result.scalars().all()
