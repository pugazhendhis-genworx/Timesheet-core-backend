from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

attachment_router = APIRouter(tags=["attachments"], prefix="/attachments")

# attachments dir is at: Timesheet-core-backend/attachments
BASE_DIR = Path(__file__).resolve().parents[4]  # go up to Timesheet-core-backend
ATTACHMENTS_DIR = BASE_DIR / "attachments"


@attachment_router.get("/{filename}")
async def get_attachment(filename: str):
    file_path = ATTACHMENTS_DIR / filename
    # Ensure file exists and is within ATTACHMENTS_DIR (prevent directory traversal)
    try:
        file_path = file_path.resolve()
        if not file_path.is_relative_to(ATTACHMENTS_DIR.resolve()):
            return FileResponse(str(file_path), status_code=401)
    except ValueError:
        return FileResponse(str(file_path), status_code=401)

    if not file_path.is_file():
        return FileResponse(str(file_path), status_code=404)
    return FileResponse(str(file_path))
