from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.api.rest.dependencies import get_pg_session
from src.core.services.timesheet_service import (
    decide_timesheet_approval_service,
    get_all_timesheets_service,
    get_extracted_timesheet_by_id_for_display,
    get_extracted_timesheets_for_display,
    get_payroll_ready_timesheets,
    get_timesheet_by_id_service,
    get_timesheet_entries_service,
    get_timesheets_by_client_service,
    get_timesheets_by_status_service,
    submit_for_approval_service,
    update_timesheet_service,
)
from src.schemas.display_schemas import ApprovalDecisionRequest
from src.schemas.timesheet_schemas import TimeEntryRawResponse, TimesheetResponse
from src.schemas.timesheet_update_schemas import TimesheetUpdate

timesheet_router = APIRouter(tags=["timesheet"], prefix="/timesheet")


@timesheet_router.get("/get-timesheets", response_model=list[TimesheetResponse])
async def get_timesheets(db=Depends(get_pg_session)):
    result = await get_all_timesheets_service(db)
    return result


@timesheet_router.get("/status/{status}", response_model=list[TimesheetResponse])
async def get_timesheets_by_status(status: str, db=Depends(get_pg_session)):
    return await get_timesheets_by_status_service(db, status)


@timesheet_router.get("/client/{client_id}", response_model=list[TimesheetResponse])
async def get_timesheets_by_client(client_id: UUID, db=Depends(get_pg_session)):
    return await get_timesheets_by_client_service(db, client_id)


@timesheet_router.post(
    "/{timesheet_id}/submit-for-approval", response_model=TimesheetResponse
)
async def submit_for_approval(timesheet_id: UUID, db=Depends(get_pg_session)):
    """Move an extracted/matched timesheet to READY_FOR_APPROVAL."""
    return await submit_for_approval_service(db, timesheet_id)


@timesheet_router.get("/{timesheet_id}", response_model=TimesheetResponse)
async def get_timesheet(timesheet_id: UUID, db=Depends(get_pg_session)):
    result = await get_timesheet_by_id_service(db, timesheet_id)
    if not result:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    return result


@timesheet_router.put("/{timesheet_id}", response_model=TimesheetResponse)
async def update_timesheet(
    timesheet_id: UUID,
    payload: TimesheetUpdate,
    db=Depends(get_pg_session),
):
    updated = await update_timesheet_service(db, timesheet_id, payload)
    return updated


@timesheet_router.get(
    "/{timesheet_id}/entries", response_model=list[TimeEntryRawResponse]
)
async def get_timesheet_entries(timesheet_id: UUID, db=Depends(get_pg_session)):
    return await get_timesheet_entries_service(db, timesheet_id)


@timesheet_router.get("/extracted-data/all")
async def get_all_extracted_timesheets(db=Depends(get_pg_session)):
    """Get all extracted timesheets with full context (names, client, email details)."""
    return await get_extracted_timesheets_for_display(db)


@timesheet_router.get("/extracted-data/{timesheet_id}")
async def get_extracted_timesheet_data(timesheet_id: UUID, db=Depends(get_pg_session)):
    """Get a single extracted timesheet with full context for display."""
    data = await get_extracted_timesheet_by_id_for_display(db, timesheet_id)
    if not data:
        raise HTTPException(status_code=404, detail="Extracted timesheet not found")
    return data


@timesheet_router.post("/approval/{timesheet_id}/decide")
async def decide_timesheet_approval(
    timesheet_id: UUID,
    request: ApprovalDecisionRequest,
    db=Depends(get_pg_session),
):
    """
    Approve or reject a timesheet.
    Request body: {"decision": "APPROVED" or "REJECTED", "comment": "optional"}
    """
    result = await decide_timesheet_approval_service(
        db, timesheet_id, request.decision, request.comment
    )
    return result


@timesheet_router.get("/payroll/export")
async def get_payroll_ready_export(db=Depends(get_pg_session)):
    """
    Get all approved timesheets in payroll-ready format.
    Includes all time entries with calculated totals per employee.
    Ready for export to payroll systems.
    """
    return await get_payroll_ready_timesheets(db)
