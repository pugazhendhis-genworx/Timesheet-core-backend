import io
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# ── MIME type → category mapping ────────────────────────

_PDF_MIMES = {"application/pdf"}
_EXCEL_MIMES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}
_IMAGE_MIME_PREFIX = "image/"


def detect_attachment_type(mime_type: str) -> str:
    """
    Detect the broad file category from a MIME type string.

    Returns one of: ``"pdf"``, ``"excel"``, ``"image"``, ``"unknown"``.
    """
    if not mime_type:
        return "unknown"

    mime_lower = mime_type.lower().strip()

    if mime_lower in _PDF_MIMES:
        return "pdf"

    if mime_lower in _EXCEL_MIMES:
        return "excel"

    if mime_lower.startswith(_IMAGE_MIME_PREFIX):
        return "image"

    return "unknown"


def parse_excel_timesheet(file_data: bytes) -> str:
    """
    Parse an Excel file from raw bytes and return the contents as
    a string table suitable for LLM processing.
    """
    try:
        df = pd.read_excel(io.BytesIO(file_data))
        return df.to_string()
    except Exception as e:
        logger.exception("Excel parsing failed")
        raise RuntimeError(f"Excel parse error: {str(e)}") from e
