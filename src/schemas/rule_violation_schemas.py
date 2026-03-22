from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.timesheet_schemas import TimeEntryRawResponse, TimesheetResponse


class RuleViolationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    violation_id: UUID
    timesheet_id: UUID
    rule_id: UUID | None = None
    violation_type: str
    severity: str
    description: str | None = None
    created_at: datetime | None = None


class FlaggedTimesheetSummaryResponse(BaseModel):
    timesheet_id: UUID
    week_ending: date | None = None
    status: str
    email: str
    source: str | None = None


class FlaggedTimesheetListEnvelope(BaseModel):
    data: list[FlaggedTimesheetSummaryResponse]


class RuleViolationDetailResponse(BaseModel):
    """Timesheet + raw entries + violations for review UI."""

    status: str
    timesheet: TimesheetResponse
    time_entries_raw: list[TimeEntryRawResponse]
    violations: list[RuleViolationItemResponse]
