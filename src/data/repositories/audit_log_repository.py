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


async def create_audit_log(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id,
    user_id=None,
    metadata_json=None,
) -> AuditLog:
    log = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        metadata_json=metadata_json or {},
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log

