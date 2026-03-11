from uuid import UUID

from fastapi import HTTPException

from src.data.repositories.assignment_repository import (
    create_assignment,
    delete_assignment,
    get_all_assignments,
    get_assignment_by_id,
    get_assignments_by_client_id,
    get_assignments_by_employee_id,
    update_assignment,
)
from src.schemas.assignment_schemas import AssignmentCreate, AssignmentUpdate


async def get_all_assignments_service(db):
    try:
        return await get_all_assignments(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_assignment_by_id_service(db, assignment_id: UUID):
    assignment = await get_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


async def get_assignments_by_employee_service(db, employee_id: UUID):
    try:
        return await get_assignments_by_employee_id(db, employee_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_assignments_by_client_service(db, client_id: UUID):
    try:
        return await get_assignments_by_client_id(db, client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_assignment_service(db, assignment_data: AssignmentCreate):
    try:
        return await create_assignment(db, assignment_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_assignment_service(
    db, assignment_id: UUID, assignment_data: AssignmentUpdate
):
    assignment = await update_assignment(db, assignment_id, assignment_data)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


async def delete_assignment_service(db, assignment_id: UUID):
    assignment = await delete_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment
