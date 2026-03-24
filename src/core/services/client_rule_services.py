from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.client_rule_repository import (
    create_client_rule_repo,
    get_client_rule_by_id_repo,
    get_client_rules_by_client_id_repo,
    update_client_rule_repo,
)
from src.observability.logging.logging import get_logger
from src.schemas.client_rule_schemas import ClientRuleCreate, ClientRuleUpdate

logger = get_logger(__name__)


async def create_client_rule_service(db: AsyncSession, rule_data: ClientRuleCreate):
    logger.info("Creating client rule")
    try:
        result = await create_client_rule_repo(db, rule_data)

        logger.info(
            f"Client rule created with id={result.rule_id},"
            "client_id={result.client_id}"
        )
        return result

    except Exception as e:
        logger.error("Error creating client rule", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_client_rules_service(
    db: AsyncSession, client_id: UUID, is_active: bool | None = None
):
    logger.info(
        f"Fetching client rules for client_id={client_id}, is_active={is_active}"
    )
    try:
        rules = await get_client_rules_by_client_id_repo(db, client_id, is_active)
        logger.info(
            f"Fetched {len(rules)} rules for client_id={client_id},"
            " is_active={is_active}"
        )
        return rules
    except Exception as e:
        logger.error(
            f"Error fetching client rules for client_id={client_id}",
            exc_info=True,
        )

        raise HTTPException(status_code=500, detail=str(e)) from e


async def get_client_rule_by_id_service(db: AsyncSession, rule_id: UUID):
    logger.info(f"Fetching client rule id={rule_id}")
    try:
        rule = await get_client_rule_by_id_repo(db, rule_id)
        if not rule:
            logger.warning(f"Client rule not found: id={rule_id}")
            raise HTTPException(status_code=404, detail="Client rule not found")
        logger.info(f"Client rule found: id={rule_id}")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client rule id={rule_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


async def update_client_rule_service(
    db: AsyncSession, rule_id: UUID, update_data: ClientRuleUpdate
):
    try:
        logger.info(f"Updating client rule id={rule_id}")
        rule = await update_client_rule_repo(db, rule_id, update_data)
        if not rule:
            raise HTTPException(status_code=404, detail="Client rule not found")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client rule id={rule_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
