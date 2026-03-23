from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.rest.dependencies import DBSession, require_roles
from src.core.services.assignment_services import (
    create_assignment_service,
    delete_assignment_service,
    get_all_assignments_service,
    get_assignment_by_id_service,
    get_assignments_by_client_service,
    get_assignments_by_employee_service,
    update_assignment_service,
)
from src.schemas.assignment_schemas import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)

assignment_router = APIRouter(
    tags=["assignment"],
    prefix="/assignment",
    dependencies=[Depends(require_roles(["operation_executive", "auditor"]))],
)


@assignment_router.get("/get-assignments", response_model=list[AssignmentResponse])
async def get_assignments(db: DBSession):
    return await get_all_assignments_service(db)


@assignment_router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(assignment_id: UUID, db: DBSession):
    return await get_assignment_by_id_service(db, assignment_id)


@assignment_router.get(
    "/employee/{employee_id}", response_model=list[AssignmentResponse]
)
async def get_assignments_by_employee(employee_id: UUID, db: DBSession):
    return await get_assignments_by_employee_service(db, employee_id)


@assignment_router.get("/client/{client_id}", response_model=list[AssignmentResponse])
async def get_assignments_by_client(client_id: UUID, db: DBSession):
    return await get_assignments_by_client_service(db, client_id)


@assignment_router.post("/assign-employee", response_model=AssignmentResponse)
async def assign_employee(assignment_data: AssignmentCreate, db: DBSession):
    return await create_assignment_service(db, assignment_data)


@assignment_router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    assignment_data: AssignmentUpdate,
    db: DBSession,
):
    return await update_assignment_service(db, assignment_id, assignment_data)


@assignment_router.delete("/{assignment_id}", response_model=AssignmentResponse)
async def delete_assignment(assignment_id: UUID, db: DBSession):
    return await delete_assignment_service(db, assignment_id)
