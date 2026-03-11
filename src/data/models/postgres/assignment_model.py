import uuid

from sqlalchemy import UUID, Boolean, Column, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from src.data.clients.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.employee_id"))
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.client_id"))
    start_date = Column(Date)
    end_date = Column(Date)
    regular_rate = Column(Numeric)
    overtime_rate = Column(Numeric)
    double_time_rate = Column(Numeric)
    paycode_id = Column(
        UUID(as_uuid=True), ForeignKey("paycodes.paycode_id"), nullable=True
    )
    is_active = Column(Boolean, default=True)

    employee = relationship("Employee", back_populates="assignments")
    client = relationship("Client")
