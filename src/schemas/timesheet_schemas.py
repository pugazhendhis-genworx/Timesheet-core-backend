from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class TimesheetResponse(BaseModel):
    timesheet_id: UUID
    email_message_id: UUID
    client_id: UUID
    week_ending: date | None
    status: str
    source: str | None
    extraction_status: str | None
    extraction_confidence: Decimal | None
    raw_extraction: dict[str, Any] | None
    updated_at: datetime | None

    class Config:
        from_attributes = True


class TimeEntryRawResponse(BaseModel):
    timeentry_id: UUID
    timesheet_id: UUID
    employee_id: UUID | None
    client_id: UUID
    start_time: datetime | None
    end_time: datetime | None
    regular_hours: Decimal
    overtime_hours: Decimal
    double_time_hours: Decimal
    paycode_id: UUID | None

    class Config:
        from_attributes = True
