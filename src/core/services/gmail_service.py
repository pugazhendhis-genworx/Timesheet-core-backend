import base64
import os

from googleapiclient.discovery import build

from .gmail_auth import authenticate

HISTORY_FILE = "history.txt"


def get_service():
    creds = authenticate()
    return build("gmail", "v1", credentials=creds)


def get_current_history_id(service):
    profile = service.users().getProfile(userId="me").execute()
    return profile["historyId"]


def save_history_id(history_id):
    with open(HISTORY_FILE, "w") as f:
        f.write(str(history_id))


def load_history_id():
    if not os.path.exists(HISTORY_FILE):
        return None
    with open(HISTORY_FILE) as f:
        return f.read().strip()


def get_header(headers, name):
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return None


def extract_body(payload):

    body_plain = None
    body_html = None

    def walk_parts(parts):
        nonlocal body_plain, body_html

        for part in parts:
            mime_type = part.get("mimeType", "")

            # If nested parts exist, go deeper first
            if "parts" in part:
                walk_parts(part["parts"])
                continue

            if mime_type == "text/plain" and body_plain is None:
                data = part.get("body", {}).get("data")
                if data:
                    body_plain = base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="ignore"
                    )

            if mime_type == "text/html" and body_html is None:
                data = part.get("body", {}).get("data")
                if data:
                    body_html = base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="ignore"
                    )

    if "parts" in payload:
        walk_parts(payload["parts"])
    else:
        # Single-part message (no multipart structure)
        mime_type = payload.get("mimeType", "")
        data = payload.get("body", {}).get("data")
        if data:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            if mime_type == "text/html":
                body_html = decoded
            else:
                body_plain = decoded

    # Fallback: use snippet if no body was extracted
    if not body_plain and not body_html:
        body_plain = None  # will be handled by ingestion

    return body_plain, body_html


def extract_email_metadata(message):
    headers = message["payload"].get("headers", [])

    subject = get_header(headers, "Subject")
    sender = get_header(headers, "From")
    to = get_header(headers, "To")
    cc = get_header(headers, "Cc")
    date = get_header(headers, "Date")

    body_plain, body_html = extract_body(message["payload"])

    attachments = []
    for part in message["payload"].get("parts", []):
        if part.get("filename"):
            attachments.append(
                {"filename": part["filename"], "mimeType": part.get("mimeType")}
            )

    email_data = {
        "message_id": message.get("id"),
        "thread_id": message.get("threadId"),
        "label_ids": message.get("labelIds"),
        "snippet": message.get("snippet"),
        "subject": subject,
        "from": sender,
        "to": to,
        "cc": cc,
        "date": date,
        "body_plain": body_plain,
        "body_html": body_html,
        "attachments": attachments,
    }

    return email_data


def get_full_thread(thread_id):
    service = get_service()

    thread = service.users().threads().get(userId="me", id=thread_id).execute()

    return thread


def fetch_new_emails():
    service = get_service()

    last_history = load_history_id()

    if not last_history:
        current_history = get_current_history_id(service)
        save_history_id(current_history)
        print(" Initialized historyId.")
        return []
    try:
        response = (
            service.users()
            .history()
            .list(
                userId="me", startHistoryId=last_history, historyTypes=["messageAdded"]
            )
            .execute()
        )
    except Exception as e:
        print("History fetch error:", e)
        return []

    new_history_id = response.get("historyId")

    messages = []

    if "history" in response:
        for record in response["history"]:
            if "messagesAdded" in record:
                for msg in record["messagesAdded"]:
                    messages.append(msg["message"])

    if new_history_id:
        save_history_id(new_history_id)

    return messages


def get_message_detail(message_id):
    service = get_service()

    message = service.users().messages().get(userId="me", id=message_id).execute()

    return message


def save_attachments(message) -> list[dict]:
    """
    Download attachment data from Gmail and upload each file to GCS.

    Returns a list of ``{filename, gcs_url, mime_type}`` dicts so the
    caller can persist the GCS URLs in the database.
    """
    from src.core.services.gcs_service import upload_to_gcs

    service = get_service()
    uploaded: list[dict] = []

    for part in message["payload"].get("parts", []):
        if part.get("filename"):
            attachment_id = part["body"]["attachmentId"]

            attachment = (
                service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message["id"], id=attachment_id)
                .execute()
            )

            data = base64.urlsafe_b64decode(attachment["data"])
            mime_type = part.get("mimeType", "application/octet-stream")

            gcs_url = upload_to_gcs(data, part["filename"], mime_type)

            uploaded.append(
                {
                    "filename": part["filename"],
                    "gcs_url": gcs_url,
                    "mime_type": mime_type,
                }
            )

    return uploaded


def mark_as_read(message_id):
    service = get_service()

    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def mark_as_unread(message_id):
    service = get_service()

    service.users().messages().modify(
        userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]}
    ).execute()
