from fastapi import APIRouter

from src.api.rest.dependencies import DBSession
from src.core.services.paycode_service import (
    create_paycode_service,
    get_all_paycodes_service,
)
from src.schemas.paycode_schemas import PaycodeCreate, PaycodeResponse

paycode_router = APIRouter(tags=["paycode"], prefix="/paycode")


@paycode_router.get("/get-paycodes", response_model=list[PaycodeResponse])
async def get_paycodes(db: DBSession):
    return await get_all_paycodes_service(db)


@paycode_router.post("/add-paycode", response_model=PaycodeResponse)
async def add_paycode(paycode_data: PaycodeCreate, db: DBSession):
    return await create_paycode_service(db, paycode_data)
