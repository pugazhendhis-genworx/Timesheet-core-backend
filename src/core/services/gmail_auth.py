import logging
import os
import time

from google.auth.exceptions import TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from src.config.settings import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

TOKEN_FILE = settings.TOKEN_FILE

MAX_REFRESH_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds


def authenticate():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        _refresh_with_retry(creds)

    if not creds or not creds.valid:
        raise RuntimeError(
            "Gmail token missing or invalid. Generate token.json locally and deploy it."
        )

    return creds


def _refresh_with_retry(creds: Credentials):
    """Refresh OAuth credentials with retry logic for transient SSL/network errors."""
    for attempt in range(1, MAX_REFRESH_RETRIES + 1):
        try:
            creds.refresh(Request())
            return
        except TransportError as e:
            if attempt == MAX_REFRESH_RETRIES:
                logger.error("Token refresh failed after %d attempts: %s", attempt, e)
                raise
            wait = RETRY_BACKOFF_BASE**attempt
            logger.warning(
                "Token refresh attempt %d/%d failed (%s), retrying in %ds...",
                attempt,
                MAX_REFRESH_RETRIES,
                e,
                wait,
            )
            time.sleep(wait)
