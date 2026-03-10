import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.manual_review_repository import (
    get_all_reviews,
    get_pending_reviews,
    get_review_by_id,
)
from src.data.repositories.timesheet_repository import (
    get_timesheet_by_id,
)
from src.schemas.manual_review_schemas import ManualReviewSubmit

logger = logging.getLogger(__name__)


async def get_all_reviews_service(db: AsyncSession):
    return await get_all_reviews(db)


async def get_pending_reviews_service(db: AsyncSession):
    return await get_pending_reviews(db)


async def get_review_by_id_service(db: AsyncSession, review_id: UUID):
    review = await get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


async def submit_review_service(
    db: AsyncSession,
    review_id: UUID,
    review_data: ManualReviewSubmit,
):
    """
    Submit a manual review decision (APPROVED / REJECTED).
    Updates the review record and the associated timesheet status.
    """
    review = await get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Review already resolved with status: {review.status}",
        )

    if review_data.status not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=400,
            detail="Status must be APPROVED or REJECTED",
        )

    # Update review
    review.status = review_data.status
    review.reviewed_by = review_data.reviewed_by
    review.comments = review_data.comments
    review.reviewed_at = datetime.now(UTC)
    await db.flush()

    # Update timesheet status
    timesheet = await get_timesheet_by_id(db, review.timesheet_id)
    if timesheet:
        if review_data.status == "APPROVED":
            timesheet.status = "READY_FOR_APPROVAL"
        else:
            timesheet.status = "REJECTED"
        await db.flush()

    await db.commit()

    logger.info(
        "Review %s submitted: %s for timesheet %s",
        review_id,
        review_data.status,
        review.timesheet_id,
    )
    return review
