from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.api.rest.dependencies import DBSession, require_roles
from src.core.services.payroll_payslip_service import (
    get_timesheet_payroll_payslips_service,
)
from src.schemas.payroll_payslip_schemas import PayrollTimesheetPayslipResponse

payroll_payslip_router = APIRouter(
    tags=["payroll_payslip"],
    prefix="/payroll_ready",
    dependencies=[Depends(require_roles(["operation_executive", "auditor"]))],
)


@payroll_payslip_router.get(
    "/timesheet/{timesheet_id}/payslips",
    response_model=PayrollTimesheetPayslipResponse,
)
async def get_timesheet_payroll_payslips(timesheet_id: UUID, db: DBSession):
    payload = await get_timesheet_payroll_payslips_service(db, timesheet_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Payroll entry not found")
    return payload
