from datetime import date, datetime, timedelta

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%m-%d-%Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
)
_DAY_NAME_INDEX: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _resolve_week_ending(date_str: str) -> date | None:
    """Parse a week_ending string across multiple common formats."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _resolve_entry_date(date_str: str, week_ending: date | None) -> date | None:
    """
    Resolve an entry date string to an actual calendar date.
    Handles day names ('Monday') by anchoring to week_ending,
    and explicit date strings ('2026-03-03') by direct parsing.
    """
    if not date_str:
        return None
    key = date_str.strip().lower()
    if key in _DAY_NAME_INDEX:
        if week_ending is None:
            return None
        # Find Monday of the week that contains week_ending
        monday = week_ending - timedelta(days=week_ending.weekday())
        return monday + timedelta(days=_DAY_NAME_INDEX[key])
    return _resolve_week_ending(date_str)
