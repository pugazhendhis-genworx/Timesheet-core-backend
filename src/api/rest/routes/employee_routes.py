from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_pg_session
from src.core.services.employee_services import (
    create_employee_service,
    delete_employee_service,
    get_all_employees_service,
    get_employee_by_id_service,
    update_employee_service,
)
from src.schemas.employee_schemas import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)

employee_router = APIRouter(tags=["employee"], prefix="/employee")


@employee_router.get("/get-employees", response_model=list[EmployeeResponse])
async def get_employees(db=Depends(get_pg_session)):
    return await get_all_employees_service(db)


@employee_router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: UUID, db=Depends(get_pg_session)):
    return await get_employee_by_id_service(db, employee_id)


@employee_router.post("/add-employee", response_model=EmployeeResponse)
async def add_employee(employee_data: EmployeeCreate, db=Depends(get_pg_session)):
    return await create_employee_service(db, employee_data)


@employee_router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    employee_data: EmployeeUpdate,
    db=Depends(get_pg_session),
):
    return await update_employee_service(db, employee_id, employee_data)


@employee_router.delete("/{employee_id}", response_model=EmployeeResponse)
async def delete_employee(employee_id: UUID, db=Depends(get_pg_session)):
    return await delete_employee_service(db, employee_id)
