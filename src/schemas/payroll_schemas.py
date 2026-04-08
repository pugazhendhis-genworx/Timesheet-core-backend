from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from src.schemas.rule_violation_schemas import RuleViolationItemResponse


class PayrollReadyEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payroll_entry_id: UUID
    export_id: UUID | None = None
    timesheet_id: UUID
    client_id: UUID
    employee_id: UUID | None = None
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
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return float(value)


class PayrollReadyListEnvelope(BaseModel):
    data: list[PayrollReadyEntryResponse]


class PayrollReadySingleEnvelope(BaseModel):
    data: PayrollReadyEntryResponse


class PayrollTimesheetSummaryResponse(BaseModel):
    timesheet_id: UUID
    payroll_entries: list[PayrollReadyEntryResponse] = Field(default_factory=list)
    violations: list[RuleViolationItemResponse] = Field(default_factory=list)
