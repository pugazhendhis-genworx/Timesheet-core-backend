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
from src.observability.logging.logging import get_logger
from src.schemas.manual_review_schemas import ManualReviewSubmit

logger = get_logger(__name__)


async def get_all_reviews_service(db: AsyncSession):
    logger.info("Fetching all manual reviews")

    try:
        reviews = await get_all_reviews(db)
        logger.info(f"Fetched {len(reviews)} reviews")
        return reviews

    except Exception as e:
        logger.error("Error fetching all reviews", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_pending_reviews_service(db: AsyncSession):
    logger.info("Fetching pending reviews")

    try:
        reviews = await get_pending_reviews(db)
        logger.info(f"Fetched {len(reviews)} pending reviews")
        return reviews

    except Exception as e:
        logger.error("Error fetching pending reviews", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_review_by_id_service(db: AsyncSession, review_id: UUID):
    logger.info(f"Fetching review id={review_id}")

    try:
        review = await get_review_by_id(db, review_id)

        if not review:
            logger.warning(f"Review not found: id={review_id}")
            raise HTTPException(status_code=404, detail="Review not found")

        logger.info(f"Review found: id={review_id}")
        return review

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review id={review_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def submit_review_service(
    db: AsyncSession,
    review_id: UUID,
    review_data: ManualReviewSubmit,
):
    """
    Submit a manual review decision (APPROVED / REJECTED).
    Updates the review record and the associated timesheet status.
    """
    logger.info(f"Submitting review id={review_id}")

    try:
        review = await get_review_by_id(db, review_id)

        if not review:
            logger.warning(f"Review not found: id={review_id}")
            raise HTTPException(status_code=404, detail="Review not found")

        if review.status != "PENDING":
            logger.warning(
                f"Review already resolved: id={review_id}, status={review.status}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"Review already resolved with status: {review.status}",
            )

        if review_data.status not in ("APPROVED", "REJECTED"):
            logger.warning(
                f"Invalid review status: id={review_id}, status={review_data.status}"
            )
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

        logger.info(
            f"Review updated: id={review_id}, status={review_data.status}, "
            f"reviewed_by={review_data.reviewed_by}"
        )

        # Update timesheet status
        timesheet = await get_timesheet_by_id(db, review.timesheet_id)

        if timesheet:
            if review_data.status == "APPROVED":
                timesheet.status = "READY_FOR_APPROVAL"
            else:
                timesheet.status = "REJECTED"

            await db.flush()

            logger.info(
                f"""Timesheet updated: id={review.timesheet_id},
                status={timesheet.status}"""
            )
        else:
            logger.warning(
                f"Timesheet not found for review: review_id={review_id}, "
                f"timesheet_id={review.timesheet_id}"
            )

        await db.commit()

        logger.info(
            f"Review submission completed: id={review_id}, status={review_data.status}"
        )

        return review

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting review id={review_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
