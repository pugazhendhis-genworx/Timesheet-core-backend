from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.employee_model import Employee
from src.data.repositories.client_repository import get_client_by_id
from src.data.repositories.payroll_repository import (
    get_payroll_ready_entries_by_timesheet_repo,
)
from src.observability.logging.logging import get_logger
from src.schemas.payroll_payslip_schemas import (
    PayrollEmployeePayslipResponse,
    PayrollTimesheetPayslipResponse,
)

logger = get_logger(__name__)


def _to_decimal(value: Decimal | int | float | None) -> Decimal:
    return Decimal(str(value or 0))


async def _get_employee_name_map(
    db: AsyncSession, employee_ids: set[UUID]
) -> dict[UUID, str]:
    if not employee_ids:
        return {}

    stmt = select(Employee).where(Employee.employee_id.in_(employee_ids))
    result = await db.execute(stmt)
    employees = result.scalars().all()

    name_map: dict[UUID, str] = {}
    for employee in employees:
        first_name = (employee.first_name or "").strip()
        last_name = (employee.last_name or "").strip()
        full_name = f"{first_name} {last_name}".strip()
        name_map[employee.employee_id] = full_name or employee.emp_email or ""
    return name_map


async def get_timesheet_payroll_payslips_service(
    db: AsyncSession, timesheet_id: UUID
) -> PayrollTimesheetPayslipResponse | None:
    logger.info(f"Fetching payroll payslips for timesheet_id={timesheet_id}")

    entries = await get_payroll_ready_entries_by_timesheet_repo(db, timesheet_id)
    if not entries:
        logger.warning(f"No payroll entries found for timesheet_id={timesheet_id}")
        return None

    employee_ids = {
        entry.employee_id for entry in entries if entry.employee_id is not None
    }
    employee_name_map = await _get_employee_name_map(db, employee_ids)

    first_entry = entries[0]
    client = await get_client_by_id(db, first_entry.client_id)

    total_regular_hours = Decimal("0")
    total_overtime_hours = Decimal("0")
    total_double_time_hours = Decimal("0")
    total_pay = Decimal("0")
    payroll_slips: list[PayrollEmployeePayslipResponse] = []

    for entry in entries:
        regular_hours = _to_decimal(entry.regular_hours)
        overtime_hours = _to_decimal(entry.overtime_hours)
        double_time_hours = _to_decimal(entry.double_time_hours)
        regular_rate = _to_decimal(entry.regular_rate)
        overtime_rate = _to_decimal(entry.overtime_rate)
        double_time_rate = _to_decimal(entry.double_time_rate)
        reg_pay = _to_decimal(entry.reg_pay)
        ot_pay = _to_decimal(entry.ot_pay)
        holiday_pay = _to_decimal(entry.holiday_pay)

        regular_amount = regular_hours * reg_pay * regular_rate
        holiday_amount = regular_hours * holiday_pay * regular_rate
        overtime_amount = overtime_hours * ot_pay * overtime_rate
        double_time_amount = double_time_hours * reg_pay * double_time_rate
        line_total_pay = (
            regular_amount + holiday_amount + overtime_amount + double_time_amount
        )

        total_regular_hours += regular_hours
        total_overtime_hours += overtime_hours
        total_double_time_hours += double_time_hours
        total_pay += line_total_pay

        payroll_slips.append(
            PayrollEmployeePayslipResponse(
                payroll_entry_id=entry.payroll_entry_id,
                timesheet_id=entry.timesheet_id,
                client_id=entry.client_id,
                employee_id=entry.employee_id,
                employee_name=(
                    employee_name_map.get(entry.employee_id)
                    if entry.employee_id is not None
                    else None
                ),
                week_ending=entry.week_ending,
                regular_hours=regular_hours,
                overtime_hours=overtime_hours,
                double_time_hours=double_time_hours,
                regular_rate=regular_rate,
                overtime_rate=overtime_rate,
                double_time_rate=double_time_rate,
                reg_pay=reg_pay,
                ot_pay=ot_pay,
                holiday_pay=holiday_pay,
                regular_amount=regular_amount,
                holiday_amount=holiday_amount,
                overtime_amount=overtime_amount,
                double_time_amount=double_time_amount,
                total_pay=line_total_pay,
            )
        )

    return PayrollTimesheetPayslipResponse(
        timesheet_id=timesheet_id,
        client_id=first_entry.client_id,
        client_name=client.client_name if client else None,
        week_ending=first_entry.week_ending,
        total_regular_hours=total_regular_hours,
        total_overtime_hours=total_overtime_hours,
        total_double_time_hours=total_double_time_hours,
        total_pay=total_pay,
        payroll_slips=payroll_slips,
    )
