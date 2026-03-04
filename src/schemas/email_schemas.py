from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class EmailWhitelistCreate(BaseModel):
    client_id: UUID
    allowed_email: EmailStr


class EmailWhitelistResponse(BaseModel):
    email_whitelist_id: UUID
    client_id: UUID
    allowed_email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
