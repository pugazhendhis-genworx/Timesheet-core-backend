import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from src.config.settings import settings
from src.core.services.gcs_service import generate_signed_url

logger = logging.getLogger(__name__)

attachment_router = APIRouter(tags=["attachments"], prefix="/attachments")


@attachment_router.get("/{filename}")
async def get_attachment(filename: str):
    """
    Return a redirect to a time-limited GCS signed URL for the
    requested attachment file.
    """
    try:
        gcs_url = (
            f"gs://{settings.GCS_BUCKET_NAME}"
            f"/{settings.GCS_BUCKET_PREFIX}/{filename}"
        )
        signed_url = generate_signed_url(gcs_url)
        return RedirectResponse(url=signed_url, status_code=307)

    except Exception as e:
        logger.exception("Failed to generate signed URL for %s", filename)
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate download URL: {e}",
        ) from e
