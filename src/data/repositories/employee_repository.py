from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.employee_model import Employee
from src.schemas.employee_schemas import EmployeeCreate, EmployeeUpdate


async def get_all_employees(db: AsyncSession):
    result = await db.execute(select(Employee))
    return result.scalars().all()


async def get_employee_by_id(db: AsyncSession, employee_id: UUID):
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_id)
    )
    return result.scalar_one_or_none()


async def get_all_active_employees(db: AsyncSession):
    result = await db.execute(select(Employee).where(Employee.is_active.is_(True)))
    return result.scalars().all()


async def create_employee(db: AsyncSession, employee_data: EmployeeCreate):
    new_employee = Employee(
        emp_email=employee_data.emp_email,
        first_name=employee_data.first_name,
        last_name=employee_data.last_name,
        dob=employee_data.dob,
        designation=employee_data.designation,
    )
    db.add(new_employee)
    await db.commit()
    await db.refresh(new_employee)
    return new_employee


async def update_employee(
    db: AsyncSession, employee_id: UUID, employee_data: EmployeeUpdate
):
    employee = await get_employee_by_id(db, employee_id)
    if not employee:
        return None

    update_fields = employee_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    return employee


async def delete_employee(db: AsyncSession, employee_id: UUID):
    employee = await get_employee_by_id(db, employee_id)
    if not employee:
        return None

    employee.is_active = False
    await db.commit()
    await db.refresh(employee)
    return employee
