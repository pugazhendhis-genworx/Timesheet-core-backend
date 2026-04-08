from typing import Any


def _extract_sender(email_data: dict[str, Any]) -> str:
    """Extract clean sender email from email metadata."""
    sender = str(email_data["from"])
    if "<" in sender:
        sender = sender.split("<")[1].replace(">", "").strip()
    return sender


def _resolve_body(email_data: dict[str, Any]) -> str:
    """Resolve email body with fallback: plain → html → snippet."""
    return (
        str(email_data["body_plain"])
        or str(email_data["body_html"])
        or str(email_data.get("snippet", ""))
    )
