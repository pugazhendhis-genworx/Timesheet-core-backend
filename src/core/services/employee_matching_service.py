import logging
from uuid import UUID

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.assignment_model import Assignment
from src.data.models.postgres.client_rule_model import RuleViolation
from src.data.models.postgres.employee_model import Employee
from src.data.repositories.time_entry_repository import get_entries_by_timesheet_id
from src.data.repositories.timesheet_repository import (
    get_timesheet_by_id,
    update_timesheet_status,
)

logger = logging.getLogger(__name__)

FUZZY_MATCH_THRESHOLD = 80


async def match_employees_for_timesheet(
    db: AsyncSession,
    timesheet_id: UUID,
    raw_extraction: dict,
) -> bool:
    """
    Match extracted employee identifiers to the employees table.

    Returns True if all entries matched, False otherwise.
    """
    timesheet = await get_timesheet_by_id(db, timesheet_id)
    if not timesheet:
        logger.error("Timesheet %s not found", timesheet_id)
        return False

    entries = await get_entries_by_timesheet_id(db, timesheet_id)
    extraction_entries = raw_extraction.get("entries", [])

    # Load all active employees
    result = await db.execute(select(Employee).where(Employee.is_active.is_(True)))
    all_employees = result.scalars().all()

    all_matched = True

    for idx, entry in enumerate(entries):
        ext_data = extraction_entries[idx] if idx < len(extraction_entries) else {}
        employee_email = ext_data.get("employee_email", "")
        employee_name = ext_data.get("employee_name", "")

        matched_employee = None

        # Strategy 1: Exact email match
        if employee_email:
            matched_employee = _exact_email_match(all_employees, employee_email)

        # Strategy 2: Normalized name match
        if not matched_employee and employee_name:
            matched_employee = _normalized_name_match(all_employees, employee_name)

        # Strategy 3: Fuzzy name match
        if not matched_employee and employee_name:
            matched_employee = _fuzzy_name_match(all_employees, employee_name)

        # Strategy 4: Fuzzy email-as-name match (email before @ as name)
        if not matched_employee and employee_email and "@" in employee_email:
            name_from_email = employee_email.split("@")[0].replace(".", " ")
            matched_employee = _fuzzy_name_match(all_employees, name_from_email)

        if matched_employee:
            # Set entry status to MATCHED
            entry.employee_id = matched_employee.employee_id
            entry.matching_status = "MATCHED"
            await db.flush()

            # Validate assignment
            assignment_valid = await _validate_assignment(
                db,
                matched_employee.employee_id,
                timesheet.client_id,
                timesheet_id,
            )
            if not assignment_valid:
                entry.matching_status = "ASSIGNMENT_VIOLATION"
                entry.employee_unmatched_reason = (
                    f"Employee {matched_employee.first_name} "
                    f"{matched_employee.last_name} has no active "
                    f"assignment for this client"
                )
                all_matched = False
                logger.warning(
                    "Assignment violation for entry %s: "
                    "employee %s not assigned to client %s",
                    entry.timeentry_id,
                    matched_employee.employee_id,
                    timesheet.client_id,
                )
            else:
                logger.info(
                    "Matched & verified entry %s → employee %s",
                    entry.timeentry_id,
                    matched_employee.employee_id,
                )
        else:
            # No match found
            entry.matching_status = "EMPLOYEE_UNMATCHED"
            entry.employee_unmatched_reason = (
                f"No match found for '{employee_name or employee_email}' "
                f"(email={employee_email}, name={employee_name})"
            )
            all_matched = False
            logger.warning(
                "No match for entry %s (email=%s, name=%s)",
                entry.timeentry_id,
                employee_email,
                employee_name,
            )

        await db.flush()

    # Update timesheet status
    new_status = "MATCHED" if all_matched else "UNMATCHED"
    await update_timesheet_status(db, timesheet_id, new_status)

    return all_matched


def _exact_email_match(employees: list[Employee], email: str) -> Employee | None:
    email_lower = email.strip().lower()
    for emp in employees:
        if emp.emp_email and emp.emp_email.strip().lower() == email_lower:
            return emp
    return None


def _normalized_name_match(employees: list[Employee], name: str) -> Employee | None:
    normalized = _normalize(name)
    for emp in employees:
        full_name = _normalize(f"{emp.first_name} {emp.last_name}")
        if full_name == normalized:
            return emp
        # Also try reversed order
        reversed_name = _normalize(f"{emp.last_name} {emp.first_name}")
        if reversed_name == normalized:
            return emp
    return None


