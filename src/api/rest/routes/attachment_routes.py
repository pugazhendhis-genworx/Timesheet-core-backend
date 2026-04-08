import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from src.config.settings import settings
from src.core.services.gcs_service import generate_signed_url

logger = logging.getLogger(__name__)

attachment_router = APIRouter(tags=["attachments"], prefix="/attachments")


@attachment_router.get("/{filename}")
async def get_attachment(filename: str):
    """
    Return a redirect to a time-limited GCS signed URL for the
    requested attachment file, or serve it from local fallback.
    """
    try:
        gcs_url = (
            f"gs://{settings.GCS_BUCKET_NAME}/{settings.GCS_BUCKET_PREFIX}/{filename}"
        )
        signed_url = generate_signed_url(gcs_url)
        return RedirectResponse(url=signed_url, status_code=307)

    except Exception as e:
        logger.warning(
            "Failed to generate signed URL for %s: %s. Trying local fallback.",
            filename,
            e,
        )
        local_path = os.path.join("attachments", filename)
        if os.path.exists(local_path):
            return FileResponse(local_path)
        else:
            logger.error("File not found locally either: %s", local_path)
            raise HTTPException(
                status_code=500,
                detail=f"Could not generate download URL or find local file: {e}",
            ) from e
