from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ManualReviewSubmit(BaseModel):
    status: str  # APPROVED or REJECTED
    reviewed_by: UUID
    comments: str | None = None


class ManualReviewResponse(BaseModel):
    review_id: UUID
    timesheet_id: UUID
    reviewed_by: UUID | None
    comments: str | None
    status: str
    reviewed_at: datetime | None

    class Config:
        from_attributes = True
