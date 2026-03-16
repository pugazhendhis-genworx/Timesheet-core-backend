from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.rest.dependencies import DBSession, require_roles
from src.core.services.manual_review_service import (
    get_all_reviews_service,
    get_pending_reviews_service,
    get_review_by_id_service,
    submit_review_service,
)
from src.schemas.manual_review_schemas import ManualReviewResponse, ManualReviewSubmit

review_router = APIRouter(
    tags=["manual-review"],
    prefix="/manual-review",
    dependencies=[Depends(require_roles(["operation_executive", "auditor"]))],
)


@review_router.get("/get-reviews", response_model=list[ManualReviewResponse])
async def get_reviews(db: DBSession):
    return await get_all_reviews_service(db)


@review_router.get("/pending", response_model=list[ManualReviewResponse])
async def get_pending_reviews(db: DBSession):
    return await get_pending_reviews_service(db)


@review_router.get("/{review_id}", response_model=ManualReviewResponse)
async def get_review(review_id: UUID, db: DBSession):
    return await get_review_by_id_service(db, review_id)


@review_router.put("/{review_id}", response_model=ManualReviewResponse)
async def submit_review(
    review_id: UUID, review_data: ManualReviewSubmit, db: DBSession
):
    return await submit_review_service(db, review_id, review_data)
