from uuid import UUID

from fastapi import APIRouter, HTTPException

from src.api.rest.dependencies import DBSession
from src.core.services.payroll_service import (
    get_all_payroll_ready_service,
    get_payroll_ready_by_id_service,
    get_payroll_timesheet_summary_service,
)
from src.schemas.payroll_schemas import (
    PayrollReadyEntryResponse,
    PayrollReadyListEnvelope,
    PayrollReadySingleEnvelope,
    PayrollTimesheetSummaryResponse,
)
from src.schemas.rule_violation_schemas import RuleViolationItemResponse

payroll_router = APIRouter(tags=["payroll_ready"], prefix="/payroll_ready")


@payroll_router.get("/", response_model=PayrollReadyListEnvelope)
async def get_all_payroll_ready(db: DBSession):
    entries = await get_all_payroll_ready_service(db)
    return PayrollReadyListEnvelope(
        data=[PayrollReadyEntryResponse.model_validate(e) for e in entries]
    )


@payroll_router.get(
    "/timesheet/{timesheet_id}",
    response_model=PayrollTimesheetSummaryResponse,
)
async def get_payroll_ready_by_timesheet_id(timesheet_id: UUID, db: DBSession):
    """Payroll-ready rows for a timesheet plus any recorded violations."""
    summary = await get_payroll_timesheet_summary_service(db, timesheet_id)
    return PayrollTimesheetSummaryResponse(
        timesheet_id=summary["timesheet_id"],
        payroll_entries=[
            PayrollReadyEntryResponse.model_validate(e)
            for e in summary["payroll_entries"]
        ],
        violations=[
            RuleViolationItemResponse.model_validate(v) for v in summary["violations"]
        ],
    )


@payroll_router.get(
    "/{payroll_entry_id}",
    response_model=PayrollReadySingleEnvelope,
)
async def get_payroll_ready_by_id(payroll_entry_id: UUID, db: DBSession):
    entry = await get_payroll_ready_by_id_service(db, payroll_entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Payroll entry not found")

    return PayrollReadySingleEnvelope(
        data=PayrollReadyEntryResponse.model_validate(entry)
    )
