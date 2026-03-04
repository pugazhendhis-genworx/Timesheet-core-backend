import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def authenticate():
    creds = None

    if os.path.exists("token.json"):
        try:
            with open("token.json", "rb") as token:
                creds = pickle.load(token)
        except Exception:
            os.remove("token.json")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)

        with open("token.json", "wb") as token:
            pickle.dump(creds, token)

    return creds
