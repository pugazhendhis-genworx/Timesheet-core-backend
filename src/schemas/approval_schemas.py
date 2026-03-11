from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ApprovalCreate(BaseModel):
    approved_by: UUID
    decision: str  # APPROVED or REJECTED


class ApprovalResponse(BaseModel):
    approval_id: UUID
    timesheet_id: UUID
    approved_by: UUID | None
    decision: str
    decision_at: datetime | None

    class Config:
        from_attributes = True
