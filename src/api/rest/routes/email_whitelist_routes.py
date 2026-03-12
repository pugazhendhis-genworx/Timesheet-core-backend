from uuid import UUID

from fastapi import APIRouter

from src.api.rest.dependencies import DBSession
from src.core.services.email_whitelist_services import (
    create_whitelist_service,
    get_all_whitelist_service,
    get_whitelist_by_clientid_service,
)
from src.schemas.email_schemas import EmailWhitelistCreate, EmailWhitelistResponse

whitelist_router = APIRouter(tags=["Whitelist"], prefix="/whitelist")


@whitelist_router.get("/get-all-whitelisted-emails")
async def get_all_whitelist_emails(db: DBSession):
    result = await get_all_whitelist_service(db)
    return result


@whitelist_router.get("/{client_id}", response_model=EmailWhitelistResponse)
async def get_whitelist_by_id(client_id: UUID, db: DBSession):
    return await get_whitelist_by_clientid_service(client_id, db)


@whitelist_router.post("/add_email", response_model=EmailWhitelistResponse)
async def create_whitelist(whitelist_data: EmailWhitelistCreate, db: DBSession):
    return await create_whitelist_service(whitelist_data, db)