def _fuzzy_name_match(employees: list[Employee], name: str) -> Employee | None:
    best_match = None
    best_score = 0

    normalized_input = _normalize(name)

    for emp in employees:
        full_name = _normalize(f"{emp.first_name} {emp.last_name}")
        score = fuzz.token_sort_ratio(normalized_input, full_name)
        if score > best_score and score >= FUZZY_MATCH_THRESHOLD:
            best_score = score
            best_match = emp

    return best_match


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


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


def _get_fuzzy_score(name: str, employee: Employee) -> int:
    """Get fuzzy match score between name and employee full name."""
    normalized_input = _normalize(name)
    full_name = _normalize(f"{employee.first_name} {employee.last_name}")
    return fuzz.token_sort_ratio(normalized_input, full_name)


# ── Client validation ──────────────────────────────────────────────────────


async def validate_client_for_timesheet(
    db: AsyncSession,
    timesheet_id: UUID,
    raw_extraction: dict,
) -> bool:
    """
    Validate that the extracted client matches the resolved timesheet client.

    Compares extraction's client_name/client_id against the timesheet's client_id.
    If there's a mismatch, sets matching_status to CLIENT_UNMATCHED for all entries.

    Returns True if client is valid, False otherwise.
    """
    from sqlalchemy.orm import joinedload

    from src.data.models.postgres.timesheet_model import Timesheet

    # Load timesheet with client relationship
    result = await db.execute(
        select(Timesheet)
        .where(Timesheet.timesheet_id == timesheet_id)
        .options(joinedload(Timesheet.client))
    )
    timesheet = result.unique().scalar_one_or_none()

    if not timesheet:
        logger.error("Timesheet %s not found", timesheet_id)
        return False

    # Get the resolved client
    resolved_client = timesheet.client
    if not resolved_client:
        logger.warning("No client loaded for timesheet %s", timesheet_id)
        # If we can't find the client, mark all entries as unmatched
        entries = await get_entries_by_timesheet_id(db, timesheet_id)
        for entry in entries:
            if entry.matching_status == "MATCHED":
                # Only set client_unmatched_reason if employee is already matched
                entry.client_unmatched_reason = (
                    f"Client {timesheet.client_id} not found in system"
                )
            await db.flush()
        return False

    # Get extraction data
    extraction_data = raw_extraction or {}
    extracted_client_name = extraction_data.get("client_name", "").strip()

    # If no client name extracted, we can't validate
    if not extracted_client_name:
        logger.info(
            "No client_name in extraction for timesheet %s, skipping validation",
            timesheet_id,
        )
        return True  # Can't validate, but not an error

    # Compare extraction client_name with resolved client_name
    if _is_client_match(extracted_client_name, resolved_client.client_name):
        # Client matches - no action needed
        logger.info(
            "Client validated for timesheet %s: '%s' → %s",
            timesheet_id,
            extracted_client_name,
            resolved_client.client_id,
        )
        return True
    else:
        # Mismatch - mark all MATCHED entries as CLIENT_UNMATCHED
        logger.warning(
            "Client mismatch for timesheet %s: extracted '%s' ≠ resolved '%s'",
            timesheet_id,
            extracted_client_name,
            resolved_client.client_name,
        )

        entries = await get_entries_by_timesheet_id(db, timesheet_id)
        for entry in entries:
            if entry.matching_status != "MATCHED":
                # Only update if employee is already matched
                continue
            entry.matching_status = "CLIENT_UNMATCHED"
            entry.client_unmatched_reason = (
                f"Extracted client '{extracted_client_name}' "
                f"does not match resolved client '{resolved_client.client_name}'"
            )
            await db.flush()

        return False


def _is_client_match(extracted_name: str, system_name: str) -> bool:
    """Check if extracted client name matches system client name."""
    # Exact match (case-insensitive)
    if extracted_name.lower().strip() == system_name.lower().strip():
        return True

    # Normalized match
    extracted_normalized = _normalize(extracted_name)
    system_normalized = _normalize(system_name)
    if extracted_normalized == system_normalized:
        return True

    # Fuzzy match (high threshold for client names)
    score = fuzz.token_sort_ratio(extracted_normalized, system_normalized)
    if score >= 85:  # Higher threshold for clients (fewer false positives)
        return True
    return False
