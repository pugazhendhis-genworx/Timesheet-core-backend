from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_pg_session
from src.core.services.client_services import create_client_service, get_clients_service

client_router = APIRouter(tags=["client"])


@client_router.get("/get-clients")
async def get_clients(db=Depends(get_pg_session)):
    result = await get_clients_service(db)
    return result


@client_router.post("/add-clients")
async def add_clients(db=Depends(get_pg_session)):
    result = await create_client_service(db)
    return result
