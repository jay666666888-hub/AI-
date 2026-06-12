"""
审计日志 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models.audit import AuditLog
from app.models.models import User
from app.api.deps import get_current_user
from app.core.logging import logger

router = APIRouter()

class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogCreate(BaseModel):
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[dict] = None

async def log_action(
    db: AsyncSession,
    user_id: UUID,
    action: str,
    entity_type: str = None,
    entity_id: UUID = None,
    details: dict = None,
    ip_address: str = None
):
    """记录审计日志"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address
    )
    db.add(audit_log)
    await db.commit()

    # 记录到结构化日志
    logger.info(
        f"audit: {action}",
        extra={
            "user_id": str(user_id),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id
        }
    )

@router.post("/audit", response_model=AuditLogResponse)
async def create_audit_log(
    log_data: AuditLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建审计日志"""
    await log_action(
        db=db,
        user_id=current_user.id,
        action=log_data.action,
        entity_type=log_data.entity_type,
        entity_id=log_data.entity_id,
        details=log_data.details
    )
    return {"status": "ok"}

@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取审计日志列表"""
    query = select(AuditLog).where(AuditLog.user_id == current_user.id)

    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)

    query = query.order_by(desc(AuditLog.created_at)).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        AuditLogResponse(
            id=str(log.id),
            user_id=str(log.user_id),
            action=log.action,
            entity_type=log.entity_type,
            entity_id=str(log.entity_id) if log.entity_id else None,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at
        )
        for log in logs
    ]