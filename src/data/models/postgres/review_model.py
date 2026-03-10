import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

from src.data.clients.database import Base


class ManualReview(Base):
    __tablename__ = "manual_reviews"

    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timesheet_id = Column(UUID(as_uuid=True), ForeignKey("timesheets.timesheet_id"))
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    comments = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING")
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    timesheet = relationship("Timesheet")


class Approval(Base):
    __tablename__ = "approvals"

    approval_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timesheet_id = Column(UUID(as_uuid=True), ForeignKey("timesheets.timesheet_id"))
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    decision = Column(String(50))
    decision_at = Column(DateTime(timezone=True), nullable=True)

    timesheet = relationship("Timesheet")
