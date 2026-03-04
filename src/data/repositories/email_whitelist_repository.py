from sqlalchemy import select

from src.data.models.postgres.email_model import EmailWhitelist


async def get_whitelisted_client(sender_email: str, db):
    """
    Returns client_id if sender is whitelisted (async — for FastAPI).
    """
    result = await db.execute(
        select(EmailWhitelist).where(
            EmailWhitelist.allowed_email == sender_email,
            EmailWhitelist.is_active,
        )
    )

    whitelist_entry = result.scalar_one_or_none()

    if whitelist_entry:
        return whitelist_entry.client_id

    return None


def get_whitelisted_client_sync(sender_email: str, db):
    """
    Returns client_id if sender is whitelisted (sync — for Celery).
    """
    result = db.execute(
        select(EmailWhitelist).where(
            EmailWhitelist.allowed_email == sender_email,
            EmailWhitelist.is_active,
        )
    )

    whitelist_entry = result.scalar_one_or_none()

    if whitelist_entry:
        return whitelist_entry.client_id

    return None
