from collections.abc import Sequence
from datetime import date
from typing import cast
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.holiday_model import Holiday
from src.schemas.holiday_schemas import HolidayCreate, HolidayUpdate


async def create_holiday_repo(db: AsyncSession, holiday_data: HolidayCreate) -> Holiday:
    new_holiday = Holiday(
        client_id=holiday_data.client_id,
        holiday_date=holiday_data.holiday_date,
        name=holiday_data.name,
        type=holiday_data.type,
    )
    db.add(new_holiday)
    await db.commit()
    await db.refresh(new_holiday)
    return new_holiday


async def get_holidays_by_client_repo(
    db: AsyncSession, client_id: UUID
) -> Sequence[Holiday]:
    stmt = (
        select(Holiday)
        .where(Holiday.client_id == client_id)
        .order_by(Holiday.holiday_date)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_holidays_by_dates_and_client_repo(
    db: AsyncSession, client_id: UUID, dates: list[date]
) -> Sequence[Holiday]:
    if not dates:
        return []
    stmt = select(Holiday).where(
        Holiday.client_id == client_id, Holiday.holiday_date.in_(dates)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_holiday_by_id_repo(db: AsyncSession, holiday_id: UUID) -> Holiday | None:
    stmt = select(Holiday).where(Holiday.id == holiday_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_holiday_repo(
    db: AsyncSession, holiday_id: UUID, update_data: HolidayUpdate
) -> Holiday | None:
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        return await get_holiday_by_id_repo(db, holiday_id)

    stmt = (
        update(Holiday)
        .where(Holiday.id == holiday_id)
        .values(**update_dict)
        .returning(Holiday)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one_or_none()


async def delete_holiday_repo(db: AsyncSession, holiday_id: UUID) -> bool:
    stmt = delete(Holiday).where(Holiday.id == holiday_id)
    result = await db.execute(stmt)
    await db.commit()
    cursor_result = cast(CursorResult, result)
    return cursor_result.rowcount > 0
