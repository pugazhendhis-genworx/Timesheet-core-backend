import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from src.config.settings import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

TOKEN_FILE = settings.TOKEN_FILE


def authenticate():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        raise RuntimeError(
            "Gmail token missing or invalid. Generate token.json locally and deploy it."
        )

    return creds
