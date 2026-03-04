from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.client_model import Client
from src.schemas.client_schemas import ClientCreate


async def get_client_by_client_id(client_id, db):
    """Async — get client by client_id."""
    result = await db.execute(select(Client).where(Client.client_id == client_id))
    return result.scalar_one()


async def get_client_by_id(db: AsyncSession, client_id):
    result = await db.execute(select(Client).where(Client.client_id == client_id))
    return result.scalar_one_or_none()


async def get_all_clients(db):
    result = await db.execute(select(Client))
    clients = result.scalars().all()
    return clients


async def create_client(db: AsyncSession, client_data: ClientCreate):
    new_client = Client(
        client_name=client_data.client_name,
        client_code=client_data.client_code,
        client_email=client_data.client_email,
        created_by=client_data.created_by,
    )

    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)

    return new_client


def get_client_by_client_id_sync(client_id, db):
    """Sync — get client by client_id."""
    result = db.execute(select(Client).where(Client.client_id == client_id))
    return result.scalar_one()
