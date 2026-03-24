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
from src.observability.logging.logging import get_logger
from src.schemas.assignment_schemas import AssignmentCreate, AssignmentUpdate

logger = get_logger(__name__)


async def get_all_assignments_service(db):
    logger.info("Fetching all assignments")
    try:
        assignments = await get_all_assignments(db)
        logger.info(f"Fetched {len(assignments)} assignments")
        return assignments
    except Exception as e:
        logger.error("Error fetching all assignments", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_assignment_by_id_service(db, assignment_id: UUID):
    try:
        logger.info(f"Fetching assignment with id={assignment_id}")
        assignment = await get_assignment_by_id(db, assignment_id)
        if not assignment:
            logger.warning(f"Assignment not found: id={assignment_id}")
            raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)
        logger.info(f"Assignment found: id={assignment_id}")
        return assignment
    except Exception as e:
        logger.error(f"Error fetching assignment id={assignment_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_assignments_by_employee_service(db, employee_id: UUID):
    logger.info(f"Fetching assignments for employee_id={employee_id}")
    try:
        assignments = await get_assignments_by_employee_id(db, employee_id)
        logger.info(
            f"Found {len(assignments)} assignments for employee_id={employee_id}"
        )
        return assignments
    except Exception as e:
        logger.error(
            f"Error fetching assignments for employee_id={employee_id}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_assignments_by_client_service(db, client_id: UUID):
    logger.info(f"Fetching assignments for client_id={client_id}")
    try:
        assignments = await get_assignments_by_client_id(db, client_id)
        logger.info(f"Found {len(assignments)} assignments for client_id={client_id}")
        return assignments
    except Exception as e:
        logger.error(
            f"Error fetching assignments for client_id={client_id}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_assignment_service(db, assignment_data: AssignmentCreate):
    logger.info("Creating new assignment")
    try:
        assignment = await create_assignment(db, assignment_data)
        logger.info(
            f"Assignment created with id={assignment.assignment_id}, "
            f"client_id={assignment.client_id}, employee_id={assignment.employee_id}"
        )

        await create_audit_log(
            db,
            action="CREATED",
            entity_type="ASSIGNMENT",
            entity_id=str(assignment.assignment_id),
            metadata_json={
                "client_id": str(assignment.client_id),
                "employee_id": str(assignment.employee_id),
            },
        )

        logger.info(f"Audit log created for assignment id={assignment.assignment_id}")
        return assignment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_assignment_service(
    db, assignment_id: UUID, assignment_data: AssignmentUpdate
):
    logger.info(f"Updating assignment id={assignment_id}")
    try:
        assignment = await update_assignment(db, assignment_id, assignment_data)

        if not assignment:
            logger.warning(f"Assignment not found for update: id={assignment_id}")
            raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)

        logger.info(f"Assignment updated: id={assignment_id}")

        await create_audit_log(
            db,
            action="UPDATED",
            entity_type="ASSIGNMENT",
            entity_id=str(assignment.assignment_id),
            metadata_json={"updates": assignment_data.model_dump(exclude_unset=True)},
        )

        logger.info(f"Audit log created for updated assignment id={assignment_id}")
        return assignment

    except Exception as e:
        logger.error(f"Error updating assignment id={assignment_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def delete_assignment_service(db, assignment_id: UUID):
    logger.info(f"Deleting assignment id={assignment_id}")
    try:
        assignment = await delete_assignment(db, assignment_id)

        if not assignment:
            logger.warning(f"Assignment not found for deletion: id={assignment_id}")
            raise HTTPException(status_code=404, detail=ASSIGNMENT_NOT_FOUND)

        logger.info(f"Assignment deleted: id={assignment_id}")
        return assignment

    except Exception as e:
        logger.error(f"Error deleting assignment id={assignment_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
