from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.assignment_model import Assignment
from src.schemas.assignment_schemas import AssignmentCreate, AssignmentUpdate


async def get_all_assignments(db: AsyncSession):
    result = await db.execute(select(Assignment))
    return result.scalars().all()


async def get_assignment_by_id(db: AsyncSession, assignment_id: UUID):
    result = await db.execute(
        select(Assignment).where(Assignment.assignment_id == assignment_id)
    )
    return result.scalar_one_or_none()


async def get_assignments_by_employee_id(db: AsyncSession, employee_id: UUID):
    result = await db.execute(
        select(Assignment).where(Assignment.employee_id == employee_id)
    )
    return result.scalars().all()


async def get_assignments_by_client_id(db: AsyncSession, client_id: UUID):
    result = await db.execute(
        select(Assignment).where(Assignment.client_id == client_id)
    )
    return result.scalars().all()


async def create_assignment(db: AsyncSession, assignment_data: AssignmentCreate):
    new_assignment = Assignment(
        employee_id=assignment_data.employee_id,
        client_id=assignment_data.client_id,
        start_date=assignment_data.start_date,
        end_date=assignment_data.end_date,
        regular_rate=assignment_data.regular_rate,
        overtime_rate=assignment_data.overtime_rate,
        double_time_rate=assignment_data.double_time_rate,
        paycode_id=assignment_data.paycode_id,
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)
    return new_assignment


async def update_assignment(
    db: AsyncSession, assignment_id: UUID, assignment_data: AssignmentUpdate
):
    assignment = await get_assignment_by_id(db, assignment_id)
    if not assignment:
        return None

    update_fields = assignment_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(assignment, field, value)

    await db.commit()
    await db.refresh(assignment)
    return assignment


async def delete_assignment(db: AsyncSession, assignment_id: UUID):
    assignment = await get_assignment_by_id(db, assignment_id)
    if not assignment:
        return None

    assignment.is_active = False
    await db.commit()
    await db.refresh(assignment)
    return assignment
