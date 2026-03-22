import logging
from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.services.holiday_service import get_client_holidays_map
from src.data.models.postgres.client_rule_model import RuleViolation
from src.data.models.postgres.timesheet_model import TimeEntryRaw
from src.data.repositories.client_rule_repository import (
    get_client_rules_by_client_id_repo,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def apply_client_rules(
    db: AsyncSession, timesheet_id: UUID, client_id: UUID
) -> None:

    logger.info(
        f"Starting rule engine for timesheet_id={timesheet_id}, client_id={client_id}"
    )

    # 1. Fetch rules
    rules = await get_client_rules_by_client_id_repo(db, client_id, is_active=True)
    logger.info(f"Fetched {len(rules)} rules")

    rule_config = None
    rule_id = None

    for r in rules:
        logger.info(f"Checking rule: {r.rule_type}")
        if r.rule_type == "TIMESHEET_CALCULATION":
            rule_config = r.rule_config
            rule_id = r.rule_id
            logger.info(f"Found TIMESHEET_CALCULATION rule: {rule_config}")
            break

    ot_threshold = (
        Decimal(rule_config.get("ot_threshold", "8")) if rule_config else Decimal("8")
    )
    dt_threshold = (
        Decimal(rule_config.get("dt_threshold", "12")) if rule_config else Decimal("12")
    )

    logger.info(f"Thresholds -> OT: {ot_threshold}, DT: {dt_threshold}")

    # 2. Fetch entries
    stmt = (
        select(TimeEntryRaw)
        .options(joinedload(TimeEntryRaw.paycode))
        .where(TimeEntryRaw.timesheet_id == timesheet_id)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    logger.info(f"Total entries fetched: {len(entries)}")

    if not entries:
        logger.warning("No entries found, exiting")
        return

    # Holidays
    dates_to_check = [e.start_time.date() for e in entries if e.start_time]
    logger.info(f"Dates to check for holidays: {dates_to_check}")

    holiday_map = await get_client_holidays_map(db, dates_to_check, client_id)
    logger.info(f"Holiday map: {holiday_map}")

    violations: list[RuleViolation] = []

    entries_by_emp = defaultdict(list)
    for e in entries:
        entries_by_emp[e.employee_id].append(e)

    logger.info(f"Employees found: {len(entries_by_emp)}")

    for emp_id, emp_entries in entries_by_emp.items():
        logger.info(f"Processing employee: {emp_id}")

        valid_entries = [e for e in emp_entries if e.start_time and e.end_time]
        invalid_entries = [e for e in emp_entries if not (e.start_time and e.end_time)]

        logger.info(
            f"Valid entries: {len(valid_entries)}, Invalid entries: {len(invalid_entries)}"
        )

        for entry in invalid_entries:
            logger.warning("Missing time fields for entry")
            violations.append(
                RuleViolation(
                    timesheet_id=timesheet_id,
                    rule_id=rule_id,
                    violation_type="MISSING_TIME_FIELDS",
                    severity="HIGH",
                    description="Start time or end time is missing.",
                )
            )

        valid_entries.sort(key=lambda x: x.start_time)

        weekly_hours = Decimal(0)

        for entry in valid_entries:
            entry_date = entry.start_time.date()
            is_holiday = entry_date in holiday_map
            paycode = entry.paycode.paycode if entry.paycode else ""

            logger.info(
                f"Entry -> Date: {entry_date}, Paycode: {paycode}, Holiday: {is_holiday}"
            )

            # --- VALIDATION ---
            if entry.end_time <= entry.start_time:
                logger.error("Invalid time range detected")
                violations.append(
                    RuleViolation(
                        timesheet_id=timesheet_id,
                        rule_id=rule_id,
                        violation_type="INVALID_TIME_RANGE",
                        severity="HIGH",
                        description="End time is before or equal to start time.",
                    )
                )

            regular_input = Decimal(str(entry.regular_hours or 0))
            logger.info(f"Regular input hours: {regular_input}")

            if regular_input <= 0:
                logger.error("Zero or negative hours")
                violations.append(
                    RuleViolation(
                        timesheet_id=timesheet_id,
                        rule_id=rule_id,
                        violation_type="ZERO_OR_NEGATIVE_HOURS",
                        severity="HIGH",
                        description="Total extracted hours are zero or negative.",
                    )
                )

            if not paycode:
                logger.error("Missing paycode")
                violations.append(
                    RuleViolation(
                        timesheet_id=timesheet_id,
                        rule_id=rule_id,
                        violation_type="MISSING_PAYCODE",
                        severity="HIGH",
                        description="No paycode assigned to this time entry.",
                    )
                )

            # --- HOLIDAY LOGIC ---
            if paycode == "HOL" and not is_holiday:
                logger.error("HOL marked but not holiday")
                violations.append(
                    RuleViolation(
                        timesheet_id=timesheet_id,
                        rule_id=rule_id,
                        violation_type="INVALID_HOLIDAY_MARKING",
                        severity="HIGH",
                        description="Marked as holiday but date is not valid holiday.",
                    )
                )

            elif paycode == "REG" and is_holiday:
                logger.warning("Holiday marked as REG")
                violations.append(
                    RuleViolation(
                        timesheet_id=timesheet_id,
                        rule_id=rule_id,
                        violation_type="HOLIDAY_AS_REGULAR",
                        severity="MEDIUM",
                        description="Holiday marked as regular working day.",
                    )
                )

            # --- CALCULATION ---
            total_daily = regular_input
            weekly_hours += total_daily

            logger.info(f"Total daily hours: {total_daily}")

            reg_hrs = Decimal(0)
            ot_hrs = Decimal(0)
            dt_hrs = Decimal(0)

            if total_daily > dt_threshold:
                logger.info("Applying Double Time")
                reg_hrs = ot_threshold
                ot_hrs = dt_threshold - ot_threshold
                dt_hrs = total_daily - dt_threshold

            elif total_daily > ot_threshold:
                logger.info("Applying Overtime")
                reg_hrs = ot_threshold
                ot_hrs = total_daily - ot_threshold

            else:
                reg_hrs = total_daily

            if total_daily > Decimal("18"):
                logger.warning(f"Exceeds daily limit: {total_daily}")
                violations.append(
                    RuleViolation(
                        timesheet_id=timesheet_id,
                        rule_id=rule_id,
                        violation_type="EXCEEDS_DAILY_LIMIT",
                        severity="MEDIUM",
                        description=f"Daily hours {total_daily} exceeds limit.",
                    )
                )

            entry.regular_hours = float(reg_hrs)
            entry.overtime_hours = float(ot_hrs)
            entry.double_time_hours = float(dt_hrs)

            logger.info(f"Computed -> REG: {reg_hrs}, OT: {ot_hrs}, DT: {dt_hrs}")

        logger.info(f"Weekly hours: {weekly_hours}")

        if weekly_hours > Decimal("100"):
            logger.warning("Weekly limit exceeded")
            violations.append(
                RuleViolation(
                    timesheet_id=timesheet_id,
                    rule_id=rule_id,
                    violation_type="EXCEEDS_WEEKLY_LIMIT",
                    severity="MEDIUM",
                    description=f"Weekly hours {weekly_hours} exceeds limit.",
                )
            )

    try:
        logger.info(f"Total violations generated: {len(violations)}")

        if violations:
            db.add_all(violations)
            logger.info("Violations added to DB")

        else:
            logger.info("No violations, proceeding to payroll")

            from src.data.models.postgres.timesheet_model import Timesheet

            stmt_ts = select(Timesheet.week_ending).where(
                Timesheet.timesheet_id == timesheet_id
            )
            result_ts = await db.execute(stmt_ts)
            week_ending = result_ts.scalar_one_or_none()

            logger.info(f"Week ending: {week_ending}")

            if rule_config is not None:
                from src.core.services.payroll_service import (
                    create_payroll_records_for_timesheet,
                )

                logger.info("Creating payroll records")

                await create_payroll_records_for_timesheet(
                    db=db,
                    timesheet_id=timesheet_id,
                    client_id=client_id,
                    rule_config=rule_config,
                    entries_by_emp=entries_by_emp,
                    week_ending=week_ending,
                )

        await db.commit()
        logger.info("DB Commit successful")

    except SQLAlchemyError as e:
        logger.error(f"DB Error: {str(e)}")
        await db.rollback()
        raise e
