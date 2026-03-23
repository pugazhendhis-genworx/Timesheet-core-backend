from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.rest.dependencies import DBSession, require_roles
from src.core.services.client_rule_services import (
    create_client_rule_service,
    get_client_rules_service,
    update_client_rule_service,
)
from src.schemas.client_rule_schemas import (
    ClientRuleCreate,
    ClientRuleResponse,
    ClientRuleUpdate,
)

rule_router = APIRouter(
    tags=["rule"],
    prefix="/rule",
    dependencies=[Depends(require_roles(["operation_executive", "auditor"]))],
)


@rule_router.post("/create_rule", response_model=ClientRuleResponse)
async def create_client_rule(client_rule: ClientRuleCreate, db: DBSession):
    result = await create_client_rule_service(db, client_rule)
    return result


@rule_router.get("/client/{client_id}", response_model=list[ClientRuleResponse])
async def get_rules_by_client(client_id: UUID, db: DBSession):
    result = await get_client_rules_service(db, client_id)
    return result


@rule_router.get(
    "/client/{client_id}/status/{is_active}", response_model=list[ClientRuleResponse]
)
async def get_rules_by_client_and_status(
    client_id: UUID, is_active: bool, db: DBSession
):
    result = await get_client_rules_service(db, client_id, is_active)
    return result


@rule_router.put("/{rule_id}", response_model=ClientRuleResponse)
async def update_client_rule(
    rule_id: UUID, update_data: ClientRuleUpdate, db: DBSession
):
    result = await update_client_rule_service(db, rule_id, update_data)
    return result
