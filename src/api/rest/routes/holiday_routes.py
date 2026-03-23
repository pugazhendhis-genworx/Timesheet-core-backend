from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.rest.dependencies import DBSession, require_roles
from src.core.services.holiday_service import (
    add_holiday,
    delete_holiday_service,
    get_holidays_by_client,
    update_holiday_service,
)
from src.schemas.holiday_schemas import HolidayCreate, HolidayResponse, HolidayUpdate

holiday_router = APIRouter(
    tags=["holiday"],
    prefix="/holiday",
    dependencies=[Depends(require_roles(["operation_executive", "auditor"]))],
)


@holiday_router.post("/create_holiday", response_model=HolidayResponse)
async def create_client_holiday(holiday_data: HolidayCreate, db: DBSession):
    return await add_holiday(db, holiday_data)


@holiday_router.get("/client/{client_id}", response_model=list[HolidayResponse])
async def list_client_holidays(client_id: UUID, db: DBSession):
    return await get_holidays_by_client(db, client_id)


@holiday_router.put("/{holiday_id}", response_model=HolidayResponse)
async def update_client_holiday(
    holiday_id: UUID, holiday_data: HolidayUpdate, db: DBSession
):
    holiday = await update_holiday_service(db, holiday_id, holiday_data)
    if not holiday:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found"
        )
    return holiday


@holiday_router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_holiday(holiday_id: UUID, db: DBSession):
    success = await delete_holiday_service(db, holiday_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found"
        )
