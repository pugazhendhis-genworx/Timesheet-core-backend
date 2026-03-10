from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.paycode_model import Paycode
from src.schemas.paycode_schemas import PaycodeCreate


async def get_all_paycodes(db: AsyncSession):
    result = await db.execute(select(Paycode))
    return result.scalars().all()


async def get_paycode_by_code(db: AsyncSession, code: str):
    result = await db.execute(select(Paycode).where(Paycode.paycode == code))
    return result.scalar_one_or_none()


async def create_paycode(db: AsyncSession, paycode_data: PaycodeCreate):
    new_paycode = Paycode(
        paycode=paycode_data.paycode,
        paycode_name=paycode_data.paycode_name,
    )
    db.add(new_paycode)
    await db.commit()
    await db.refresh(new_paycode)
    return new_paycode
