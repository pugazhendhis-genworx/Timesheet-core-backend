from typing import Annotated

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.data.clients.database import async_session_maker


async def get_pg_session():
    async with async_session_maker() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_pg_session)]


AUTH_SERVICE_URL = settings.AUTHBACKEND_URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{AUTH_SERVICE_URL}/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/auth/validate",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_data = response.json()
            return user_data
        except httpx.RequestError as err:
            raise HTTPException(
                status_code=500,
                detail="Authentication service unavailable",
            ) from err


def require_roles(allowed_roles: list[str]):
    def checker(current_user=Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required role. Allowed roles: {allowed_roles}",
            )
        return current_user

    return checker
