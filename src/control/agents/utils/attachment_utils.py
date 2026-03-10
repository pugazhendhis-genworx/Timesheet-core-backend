import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def detect_attachment_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()

    if suffix == ".pdf":
        return "pdf"

    if suffix in [".xlsx", ".xls"]:
        return "excel"

    if suffix in [".jpg", ".jpeg", ".png"]:
        return "image"

    return "unknown"


def parse_excel_timesheet(file_path: str) -> str:
    try:
        df = pd.read_excel(file_path)
        return df.to_string()
    except Exception as e:
        logger.exception("Excel parsing failed")
        raise RuntimeError(f"Excel parse error: {str(e)}") from e
