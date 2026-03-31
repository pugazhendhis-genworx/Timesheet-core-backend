import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func

from src.data.clients.database import Base


class PayrollExport(Base):
    __tablename__ = "payroll_exports"

    export_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_ending = Column(Date)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))
    exported_by = Column(UUID(as_uuid=True), nullable=True)
    file_path = Column(Text)
    exported_at = Column(DateTime(timezone=True), server_default=func.now())

    client = relationship("Client")


class PayrollReadyEntry(Base):
    __tablename__ = "payroll_ready_entries"

    payroll_entry_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    export_id = Column(UUID(as_uuid=True), ForeignKey("payroll_exports.export_id"))
    timesheet_id = Column(UUID(as_uuid=True), ForeignKey("timesheets.timesheet_id"))
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.employee_id"))
    week_ending = Column(Date)
    regular_hours = Column(Numeric)
    overtime_hours = Column(Numeric)
    double_time_hours = Column(Numeric)
    regular_rate = Column(Numeric)
    overtime_rate = Column(Numeric)
    double_time_rate = Column(Numeric)
    reg_pay = Column(Numeric)
    ot_pay = Column(Numeric)
    holiday_pay = Column(Numeric)
    approval_status = Column(Boolean, default=False)

    export = relationship("PayrollExport")
    client = relationship("Client")
    employee = relationship("Employee")
    timesheet = relationship("Timesheet")
