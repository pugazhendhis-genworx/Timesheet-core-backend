import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.data.clients.database import Base


class EmailThread(Base):
    __tablename__ = "email_threads"

    thread_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gmail_thread_id = Column(String(255), unique=True)
    subject = Column(Text)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))

    messages = relationship("EmailMessage", back_populates="thread")


class EmailMessage(Base):
    __tablename__ = "email_messages"

    email_message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("email_threads.thread_id"))
    message_id = Column(String(255), unique=True)
    sender_email = Column(String(150))
    subject = Column(Text)
    body = Column(Text)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    is_reply = Column(Boolean)
    processed_status = Column(String)

    thread = relationship("EmailThread", back_populates="messages")
    attachments = relationship("EmailAttachment", back_populates="email_message")


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    attachment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_message_id = Column(
        UUID(as_uuid=True), ForeignKey("email_messages.email_message_id")
    )
    file_name = Column(String(255))
    file_type = Column(String(100))
    file_path = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    email_message = relationship("EmailMessage", back_populates="attachments")


class EmailWhitelist(Base):
    __tablename__ = "email_whitelist"

    email_whitelist_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))
    allowed_email = Column(String(150))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client", back_populates="whitelist")
