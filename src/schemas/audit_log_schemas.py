from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    audit_log_id: UUID
    user_id: UUID | None
    entity_type: str
    entity_id: UUID
    action: str
    metadata_json: dict | None
    created_at: datetime

    class Config:
        from_attributes = True

