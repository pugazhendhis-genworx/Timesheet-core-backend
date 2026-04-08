from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.config.settings import settings

# --- Async engine (for FastAPI) ---
engine = create_async_engine(settings.POSTGRES_DB_URL, future=True)
async_session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_pg_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


# --- Sync engine (for Celery workers) ---
sync_engine = create_engine(settings.SYNC_POSTGRES_DB_URL, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(
    bind=sync_engine, class_=Session, expire_on_commit=False
)


def get_sync_session() -> Generator[Session, None, None]:
    """Context manager for sync DB session (use in Celery tasks)."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
