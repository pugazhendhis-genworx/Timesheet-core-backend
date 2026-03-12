def _extract_sender(email_data: dict) -> str:
    """Extract clean sender email from email metadata."""
    sender = email_data["from"]
    if "<" in sender:
        sender = sender.split("<")[1].replace(">", "").strip()
    return sender


def _resolve_body(email_data: dict) -> str:
    """Resolve email body with fallback: plain → html → snippet."""
    return (
        email_data["body_plain"]
        or email_data["body_html"]
        or email_data.get("snippet", "")
    )
