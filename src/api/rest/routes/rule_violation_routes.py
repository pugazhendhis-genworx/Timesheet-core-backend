from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.api.rest.dependencies import DBSession, require_roles
from src.core.services.rule_violation_service import (
    get_flagged_timesheet_summary_service,
    get_flagged_timesheets_list_service,
)
from src.schemas.rule_violation_schemas import (
    FlaggedTimesheetListEnvelope,
    FlaggedTimesheetSummaryResponse,
    RuleViolationDetailResponse,
    RuleViolationItemResponse,
)
from src.schemas.timesheet_schemas import TimeEntryRawResponse, TimesheetResponse

rule_violation_router = APIRouter(
    tags=["rule_violations"],
    prefix="/rule_violations",
    dependencies=[Depends(require_roles(["operation_executive", "auditor"]))],
)


@rule_violation_router.get("/", response_model=FlaggedTimesheetListEnvelope)
async def get_all_flagged_timesheets(db: DBSession):
    """Returns a list of timesheets that possess
    rule violations with frontend metadata."""
    summaries = await get_flagged_timesheets_list_service(db)
    return FlaggedTimesheetListEnvelope(
        data=[FlaggedTimesheetSummaryResponse.model_validate(s) for s in summaries]
    )


@rule_violation_router.get(
    "/timesheet/{timesheet_id}",
    response_model=RuleViolationDetailResponse,
)
async def get_flagged_timesheet_details(timesheet_id: UUID, db: DBSession):
    """Detailed view showing Timesheet, raw time entries, and triggered violations."""
    summary = await get_flagged_timesheet_summary_service(db, timesheet_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    return RuleViolationDetailResponse(
        status=summary["status"],
        timesheet=TimesheetResponse.model_validate(summary["timesheet"]),
        time_entries_raw=[
            TimeEntryRawResponse.model_validate(e) for e in summary["time_entries_raw"]
        ],
        violations=[
            RuleViolationItemResponse.model_validate(v) for v in summary["violations"]
        ],
    )
