from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_pg_session
from src.core.services.paycode_service import (
    create_paycode_service,
    get_all_paycodes_service,
)
from src.schemas.paycode_schemas import PaycodeCreate, PaycodeResponse

paycode_router = APIRouter(tags=["paycode"], prefix="/paycode")


@paycode_router.get("/get-paycodes", response_model=list[PaycodeResponse])
async def get_paycodes(db=Depends(get_pg_session)):
    return await get_all_paycodes_service(db)


@paycode_router.post("/add-paycode", response_model=PaycodeResponse)
async def add_paycode(paycode_data: PaycodeCreate, db=Depends(get_pg_session)):
    return await create_paycode_service(db, paycode_data)
