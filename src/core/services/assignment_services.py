from uuid import UUID

from fastapi import HTTPException

from src.constants.error_constants import ASSIGNMENT_NOT_FOUND
from src.data.repositories.assignment_repository import (
    create_assignment,
    delete_assignment,
    get_all_assignments,
    get_assignment_by_id,
    get_assignments_by_client_id,
    get_assignments_by_employee_id,
    update_assignment,
)
from src.data.repositories.audit_log_repository import create_audit_log
from src.schemas.assignment_schemas import AssignmentCreate, AssignmentUpdate


async def get_all_assignments_service(db):
    try:
        return await get_all_assignments(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_assignment_by_id_service(db, assignment_id: UUID):
    try:
        assignment = await get_assignment_by_id(db, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
        return assignment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


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
        assignment = await create_assignment(db, assignment_data)
        await create_audit_log(
            db,
            action="CREATED",
            entity_type="ASSIGNMENT",
            entity_id=str(assignment.assignment_id),
            metadata_json={"client_id": str(assignment.client_id), "employee_id": str(assignment.employee_id)},
        )
        return assignment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_assignment_service(
    db, assignment_id: UUID, assignment_data: AssignmentUpdate
):
    try:
        assignment = await update_assignment(db, assignment_id, assignment_data)
        if not assignment:
            raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
        
        await create_audit_log(
            db,
            action="UPDATED",
            entity_type="ASSIGNMENT",
            entity_id=str(assignment.assignment_id),
            metadata_json={"updates": assignment_data.model_dump(exclude_unset=True)},
        )
        return assignment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def delete_assignment_service(db, assignment_id: UUID):
    try:
        assignment = await delete_assignment(db, assignment_id)
        if not assignment:
            raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
        return assignment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
