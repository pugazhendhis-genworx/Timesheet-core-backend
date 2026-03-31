from uuid import UUID

from fastapi import HTTPException

from src.data.repositories.client_repository import (
    create_client,
    get_all_clients,
    get_client_by_id,
)
from src.observability.logging.logging import get_logger
from src.schemas.client_schemas import ClientCreate

logger = get_logger(__name__)


async def get_clients_service(db):
    try:
        result = await get_all_clients(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_client_by_id_service(db, client_id: UUID):
    try:
        client = await get_client_by_id(db, client_id)

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return client
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_client_service(db, client_data: ClientCreate):
    logger.info("Creating new client")
    try:
        result = await create_client(db, client_data)

        logger.info(f"Client created with id={result.client_id}")
        return result

    except Exception as e:
        logger.error("Error creating client", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
