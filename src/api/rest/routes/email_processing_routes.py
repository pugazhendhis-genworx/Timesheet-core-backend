from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_pg_session
from src.core.services.email_processing_service import (
    process_unprocessed_emails,
    reprocess_failed_emails,
)

email_process_router = APIRouter(tags=["email-processing"], prefix="/email-processing")


@email_process_router.post("/process-all")
async def process_all_emails(db: AsyncSession = Depends(get_pg_session)):
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


@email_process_router.post("/reprocess-failed")
async def reprocess_failed_emails_endpoint(db: AsyncSession = Depends(get_pg_session)):
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
