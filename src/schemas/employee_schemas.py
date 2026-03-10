from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class EmployeeCreate(BaseModel):
    emp_email: EmailStr
    first_name: str
    last_name: str
    dob: date
    designation: str


class EmployeeUpdate(BaseModel):
    emp_email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    designation: str | None = None
    is_active: bool | None = None


class EmployeeResponse(BaseModel):
    employee_id: UUID
    emp_email: str
    first_name: str
    last_name: str
    dob: date
    designation: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
