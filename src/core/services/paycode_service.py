from fastapi import HTTPException

from src.data.repositories.paycode_repository import (
    create_paycode,
    get_all_paycodes,
)
from src.observability.logging.logging import get_logger
from src.schemas.paycode_schemas import PaycodeCreate

logger = get_logger(__name__)


async def get_all_paycodes_service(db):
    logger.info("Fetching all paycodes")

    try:
        paycodes = await get_all_paycodes(db)

        logger.info(f"Fetched {len(paycodes)} paycodes")
        return paycodes

    except Exception as e:
        logger.error("Error fetching paycodes", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_paycode_service(db, paycode_data: PaycodeCreate):
    logger.info("Creating new paycode")

    try:
        paycode = await create_paycode(db, paycode_data)

        logger.info(f"Paycode created with id={paycode.paycode_id}")
        return paycode

    except Exception as e:
        logger.error("Error creating paycode", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
