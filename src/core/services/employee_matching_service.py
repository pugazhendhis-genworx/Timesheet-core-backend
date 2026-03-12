import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.data.models.postgres.timesheet_model import Timesheet
from src.data.repositories.employee_repository import get_all_active_employees
from src.data.repositories.time_entry_repository import get_entries_by_timesheet_id
from src.data.repositories.timesheet_repository import (
    get_timesheet_by_id,
    update_timesheet_status,
)
from src.utils.matching_utils import (
    _exact_email_match,
    _fuzzy_name_match,
    _is_client_match,
    _normalized_name_match,
)
from src.utils.validation_helper import _validate_assignment

logger = logging.getLogger(__name__)


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

    all_employees = await get_all_active_employees(db)

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
