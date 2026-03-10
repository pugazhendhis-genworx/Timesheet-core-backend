from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.rest.dependencies import get_pg_session
from src.core.services.approval_service import (
    approve_timesheet_service,
    get_all_approvals_service,
    get_approval_by_id_service,
)
from src.schemas.approval_schemas import ApprovalCreate, ApprovalResponse

approval_router = APIRouter(tags=["approval"], prefix="/approval")


@approval_router.get("/get-approvals", response_model=list[ApprovalResponse])
async def get_approvals(db=Depends(get_pg_session)):
    return await get_all_approvals_service(db)


@approval_router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: UUID, db=Depends(get_pg_session)):
    return await get_approval_by_id_service(db, approval_id)


@approval_router.post("/{timesheet_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    timesheet_id: UUID,
    approval_data: ApprovalCreate,
    db=Depends(get_pg_session),
):
    """
    Approve or reject a timesheet that is READY_FOR_APPROVAL.
    approval_data.decision must be 'APPROVED' or 'REJECTED'.
    """
    return await approve_timesheet_service(db, timesheet_id, approval_data)
