from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.client_rule_repository import (
    create_client_rule_repo,
    get_client_rule_by_id_repo,
    get_client_rules_by_client_id_repo,
    update_client_rule_repo,
)
from src.schemas.client_rule_schemas import ClientRuleCreate, ClientRuleUpdate


async def create_client_rule_service(db: AsyncSession, rule_data: ClientRuleCreate):
    try:
        result = await create_client_rule_repo(db, rule_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_client_rules_service(
    db: AsyncSession, client_id: UUID, is_active: bool | None = None
):
    try:
        rules = await get_client_rules_by_client_id_repo(db, client_id, is_active)
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_client_rule_by_id_service(db: AsyncSession, rule_id: UUID):
    try:
        rule = await get_client_rule_by_id_repo(db, rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Client rule not found")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_client_rule_service(
    db: AsyncSession, rule_id: UUID, update_data: ClientRuleUpdate
):
    try:
        rule = await update_client_rule_repo(db, rule_id, update_data)
        if not rule:
            raise HTTPException(status_code=404, detail="Client rule not found")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
