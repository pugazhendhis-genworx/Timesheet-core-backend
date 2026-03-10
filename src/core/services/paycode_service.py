from fastapi import HTTPException

from src.data.repositories.paycode_repository import (
    create_paycode,
    get_all_paycodes,
)
from src.schemas.paycode_schemas import PaycodeCreate


async def get_all_paycodes_service(db):
    try:
        return await get_all_paycodes(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_paycode_service(db, paycode_data: PaycodeCreate):
    try:
        return await create_paycode(db, paycode_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
