from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_pg_session
from src.data.repositories.audit_log_repository import get_audit_logs
from src.schemas.audit_log_schemas import AuditLogResponse

audit_log_router = APIRouter(tags=["audit-log"], prefix="/audit-log")


@audit_log_router.get("/", response_model=list[AuditLogResponse])
async def list_audit_logs(
    resource_type: str | None = None,
    db: AsyncSession = Depends(get_pg_session),
):
    """Return audit logs, optionally filtered by resource_type."""
    return await get_audit_logs(db, resource_type=resource_type)
