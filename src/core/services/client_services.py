from fastapi import HTTPException

from src.data.repositories.client_repository import get_all_clients


async def get_clients_service(db):
    try:
        result = await get_all_clients(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_client_service(db):
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
