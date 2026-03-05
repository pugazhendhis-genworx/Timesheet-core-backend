from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.rest.routes.client_routes import client_router
from src.api.rest.routes.email_routes import email_router
from src.api.rest.routes.email_whitelist_routes import whitelist_router
from src.api.rest.routes.health_routes import health_router
from src.data.clients.database import Base, engine
from src.data.models.postgres.client_model import Client  # noqa
from src.data.models.postgres.email_model import (  # noqa
    EmailAttachment,
    EmailMessage,
    EmailThread,
    EmailWhitelist,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(email_router)
    app.include_router(client_router)
    app.include_router(whitelist_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173","http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
