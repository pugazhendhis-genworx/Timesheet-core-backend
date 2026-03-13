from uuid import UUID

from fastapi import APIRouter

from src.api.rest.dependencies import DBSession
from src.core.services.employee_services import (
    create_employee_service,
    delete_employee_service,
    get_all_employees_service,
    get_all_employees_with_assign_status,
    get_employee_by_id_service,
    update_employee_service,
)
from src.schemas.employee_schemas import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    EmployeeWithAssignStatusResponse,
)

employee_router = APIRouter(tags=["employee"], prefix="/employee")


@employee_router.get("/get-employees", response_model=list[EmployeeResponse])
async def get_employees(db: DBSession):
    return await get_all_employees_service(db)


@employee_router.get(
    "/get-employees-with-assign-status",
    response_model=list[EmployeeWithAssignStatusResponse],
)
async def get_employees_with_assign_status(db: DBSession):
    return await get_all_employees_with_assign_status(db)


@employee_router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: UUID, db: DBSession):
    return await get_employee_by_id_service(db, employee_id)


@employee_router.post("/add-employee", response_model=EmployeeResponse)
async def add_employee(employee_data: EmployeeCreate, db: DBSession):
    return await create_employee_service(db, employee_data)


@employee_router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID, employee_data: EmployeeUpdate, db: DBSession
):
    return await update_employee_service(db, employee_id, employee_data)


@employee_router.delete("/{employee_id}", response_model=EmployeeResponse)
async def delete_employee(employee_id: UUID, db: DBSession):
    return await delete_employee_service(db, employee_id)
