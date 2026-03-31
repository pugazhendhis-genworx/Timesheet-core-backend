from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.client_rule_model import ClientRule
from src.schemas.client_rule_schemas import ClientRuleCreate, ClientRuleUpdate


async def create_client_rule_repo(db: AsyncSession, rule_data: ClientRuleCreate):
    new_rule = ClientRule(
        client_id=rule_data.client_id,
        rule_type=rule_data.rule_type,
        rule_config=rule_data.rule_config.model_dump(),
        is_active=True,
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule


async def get_client_rule_by_id_repo(db: AsyncSession, rule_id: UUID):
    result = await db.execute(select(ClientRule).where(ClientRule.rule_id == rule_id))
    return result.scalar_one_or_none()


async def get_client_rules_by_client_id_repo(
    db: AsyncSession, client_id: UUID, is_active: bool | None = None
):
    query = select(ClientRule).where(ClientRule.client_id == client_id)
    if is_active is not None:
        query = query.where(ClientRule.is_active == is_active)

    result = await db.execute(query)
    return result.scalars().all()


async def update_client_rule_repo(
    db: AsyncSession, rule_id: UUID, update_data: ClientRuleUpdate
):
    rule = await get_client_rule_by_id_repo(db, rule_id)
    if not rule:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)
    if "is_active" in update_dict:
        rule.is_active = update_dict["is_active"]
    if "rule_config" in update_dict:
        rule.rule_config = update_dict["rule_config"]

    await db.commit()
    await db.refresh(rule)
    return rule
