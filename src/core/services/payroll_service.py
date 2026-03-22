from datetime import date
from decimal import Decimal
from typing import Dict, List, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.payroll_model import PayrollReadyEntry
from src.data.models.postgres.timesheet_model import TimeEntryRaw
from src.data.repositories.payroll_repository import (
    create_payroll_ready_entries_repo,
    get_all_payroll_ready_repo,
    get_payroll_ready_by_id_repo,
    get_payroll_ready_entries_by_timesheet_repo,
)
from src.data.repositories.rule_violation_repository import (
    get_rule_violations_by_timesheet_id_repo,
)


async def create_payroll_records_for_timesheet(
    db: AsyncSession,
    timesheet_id: UUID,
    client_id: UUID,
    rule_config: dict,
    entries_by_emp: Dict[UUID, List[TimeEntryRaw]],
    week_ending: date | None,
) -> None:
    payroll_entries = []

    # Map raw rates strictly mapping fields without arithmetic modifications to pay bounds.
    reg_markup_rate = rule_config.get("reg_markup_rate", 1.0)
    ot_markup_rate = rule_config.get("ot_markup_rate", 1.5)
    dt_markup_rate = rule_config.get("dt_markup_rate", 2.0)

    reg_pay_config = rule_config.get("reg_pay", 0)
    ot_pay_config = rule_config.get("ot_pay", 0)
    dt_pay_config = rule_config.get("dt_pay", 0)
    holiday_pay_config = rule_config.get("holiday_pay", 0)

    for emp_id, emp_entries in entries_by_emp.items():
        total_reg = Decimal(0)
        total_ot = Decimal(0)
        total_dt = Decimal(0)

        for entry in emp_entries:
            total_reg += Decimal(str(entry.regular_hours or 0))
            total_ot += Decimal(str(entry.overtime_hours or 0))
            total_dt += Decimal(str(entry.double_time_hours or 0))

        pr_entry = PayrollReadyEntry(
            timesheet_id=timesheet_id,
            client_id=client_id,
            employee_id=emp_id,
            week_ending=week_ending,
            regular_hours=total_reg,
            overtime_hours=total_ot,
            double_time_hours=total_dt,
            regular_rate=Decimal(str(reg_markup_rate)),
            overtime_rate=Decimal(str(ot_markup_rate)),
            double_time_rate=Decimal(str(dt_markup_rate)),
            reg_pay=Decimal(str(reg_pay_config)),
            ot_pay=Decimal(str(ot_pay_config)),
            holiday_pay=Decimal(str(holiday_pay_config)),
        )
        payroll_entries.append(pr_entry)

    if payroll_entries:
        await create_payroll_ready_entries_repo(db, payroll_entries)


async def get_all_payroll_ready_service(db: AsyncSession):
    return await get_all_payroll_ready_repo(db)


async def get_payroll_ready_by_id_service(db: AsyncSession, payroll_entry_id: UUID):
    return await get_payroll_ready_by_id_repo(db, payroll_entry_id)


async def get_payroll_timesheet_summary_service(db: AsyncSession, timesheet_id: UUID):
    entries = await get_payroll_ready_entries_by_timesheet_repo(db, timesheet_id)
    violations = await get_rule_violations_by_timesheet_id_repo(db, timesheet_id)

    return {
        "timesheet_id": timesheet_id,
        "payroll_entries": entries,
        "violations": violations,
    }
