import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.review_model import Approval
from src.data.repositories.approval_repository import (
    create_approval,
    get_all_approvals,
    get_approval_by_id,
)
from src.data.repositories.timesheet_repository import get_timesheet_by_id
from src.schemas.approval_schemas import ApprovalCreate

logger = logging.getLogger(__name__)


async def get_all_approvals_service(db: AsyncSession):
    return await get_all_approvals(db)


async def get_approval_by_id_service(db: AsyncSession, approval_id: UUID):
    approval = await get_approval_by_id(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


async def approve_timesheet_service(
    db: AsyncSession,
    timesheet_id: UUID,
    approval_data: ApprovalCreate,
):
    """
    Approve or reject a timesheet that is READY_FOR_APPROVAL.
    Creates an Approval record and updates the timesheet status.
    """
    timesheet = await get_timesheet_by_id(db, timesheet_id)
    if not timesheet:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    if timesheet.status != "READY_FOR_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=(
                "Timesheet is not ready for approval. "
                f"Current status: {timesheet.status}"
            ),
        )

    if approval_data.decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=400,
            detail="Decision must be APPROVED or REJECTED",
        )

    # Create approval record
    approval = Approval(
        timesheet_id=timesheet_id,
        approved_by=approval_data.approved_by,
        decision=approval_data.decision,
        decision_at=datetime.now(UTC),
    )
    approval = await create_approval(db, approval)

    # Update timesheet status
    timesheet.status = approval_data.decision  # APPROVED or REJECTED
    await db.flush()
    await db.commit()

    logger.info(
        "Timesheet %s %s by %s",
        timesheet_id,
        approval_data.decision,
        approval_data.approved_by,
    )
    return approval
