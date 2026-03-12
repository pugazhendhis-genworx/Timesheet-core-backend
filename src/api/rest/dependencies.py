from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.clients.database import async_session_maker


async def get_pg_session():
    async with async_session_maker() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_pg_session)]
