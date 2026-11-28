import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional, Tuple


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_reference(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def risk_level_for(score: float, threshold: float) -> str:
    """Presentation categories only. The decision threshold is applied separately."""
    if score >= threshold:
        return "High"
    if score >= 0.30:
        return "Elevated"
    if score >= 0.10:
        return "Moderate"
    return "Low"


def date_bounds(
    date_from: Optional[date], date_to: Optional[date]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Inclusive date range -> [start, end) UTC datetimes."""
    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
    end = (
        datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
        if date_to
        else None
    )
    return start, end
