from fastapi import APIRouter

from src.api.rest.dependencies import DBSession
from src.data.repositories.audit_log_repository import get_audit_logs
from src.schemas.audit_log_schemas import AuditLogResponse

audit_log_router = APIRouter(tags=["audit-log"], prefix="/audit-log")


@audit_log_router.get("/", response_model=list[AuditLogResponse])
async def list_audit_logs(
    db: DBSession,
    resource_type: str | None = None,
):
    """Return audit logs, optionally filtered by resource_type."""
    return await get_audit_logs(db, resource_type=resource_type)
