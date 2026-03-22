from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class TimesheetResponse(BaseModel):
    timesheet_id: UUID
    email_message_id: UUID
    client_id: UUID
    week_ending: date | None = None
    status: str
    source: str | None = None
    extraction_status: str | None = None
    extraction_confidence: Decimal | None = None
    raw_extraction: dict[str, Any] | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TimeEntryRawResponse(BaseModel):
    timeentry_id: UUID
    timesheet_id: UUID
    employee_id: UUID | None = None
    client_id: UUID
    start_time: datetime | None = None
    end_time: datetime | None = None
    regular_hours: Decimal
    overtime_hours: Decimal
    double_time_hours: Decimal
    paycode_id: UUID | None = None
    matching_status: str | None = None
    employee_unmatched_reason: str | None = None
    client_unmatched_reason: str | None = None
    match_confidence: Decimal | None = None

    class Config:
        from_attributes = True
