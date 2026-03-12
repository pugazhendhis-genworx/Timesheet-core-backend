from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    employee_id: UUID
    client_id: UUID
    start_date: date
    end_date: date
    regular_rate: Decimal
    overtime_rate: Decimal
    double_time_rate: Decimal
    paycode_id: UUID | None = None


class AssignmentUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    regular_rate: Decimal | None = None
    overtime_rate: Decimal | None = None
    double_time_rate: Decimal | None = None
    paycode_id: UUID | None = None
    is_active: bool | None = None


class AssignmentResponse(BaseModel):
    assignment_id: UUID
    employee_id: UUID
    client_id: UUID
    start_date: date
    end_date: date
    regular_rate: Decimal
    overtime_rate: Decimal
    double_time_rate: Decimal
    paycode_id: UUID | None = None
    is_active: bool

    class Config:
        from_attributes = True
