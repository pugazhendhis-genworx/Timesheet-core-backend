import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.assignment_model import Assignment
from src.data.models.postgres.client_rule_model import RuleViolation

logger = logging.getLogger(__name__)


async def _validate_assignment(
    db: AsyncSession,
    employee_id: UUID,
    client_id: UUID,
    timesheet_id: UUID,
) -> bool:
    """Check if employee has an active assignment for the client.
    Returns True if valid, False if violation.
    """
    result = await db.execute(
        select(Assignment).where(
            Assignment.employee_id == employee_id,
            Assignment.client_id == client_id,
            Assignment.is_active.is_(True),
        )
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        violation = RuleViolation(
            timesheet_id=timesheet_id,
            severity="HIGH",
            description=(
                f"Employee {employee_id} has no active assignment "
                f"for client {client_id}"
            ),
        )
        db.add(violation)
        await db.flush()
        logger.warning(
            "Assignment violation: employee %s not assigned to client %s",
            employee_id,
            client_id,
        )
        return False
    return True
