import uuid
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.data.clients.database import Base


class EmailClassification(StrEnum):
    TIMESHEET = "TIMESHEET"
    OTHER = "OTHER"


class ProcessedStatus(StrEnum):
    INGESTED = "INGESTED"
    CLASSIFYING = "CLASSIFYING"
    CLASSIFIED = "CLASSIFIED"
    IGNORED = "IGNORED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


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
    processed_status: Mapped[ProcessedStatus] = mapped_column(
        Enum(ProcessedStatus, name="processed_status_enum", native_enum=False),
        default=ProcessedStatus.INGESTED,
    )
    classification: Mapped[EmailClassification] = mapped_column(
        Enum(EmailClassification, name="email_classification_enum", native_enum=False),
        nullable=True,
    )
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

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
    processing_status: Mapped[ProcessedStatus | None] = mapped_column(
        Enum(ProcessedStatus, name="processed_status_enum", native_enum=False),
        nullable=True,
    )
    extracted_text = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)

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
