from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.audit_log_model import AuditLog


async def get_audit_logs(
    db: AsyncSession,
    resource_type: str | None = None,
) -> Iterable[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if resource_type:
        stmt = stmt.where(AuditLog.entity_type == resource_type)
    result = await db.execute(stmt)
    return result.scalars().all()

