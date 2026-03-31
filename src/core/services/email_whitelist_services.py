from uuid import UUID

from fastapi import HTTPException

from src.data.repositories.email_whitelist_repository import (
    create_whitelist_email,
    get_all_whitelisted_emails,
    get_whitelisted_email_by_client_id,
)
from src.observability.logging.logging import get_logger
from src.schemas.email_schemas import EmailWhitelistCreate

logger = get_logger(__name__)


async def get_all_whitelist_service(db):
    logger.info("Fetching all whitelisted emails")

    try:
        result = await get_all_whitelisted_emails(db)

        logger.info(f"Fetched {len(result)} whitelist entries")
        return result

    except Exception as e:
        logger.error("Error fetching whitelist entries", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_whitelist_by_clientid_service(client_id: UUID, db):
    logger.info(f"Fetching whitelist entry for client_id={client_id}")

    try:
        entry = await get_whitelisted_email_by_client_id(client_id, db)

        if not entry:
            logger.warning(f"Whitelist entry not found for client_id={client_id}")
            raise HTTPException(status_code=404, detail="Whitelist entry not found")

        logger.info(f"Whitelist entry found for client_id={client_id}")
        return entry

    except Exception as e:
        logger.error(
            f"Error fetching whitelist entry for client_id={client_id}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_whitelist_service(whitelist_data: EmailWhitelistCreate, db):
    logger.info("Creating whitelist entry")

    try:
        result = await create_whitelist_email(whitelist_data, db)

        logger.info(
            f"""Whitelist entry created for
            client_id={result.client_id}, email={result.email}"""
        )
        return result

    except Exception as e:
        logger.error("Error creating whitelist entry", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
