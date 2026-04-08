from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_serializer


class PayrollEmployeePayslipResponse(BaseModel):
    payroll_entry_id: UUID
    timesheet_id: UUID
    client_id: UUID
    employee_id: UUID | None = None
    employee_name: str | None = None
    week_ending: date | None = None
    regular_hours: Decimal
    overtime_hours: Decimal
    double_time_hours: Decimal
    regular_rate: Decimal
    overtime_rate: Decimal
    double_time_rate: Decimal
    reg_pay: Decimal
    ot_pay: Decimal
    holiday_pay: Decimal
    regular_amount: Decimal
    holiday_amount: Decimal
    overtime_amount: Decimal
    double_time_amount: Decimal
    total_pay: Decimal

    @field_serializer(
        "regular_hours",
        "overtime_hours",
        "double_time_hours",
        "regular_rate",
        "overtime_rate",
        "double_time_rate",
        "reg_pay",
        "ot_pay",
        "holiday_pay",
        "regular_amount",
        "holiday_amount",
        "overtime_amount",
        "double_time_amount",
        "total_pay",
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)


class PayrollTimesheetPayslipResponse(BaseModel):
    timesheet_id: UUID
    client_id: UUID | None = None
    client_name: str | None = None
    week_ending: date | None = None
    total_regular_hours: Decimal
    total_overtime_hours: Decimal
    total_double_time_hours: Decimal
    total_pay: Decimal
    payroll_slips: list[PayrollEmployeePayslipResponse]

    @field_serializer(
        "total_regular_hours",
        "total_overtime_hours",
        "total_double_time_hours",
        "total_pay",
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)
