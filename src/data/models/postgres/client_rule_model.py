import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func

from src.data.clients.database import Base


class ClientRule(Base):
    __tablename__ = "client_rules"

    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))
    rule_type = Column(String(50))
    rule_config = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


class RuleViolation(Base):
    __tablename__ = "rule_violations"

    violation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timesheet_id = Column(UUID(as_uuid=True), ForeignKey("timesheets.timesheet_id"))
    rule_id = Column(
        UUID(as_uuid=True), ForeignKey("client_rules.rule_id"), nullable=True
    )
    severity = Column(String(20))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    timesheet = relationship("Timesheet")
    rule = relationship("ClientRule")
