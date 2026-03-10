import uuid

from sqlalchemy import Column, Date, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func

from src.data.clients.database import Base


class Timesheet(Base):
    __tablename__ = "timesheets"

    timesheet_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_message_id = Column(
        UUID(as_uuid=True), ForeignKey("email_messages.email_message_id")
    )
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))
    week_ending = Column(Date)
    status = Column(String(50), default="RECEIVED")
    source = Column(String(100), nullable=True)
    extraction_status = Column(String(50), nullable=True)
    extraction_confidence = Column(Numeric, nullable=True)
    raw_extraction = Column(JSONB, nullable=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    entries = relationship("TimeEntryRaw", back_populates="timesheet")
    email_message = relationship("EmailMessage")
    client = relationship("Client")


class TimeEntryRaw(Base):
    __tablename__ = "time_entries_raw"

    timeentry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timesheet_id = Column(UUID(as_uuid=True), ForeignKey("timesheets.timesheet_id"))
    employee_id = Column(
        UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=True
    )
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    regular_hours = Column(Numeric, default=0)
    overtime_hours = Column(Numeric, default=0)
    double_time_hours = Column(Numeric, default=0)
    paycode_id = Column(
        UUID(as_uuid=True), ForeignKey("paycodes.paycode_id"), nullable=True
    )
    # --- Per-entry matching outcome tracking ---
    matching_status = Column(
        String(50),
        default="MATCHED",
        nullable=False,
    )
    # Values: MATCHED, EMPLOYEE_UNMATCHED, CLIENT_UNMATCHED, ASSIGNMENT_VIOLATION
    employee_unmatched_reason = Column(String(500), nullable=True)
    client_unmatched_reason = Column(String(500), nullable=True)
    match_confidence = Column(Numeric, nullable=True)

    timesheet = relationship("Timesheet", back_populates="entries")
    employee = relationship("Employee")
    client = relationship("Client")
    paycode = relationship("Paycode")
