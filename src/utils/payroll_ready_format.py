from src.data.models.postgres.timesheet_model import Timesheet


def _build_payroll_ready_timesheet(timesheet: Timesheet) -> dict | None:
    """
    Build payroll-ready timesheet with all entries and totals.
    """
    if not timesheet.entries:
        return None  # Skip timesheets with no entries

    entries_data = []
    total_regular: float = 0.0
    total_overtime: float = 0.0
    total_double_time: float = 0.0

    for entry in timesheet.entries:
        emp = entry.employee
        if not emp:
            continue  # Skip entries without employee

        regular_hours = float(entry.regular_hours or 0)
        overtime_hours = float(entry.overtime_hours or 0)
        double_time_hours = float(entry.double_time_hours or 0)

        total_regular += regular_hours
        total_overtime += overtime_hours
        total_double_time += double_time_hours

        # Use default rates if not specified in entry
        regular_rate = float(entry.regular_rate or 0)
        overtime_rate = float(entry.overtime_rate or 0)
        double_time_rate = float(entry.double_time_rate or 0)

        entry_total = (
            regular_hours * regular_rate
            + overtime_hours * overtime_rate
            + double_time_hours * double_time_rate
        )

        entries_data.append(
            {
                "timeentry_id": str(entry.timeentry_id),
                "employee_name": f"{emp.first_name} {emp.last_name}",
                "employee_email": emp.emp_email,
                "date": (entry.start_time.isoformat() if entry.start_time else None),
                "regular_hours": regular_hours,
                "regular_rate": regular_rate,
                "regular_total": regular_hours * regular_rate,
                "overtime_hours": overtime_hours,
                "overtime_rate": overtime_rate,
                "overtime_total": overtime_hours * overtime_rate,
                "double_time_hours": double_time_hours,
                "double_time_rate": double_time_rate,
                "double_time_total": double_time_hours * double_time_rate,
                "entry_total": entry_total,
            }
        )

    grand_total = sum(e["entry_total"] for e in entries_data)

    return {
        "timesheet_id": str(timesheet.timesheet_id),
        "week_ending": (
            timesheet.week_ending.isoformat() if timesheet.week_ending else None
        ),
        "client_name": (timesheet.client.client_name if timesheet.client else "—"),
        "entries": entries_data,
        "totals": {
            "regular_hours": total_regular,
            "overtime_hours": total_overtime,
            "double_time_hours": total_double_time,
            "total_hours": (total_regular + total_overtime + total_double_time),
            "grand_total": grand_total,
        },
    }
