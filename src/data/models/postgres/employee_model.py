import uuid

from sqlalchemy import UUID, Boolean, Column, Date, DateTime, String, func
from sqlalchemy.orm import relationship

from src.data.clients.database import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    emp_email = Column(String(150))
    first_name = Column(String(100))
    last_name = Column(String(100))
    dob = Column(Date)
    designation = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assignments = relationship("Assignment", back_populates="employee")
