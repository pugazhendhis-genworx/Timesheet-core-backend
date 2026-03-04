from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ClientCreate(BaseModel):
    client_name: str
    client_code: str
    client_email: EmailStr


class ClientResponse(BaseModel):
    client_id: UUID
    client_name: str
    client_code: str
    client_email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
