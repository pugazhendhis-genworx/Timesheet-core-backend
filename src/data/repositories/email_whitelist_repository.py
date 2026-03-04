from sqlalchemy import select

from src.data.models.postgres.email_model import EmailWhitelist
from src.schemas.email_schemas import EmailWhitelistCreate


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


async def get_whitelisted_email_by_client_id(client_id, db):
    result = await db.execute(
        select(EmailWhitelist).where(EmailWhitelist.client_id == client_id)
    )
    whitelisted_emails = result.scalar_one_or_more()
    return whitelisted_emails


async def get_all_whitelisted_emails(db):
    result = await db.execute(select(EmailWhitelist))
    return result.scalars().all()


async def create_whitelist_email(whitelist_data: EmailWhitelistCreate, db):
    new_entry = EmailWhitelist(
        client_id=whitelist_data.client_id,
        allowed_email=whitelist_data.allowed_email,
    )

    db.add(new_entry)
    await db.commit()
    await db.refresh(new_entry)

    return new_entry


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
