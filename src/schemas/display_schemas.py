"""
Production-ready display schemas for TimeGuard frontend
These schemas include denormalized data (names, not just IDs) for UI display
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


# ── Extracted Data (with denormalized names) ────────────────────────────
class TimeEntryDisplayResponse(BaseModel):
    """Time entry with employee and paycode names, plus matching outcome."""

    timeentry_id: UUID
    employee_id: UUID | None = None
    employee_name: str | None = None  # "John Doe" instead of UUID
    client_id: UUID
    client_name: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    regular_hours: Decimal
    overtime_hours: Decimal
    double_time_hours: Decimal
    paycode_id: UUID | None = None
    paycode_code: str | None = None  # "REG", "OT" instead of UUID
    # --- Matching outcome fields ---
    matching_status: str = "MATCHED"
    employee_unmatched_reason: str | None = None
    client_unmatched_reason: str | None = None
    match_confidence: Decimal | None = None


class ExtractedTimesheetDisplayResponse(BaseModel):
    """Extracted timesheet with full context for review"""

    timesheet_id: UUID
    email_message_id: UUID
    sender_email: str  # from email
    received_at: datetime  # from email
    client_id: UUID
    client_name: str
    week_ending: datetime | None = None
    status: str
    extraction_status: str | None = None  # CLASSIFYING, EXTRACTING, COMPLETED, FAILED
    extraction_confidence: Decimal | None = None
    raw_extraction: dict[str, Any] | None = None
    entries: list[TimeEntryDisplayResponse]
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# ── Payroll Ready Format (for auditor/export) ───────────────────────────
class PayrollReadyEntryResponse(BaseModel):
    """Payroll-ready time entry (standardized format for export/payroll)"""

    employee_id: UUID
    employee_name: str
    employee_email: str
    client_name: str
    week_ending: datetime
    paycode: str
    hours: Decimal
    rate: Decimal
    total: Decimal  # hours * rate


class PayrollReadyTimesheetResponse(BaseModel):
    """Payroll-ready timesheet (grouped by week/client/employee)"""

    timesheet_id: UUID
    email_message_id: UUID
    sender_email: str
    received_at: datetime
    client_name: str
    week_ending: datetime
    total_hours: Decimal
    total_cost: Decimal
    entries: list[PayrollReadyEntryResponse]
    status: str  # APPROVED, REJECTED, READY_FOR_APPROVAL
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Email Status with Extraction Trace ──────────────────────────────────
class ExtractionTraceEvent(BaseModel):
    """Single event in extraction workflow trace"""

    timestamp: datetime
    # INGESTED, CLASSIFYING, CLASSIFIED, EXTRACTING, EXTRACTED, MATCHED
    stage: str  # Workflow stage
    status: str  # IN_PROGRESS, SUCCESS, FAILED
    message: str | None = None
    details: dict[str, Any] | None = None


class EmailWithExtractionTraceResponse(BaseModel):
    """Email with full extraction status trace"""

    email_message_id: UUID
    thread_id: UUID
    message_id: str
    sender_email: str
    subject: str | None = None
    received_at: datetime
    # INGESTED, CLASSIFYING, CLASSIFIED, EXTRACTING, COMPLETED, FAILED
    processed_status: str
    classification: str | None = None  # TIMESHEET, OTHER
    last_error: str | None = None
    retry_count: int
    file_count: int  # number of attachments
    trace: list[ExtractionTraceEvent]  # workflow history

    class Config:
        from_attributes = True


# ── Review & Approval ───────────────────────────────────────────────────
class ManualReviewDisplayResponse(BaseModel):
    """Manual review with full context"""

    review_id: UUID
    timesheet_id: UUID
    email_message_id: UUID
    sender_email: str
    received_at: datetime
    client_name: str
    status: str  # PENDING, APPROVED, REJECTED
    created_at: datetime
    updated_at: datetime
    comment: str | None = None
    entries: list[TimeEntryDisplayResponse]

    class Config:
        from_attributes = True


# ── Approval Decision Request ───────────────────────────────────────────
class ApprovalDecisionRequest(BaseModel):
    """Request to approve or reject a timesheet"""

    decision: str  # APPROVED or REJECTED
    comment: str | None = None
