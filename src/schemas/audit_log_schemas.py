from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    audit_log_id: UUID
    user_id: UUID | None = None
    entity_type: str
    entity_id: UUID
    action: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True
