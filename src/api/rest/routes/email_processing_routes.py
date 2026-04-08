from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.api.rest.dependencies import DBSession, require_roles
from src.constants.error_responses import COMMON_ERROR_RESPONSES
from src.core.services.email_processing_service import (
    process_unprocessed_emails,
    reprocess_failed_emails,
)

email_process_router = APIRouter(
    tags=["email-processing"],
    prefix="/email-processing",
    dependencies=[Depends(require_roles(["operation_executive", "auditor"]))],
)


@email_process_router.post("/process-all", responses=COMMON_ERROR_RESPONSES)
async def process_all_emails(db: DBSession) -> dict[str, Any]:
    try:
        result = await process_unprocessed_emails(db)
        return {
            "status": "success",
            "processed_count": result["processed_count"],
            "failed_count": result["failed_count"],
            "processed": result["processed"],
            "failed": result["failed"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@email_process_router.post("/reprocess-failed", responses=COMMON_ERROR_RESPONSES)
async def reprocess_failed_emails_endpoint(db: DBSession) -> dict[str, Any]:
    try:
        result = await reprocess_failed_emails(db)
        return {
            "status": "success",
            "message": result.get("message", "Reprocessing complete"),
            "processed_count": result["processed_count"],
            "failed_count": result["failed_count"],
            "processed": result["processed"],
            "failed": result["failed"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
