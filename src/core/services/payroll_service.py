from datetime import date
from decimal import Decimal
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
from src.observability.logging.logging import get_logger

logger = get_logger(__name__)


async def create_payroll_records_for_timesheet(
    db: AsyncSession,
    timesheet_id: UUID,
    client_id: UUID,
    rule_config: dict,
    entries_by_emp: dict[UUID, list[TimeEntryRaw]],
    week_ending: date | None,
) -> None:
    logger.info(
        f"""Creating payroll records
        for timesheet_id={timesheet_id}, client_id={client_id}"""
    )
    try:
        payroll_entries = []

        """ Map raw rates strictly mapping fields without arithmetic modifications
        to pay bounds """

        reg_markup_rate = rule_config.get("reg_markup_rate", 1.0)
        ot_markup_rate = rule_config.get("ot_markup_rate", 1.5)
        dt_markup_rate = rule_config.get("dt_markup_rate", 2.0)

        reg_pay_config = rule_config.get("reg_pay", 0)
        ot_pay_config = rule_config.get("ot_pay", 0)
        dt_pay_config = rule_config.get("dt_pay", 0)  # noqa
        holiday_pay_config = rule_config.get("holiday_pay", 0)

        logger.debug(
            f"Rule config for timesheet_id={timesheet_id}: "
            f"reg={reg_markup_rate}, ot={ot_markup_rate}, dt={dt_markup_rate}"
        )

        for emp_id, emp_entries in entries_by_emp.items():
            logger.debug(f"Processing employee_id={emp_id}, entries={len(emp_entries)}")
            total_reg = Decimal(0)
            total_ot = Decimal(0)
            total_dt = Decimal(0)

            for entry in emp_entries:
                total_reg += Decimal(str(entry.regular_hours or 0))
                total_ot += Decimal(str(entry.overtime_hours or 0))
                total_dt += Decimal(str(entry.double_time_hours or 0))
            logger.debug(
                f"Calculated hours for employee_id={emp_id}: "
                f"reg={total_reg}, ot={total_ot}, dt={total_dt}"
            )
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
            logger.info(
                f"""Created {len(payroll_entries)} payroll
                entries for timesheet_id={timesheet_id}"""
            )
        else:
            logger.warning(
                f"No payroll entries created for timesheet_id={timesheet_id}"
            )
    except Exception:
        logger.error(
            f"Error creating payroll records for timesheet_id={timesheet_id}",
            exc_info=True,
        )
        raise


async def get_all_payroll_ready_service(db: AsyncSession):
    logger.info("Fetching all payroll ready entries")

    try:
        entries = await get_all_payroll_ready_repo(db)

        logger.info(f"Fetched {len(entries)} payroll entries")
        return entries

    except Exception:
        logger.error("Error fetching payroll entries", exc_info=True)
        raise


async def get_payroll_ready_by_id_service(db: AsyncSession, payroll_entry_id: UUID):
    logger.info(f"Fetching payroll entry id={payroll_entry_id}")

    try:
        entry = await get_payroll_ready_by_id_repo(db, payroll_entry_id)

        if not entry:
            logger.warning(f"Payroll entry not found: id={payroll_entry_id}")

        return entry

    except Exception:
        logger.error(
            f"Error fetching payroll entry id={payroll_entry_id}",
            exc_info=True,
        )
        raise


async def get_payroll_timesheet_summary_service(db: AsyncSession, timesheet_id: UUID):
    logger.info(f"Fetching payroll summary for timesheet_id={timesheet_id}")

    try:
        entries = await get_payroll_ready_entries_by_timesheet_repo(db, timesheet_id)
        violations = await get_rule_violations_by_timesheet_id_repo(db, timesheet_id)

        logger.info(
            f"Fetched payroll summary for timesheet_id={timesheet_id}: "
            f"entries={len(entries)}, violations={len(violations)}"
        )

        return {
            "timesheet_id": timesheet_id,
            "payroll_entries": entries,
            "violations": violations,
        }

    except Exception:
        logger.error(
            f"Error fetching payroll summary for timesheet_id={timesheet_id}",
            exc_info=True,
        )
        raise
