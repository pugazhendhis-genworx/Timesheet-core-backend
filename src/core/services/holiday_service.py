from collections.abc import Sequence
from datetime import date
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
from src.observability.logging.logging import get_logger
from src.schemas.holiday_schemas import HolidayCreate, HolidayUpdate

logger = get_logger(__name__)


async def add_holiday(db: AsyncSession, holiday_data: HolidayCreate) -> Holiday:
    logger.info(f"Creating holiday for client_id={holiday_data.client_id}")

    try:
        holiday = await create_holiday_repo(db, holiday_data)

        logger.info(
            f"Holiday created: id={holiday.id}, "
            f"date={holiday.holiday_date}, client_id={holiday.client_id}"
        )
        return holiday

    except Exception:
        logger.error("Error creating holiday", exc_info=True)
        raise


async def get_holidays_by_client(
    db: AsyncSession, client_id: UUID
) -> Sequence[Holiday]:
    logger.info(f"Fetching holidays for client_id={client_id}")

    try:
        holidays = await get_holidays_by_client_repo(db, client_id)

        logger.info(f"Fetched {len(holidays)} holidays for client_id={client_id}")
        return holidays

    except Exception:
        logger.error(
            f"Error fetching holidays for client_id={client_id}",
            exc_info=True,
        )
        raise


async def get_client_holidays_map(
    db: AsyncSession, dates: list[date], client_id: UUID
) -> dict[date, list[str]]:
    """Returns a combined dictionary mapping date -> [list of holiday names]
    for a specific client."""
    logger.info(
        f"Building holiday map for client_id={client_id}, dates_count={len(dates)}"
    )

    try:
        db_holidays = await get_holidays_by_dates_and_client_repo(db, client_id, dates)

        logger.info(
            f"Fetched {len(db_holidays)} holidays for mapping (client_id={client_id})"
        )

        holiday_map: dict[date, list[str]] = {}

        for h in db_holidays:
            if h.holiday_date not in holiday_map:
                holiday_map[h.holiday_date] = []

            holiday_map[h.holiday_date].append(h.name)

        logger.debug(
            f"Holiday map built for client_id={client_id}: {len(holiday_map)} dates"
        )

        return holiday_map

    except Exception:
        logger.error(
            f"Error building holiday map for client_id={client_id}",
            exc_info=True,
        )
        raise


async def update_holiday_service(
    db: AsyncSession, holiday_id: UUID, update_data: HolidayUpdate
) -> Holiday | None:
    logger.info(f"Updating holiday id={holiday_id}")

    try:
        holiday = await update_holiday_repo(db, holiday_id, update_data)

        if not holiday:
            logger.warning(f"Holiday not found for update: id={holiday_id}")
            return None

        logger.info(f"Holiday updated: id={holiday_id}")
        return holiday

    except Exception:
        logger.error(f"Error updating holiday id={holiday_id}", exc_info=True)
        raise


async def delete_holiday_service(db: AsyncSession, holiday_id: UUID) -> bool:
    logger.info(f"Deleting holiday id={holiday_id}")

    try:
        deleted = await delete_holiday_repo(db, holiday_id)

        if not deleted:
            logger.warning(f"Holiday not found for deletion: id={holiday_id}")
            return False

        logger.info(f"Holiday deleted: id={holiday_id}")
        return True

    except Exception:
        logger.error(f"Error deleting holiday id={holiday_id}", exc_info=True)
        raise
