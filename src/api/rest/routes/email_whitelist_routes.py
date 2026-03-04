from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_pg_session
from src.core.services.email_whitelist_services import (
    create_whitelist_service,
    get_all_whitelist_service,
    get_whitelist_by_clientid_service,
)
from src.schemas.email_schemas import EmailWhitelistCreate, EmailWhitelistResponse

whitelist_router = APIRouter(tags=["Whitelist"])


@whitelist_router.get("/get-all-whitelisted-emails")
async def get_all_whitelist_emails(db=Depends(get_pg_session)):
    result = await get_all_whitelist_service(db)
    return result


@whitelist_router.get("/{client_id}", response_model=EmailWhitelistResponse)
async def get_whitelist_by_id(whitelist_id: UUID, db=Depends(get_pg_session)):
    return await get_whitelist_by_clientid_service(whitelist_id, db)


@whitelist_router.post("/add_email", response_model=EmailWhitelistResponse)
async def create_whitelist(
    whitelist_data: EmailWhitelistCreate,
    db=Depends(get_pg_session),
):
    return await create_whitelist_service(whitelist_data, db)
