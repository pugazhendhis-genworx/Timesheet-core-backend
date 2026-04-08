from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class TimesheetUpdate(BaseModel):
    client_id: UUID | None = None
    week_ending: date | None = None
    status: str | None = None
    raw_extraction: dict[str, Any] | None = None
