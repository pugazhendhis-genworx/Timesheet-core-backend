from sqlalchemy import select

from src.data.models.postgres.client_model import Client


async def get_client_by_client_id(client_id, db):
    """Async — get client by client_id."""
    result = await db.execute(select(Client).where(Client.client_id == client_id))
    return result.scalar_one()
async def get_all_clients(db):
    result = await db.execute(select(Client))
    clients=result.scalars().all()
    return clients


def get_client_by_client_id_sync(client_id, db):
    """Sync — get client by client_id."""
    result = db.execute(select(Client).where(Client.client_id == client_id))
    return result.scalar_one()
