import logging
from datetime import date
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.holiday_model import Holiday
from src.data.repositories.holiday_repository import (
    create_holiday_repo,
    delete_holiday_repo,
    get_holidays_by_client_repo,
    get_holidays_by_dates_and_client_repo,
    update_holiday_repo,
)
from src.schemas.holiday_schemas import HolidayCreate, HolidayUpdate

logger = logging.getLogger(__name__)


async def add_holiday(db: AsyncSession, holiday_data: HolidayCreate) -> Holiday:
    return await create_holiday_repo(db, holiday_data)


async def get_holidays_by_client(
    db: AsyncSession, client_id: UUID
) -> Sequence[Holiday]:
    return await get_holidays_by_client_repo(db, client_id)


async def get_client_holidays_map(
    db: AsyncSession, dates: list[date], client_id: UUID
) -> dict[date, list[str]]:
    """Returns a combined dictionary mapping date -> [list of holiday names]
    for a specific client."""
    db_holidays = await get_holidays_by_dates_and_client_repo(db, client_id, dates)

    holiday_map: dict[date, list[str]] = {}
    for h in db_holidays:
        if h.holiday_date not in holiday_map:
            holiday_map[h.holiday_date] = []
        holiday_map[h.holiday_date].append(h.name)

    return holiday_map


async def update_holiday_service(
    db: AsyncSession, holiday_id: UUID, update_data: HolidayUpdate
) -> Holiday | None:
    return await update_holiday_repo(db, holiday_id, update_data)


async def delete_holiday_service(db: AsyncSession, holiday_id: UUID) -> bool:
    return await delete_holiday_repo(db, holiday_id)
