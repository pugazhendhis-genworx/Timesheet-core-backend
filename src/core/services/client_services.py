from uuid import UUID

from fastapi import HTTPException

from src.data.repositories.client_repository import (
    create_client,
    get_all_clients,
    get_client_by_id,
)
from src.schemas.client_schemas import ClientCreate


async def get_clients_service(db):
    try:
        result = await get_all_clients(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_client_by_id_service(db, client_id: UUID):
    client = await get_client_by_id(db, client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return client


async def create_client_service(db, client_data: ClientCreate):
    try:
        result = await create_client(db, client_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
