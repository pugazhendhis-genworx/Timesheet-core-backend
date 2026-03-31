from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HolidayCreate(BaseModel):
    client_id: UUID
    holiday_date: date
    name: str
    type: str = "Client Holiday"


class HolidayUpdate(BaseModel):
    holiday_date: date | None = None
    name: str | None = None
    type: str | None = None


class HolidayResponse(HolidayCreate):
    id: UUID

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
