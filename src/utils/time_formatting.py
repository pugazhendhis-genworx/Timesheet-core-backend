from datetime import date, datetime

_TIME_FORMATS = ("%I:%M %p", "%H:%M", "%I:%M%p", "%H:%M:%S", "%I %p")


def _parse_time(time_str: str) -> datetime | None:
    """Parse time strings like '8:00 AM', '07:30 AM', '17:00'."""
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(time_str.strip(), fmt)
        except (ValueError, TypeError):
            continue
    return None


def _build_datetime(actual_date: date | None, time_str: str | None) -> datetime | None:
    """Combine a resolved date with a time string into a timezone-naive datetime."""
    if not actual_date or not time_str or not time_str.strip():
        return None
    parsed = _parse_time(time_str.strip())
    if parsed is None:
        return None
    return datetime.combine(actual_date, parsed.time())
