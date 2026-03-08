from uuid import UUID

from fastapi import HTTPException

from src.data.repositories.email_whitelist_repository import (
    create_whitelist_email,
    get_all_whitelisted_emails,
    get_whitelisted_email_by_client_id,
)
from src.schemas.email_schemas import EmailWhitelistCreate


async def get_all_whitelist_service(db):
    try:
        return await get_all_whitelisted_emails(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_whitelist_by_clientid_service(client_id: UUID, db):
    try:
        entry = await get_whitelisted_email_by_client_id(client_id, db)

        if not entry:
            raise HTTPException(status_code=404, detail="Whitelist entry not found")

        return entry
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_whitelist_service(whitelist_data: EmailWhitelistCreate, db):
    try:
        return await create_whitelist_email(whitelist_data, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
