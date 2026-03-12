from src.data.models.postgres.timesheet_model import Timesheet


def _build_extracted_display(timesheet: Timesheet) -> dict:
    """Build display dict for a single extracted timesheet."""
    email = timesheet.email_message
    client = timesheet.client

    entries_display = []
    for entry in timesheet.entries:
        emp = entry.employee
        pc = entry.paycode
        entries_display.append(
            {
                "timeentry_id": str(entry.timeentry_id),
                "employee_id": str(entry.employee_id) if entry.employee_id else None,
                "employee_name": f"{emp.first_name} {emp.last_name}" if emp else None,
                "client_id": str(entry.client_id),
                "client_name": client.client_name if client else "—",
                "start_time": entry.start_time.isoformat()
                if entry.start_time
                else None,
                "end_time": entry.end_time.isoformat() if entry.end_time else None,
                "regular_hours": float(entry.regular_hours)
                if entry.regular_hours
                else 0,
                "overtime_hours": float(entry.overtime_hours)
                if entry.overtime_hours
                else 0,
                "double_time_hours": float(entry.double_time_hours)
                if entry.double_time_hours
                else 0,
                "paycode_id": str(entry.paycode_id) if entry.paycode_id else None,
                "paycode_code": pc.paycode if pc else None,
                # Matching outcome fields
                "matching_status": entry.matching_status or "MATCHED",
                "employee_unmatched_reason": entry.employee_unmatched_reason,
                "client_unmatched_reason": entry.client_unmatched_reason,
                "match_confidence": float(entry.match_confidence)
                if entry.match_confidence
                else None,
            }
        )

    return {
        "timesheet_id": str(timesheet.timesheet_id),
        "email_message_id": str(timesheet.email_message_id),
        "sender_email": email.sender_email if email else "—",
        "received_at": email.received_at.isoformat() if email else None,
        "client_id": str(timesheet.client_id),
        "client_name": client.client_name if client else "—",
        "week_ending": (
            timesheet.week_ending.isoformat() if timesheet.week_ending else None
        ),
        "status": timesheet.status,
        "extraction_status": timesheet.extraction_status,
        "extraction_confidence": (
            float(timesheet.extraction_confidence)
            if timesheet.extraction_confidence
            else None
        ),
        "entries": entries_display,
        "updated_at": (
            timesheet.updated_at.isoformat() if timesheet.updated_at else None
        ),
    }


def _build_extracted_display_list(timesheets: list[Timesheet]) -> list[dict]:
    """Build display list for multiple extracted timesheets."""
    return [_build_extracted_display(ts) for ts in timesheets]
