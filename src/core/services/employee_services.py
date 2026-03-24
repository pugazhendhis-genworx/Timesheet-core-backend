from uuid import UUID

from fastapi import HTTPException

from src.constants.error_constants import EMPLOYEE_NOT_FOUND
from src.data.repositories.employee_repository import (
    create_employee,
    delete_employee,
    get_all_employees,
    get_all_employees_with_assign_status_repo,
    get_employee_by_id,
    update_employee,
)
from src.observability.logging.logging import get_logger
from src.schemas.employee_schemas import EmployeeCreate, EmployeeUpdate

logger = get_logger(__name__)


async def get_all_employees_service(db):
    logger.info("Fetching all employees")

    try:
        employees = await get_all_employees(db)
        logger.info(f"Fetched {len(employees)} employees")
        return employees

    except Exception as e:
        logger.error("Error fetching all employees", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_all_employees_with_assign_status(db):
    logger.info("Fetching all employees with assignment status")

    try:
        employees = await get_all_employees_with_assign_status_repo(db)
        logger.info(f"Fetched {len(employees)} employees with assignment status")
        return employees

    except Exception as e:
        logger.error("Error fetching employees with assignment status", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_employee_by_id_service(db, employee_id: UUID):
    logger.info(f"Fetching employee id={employee_id}")

    try:
        employee = await get_employee_by_id(db, employee_id)

        if not employee:
            logger.warning(f"Employee not found: id={employee_id}")
            raise HTTPException(status_code=404, detail=EMPLOYEE_NOT_FOUND)

        logger.info(f"Employee found: id={employee_id}")
        return employee

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching employee id={employee_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def create_employee_service(db, employee_data: EmployeeCreate):
    logger.info("Creating new employee")

    try:
        employee = await create_employee(db, employee_data)

        logger.info(f"Employee created with id={employee.employee_id}")
        return employee

    except Exception as e:
        logger.error("Error creating employee", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_employee_service(db, employee_id: UUID, employee_data: EmployeeUpdate):
    logger.info(f"Updating employee id={employee_id}")

    try:
        employee = await update_employee(db, employee_id, employee_data)

        if not employee:
            logger.warning(f"Employee not found for update: id={employee_id}")
            raise HTTPException(status_code=404, detail=EMPLOYEE_NOT_FOUND)

        logger.info(f"Employee updated: id={employee_id}")
        return employee

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating employee id={employee_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def delete_employee_service(db, employee_id: UUID):
    logger.info(f"Deleting employee id={employee_id}")

    try:
        employee = await delete_employee(db, employee_id)

        if not employee:
            logger.warning(f"Employee not found for deletion: id={employee_id}")
            raise HTTPException(status_code=404, detail=EMPLOYEE_NOT_FOUND)

        logger.info(f"Employee deleted: id={employee_id}")
        return employee

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting employee id={employee_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
