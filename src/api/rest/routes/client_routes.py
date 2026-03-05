from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_pg_session
from src.core.services.client_services import create_client_service, get_clients_service
from src.schemas.client_schemas import ClientCreate, ClientResponse

client_router = APIRouter(tags=["client"],prefix="/client")


@client_router.get("/get-clients", response_model=list[ClientResponse])
async def get_clients(db=Depends(get_pg_session)):
    result = await get_clients_service(db)
    return result


@client_router.post("/add-clients", response_model=ClientResponse)
async def add_clients(client_data: ClientCreate, db=Depends(get_pg_session)):
    result = await create_client_service(db, client_data)
    return result
