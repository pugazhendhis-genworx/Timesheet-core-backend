from uuid import UUID

from fastapi import HTTPException

from src.constants.error_constants import EMPLOYEE_NOT_FOUND
from src.data.repositories.employee_repository import (
    create_employee,
    delete_employee,
    get_all_employees,
    get_employee_by_id,
    update_employee,
)
from src.schemas.employee_schemas import EmployeeCreate, EmployeeUpdate


async def get_all_employees_service(db):
    try:
        return await get_all_employees(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_employee_by_id_service(db, employee_id: UUID):
    employee = await get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=EMPLOYEE_NOT_FOUND)
    return employee


async def create_employee_service(db, employee_data: EmployeeCreate):
    try:
        return await create_employee(db, employee_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_employee_service(db, employee_id: UUID, employee_data: EmployeeUpdate):
    employee = await update_employee(db, employee_id, employee_data)
    if not employee:
        raise HTTPException(status_code=404, detail=EMPLOYEE_NOT_FOUND)
    return employee


async def delete_employee_service(db, employee_id: UUID):
    employee = await delete_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail=EMPLOYEE_NOT_FOUND)
    return employee
