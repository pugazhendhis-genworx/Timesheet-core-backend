from sqlalchemy import select

from src.data.models.postgres.email_model import (
    EmailAttachment,
    EmailMessage,
    EmailThread,
)

# ── Thread ──────────────────────────────────────────────


async def get_email_thread_by_gmail_id(gmail_thread_id: str, db):
    """Async — get thread by Gmail thread ID."""
    result = await db.execute(
        select(EmailThread).where(EmailThread.gmail_thread_id == gmail_thread_id)
    )
    return result.scalar_one_or_none()


def get_email_thread_by_gmail_id_sync(gmail_thread_id: str, db):
    """Sync — get thread by Gmail thread ID."""
    result = db.execute(
        select(EmailThread).where(EmailThread.gmail_thread_id == gmail_thread_id)
    )
    return result.scalar_one_or_none()


async def create_email_thread(thread: EmailThread, db):
    """Async — insert a new thread and flush."""
    db.add(thread)
    await db.flush()
    return thread


def create_email_thread_sync(thread: EmailThread, db):
    """Sync — insert a new thread and flush."""
    db.add(thread)
    db.flush()
    return thread


# ── Message ─────────────────────────────────────────────


async def get_email_message_by_message_id(message_id: str, db):
    """Async — check if message already exists."""
    result = await db.execute(
        select(EmailMessage).where(EmailMessage.message_id == message_id)
    )
    return result.scalar_one_or_none()


async def get_email_by_id(email_id, db):
    return await db.get(EmailMessage, email_id)


def get_email_message_by_message_id_sync(message_id: str, db):
    """Sync — check if message already exists."""
    result = db.execute(
        select(EmailMessage).where(EmailMessage.message_id == message_id)
    )
    return result.scalar_one_or_none()


async def update_status(email, status, db):

    email.processed_status = status

    await db.flush()


async def update_classification(email, classification, db):

    email.classification = classification

    await db.flush()


async def get_first_message_by_thread_id(thread_id, db):
    """Async — check if thread already has messages (to detect reply)."""
    result = await db.execute(
        select(EmailMessage).where(EmailMessage.thread_id == thread_id)
    )
    return result.scalars().first()


async def get_email_message_ingested(db):
    result = await db.execute(
        select(EmailMessage).where(EmailMessage.processed_status == "INGESTED")
    )
    return result.scalars().all()


def get_first_message_by_thread_id_sync(thread_id, db):
    """Sync — check if thread already has messages (to detect reply)."""
    result = db.execute(select(EmailMessage).where(EmailMessage.thread_id == thread_id))
    return result.scalars().first()


async def create_email_message(message: EmailMessage, db):
    """Async — insert a new message and flush."""
    db.add(message)
    await db.flush()
    return message


def create_email_message_sync(message: EmailMessage, db):
    """Sync — insert a new message and flush."""
    db.add(message)
    db.flush()
    return message


# ── Attachment ──────────────────────────────────────────


async def create_email_attachment(attachment: EmailAttachment, db):
    """Async — insert a new attachment."""
    db.add(attachment)


async def get_attachments(email_id, db):

    result = await db.execute(
        select(EmailAttachment).where(EmailAttachment.email_message_id == email_id)
    )

    return result.scalars().all()


def create_email_attachment_sync(attachment: EmailAttachment, db):
    """Sync — insert a new attachment."""
    db.add(attachment)


# ── Commit ──────────────────────────────────────────────


async def commit_session(db):
    """Async — commit the session."""
    await db.commit()


def commit_session_sync(db):
    """Sync — commit the session."""
    db.commit()
