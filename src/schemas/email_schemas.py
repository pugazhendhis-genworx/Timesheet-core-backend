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


class EmailAttachmentResponse(BaseModel):
    attachment_id: UUID
    file_name: str
    file_type: str
    file_path: str

    class Config:
        from_attributes = True


class EmailMessageResponse(BaseModel):
    email_message_id: UUID
    thread_id: UUID
    message_id: str
    sender_email: str
    subject: str | None
    body: str | None
    received_at: datetime
    is_reply: bool | None
    processed_status: str | None
    classification: str | None
    attachments: list[EmailAttachmentResponse] = []

    class Config:
        from_attributes = True
