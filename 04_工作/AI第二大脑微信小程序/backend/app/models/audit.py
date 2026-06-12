"""
审计日志模型
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import uuid
from datetime import datetime

class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)  # create_task, complete_task, delete_task, login
    entity_type = Column(String(32), nullable=True)  # task, project, note, habit
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)  # 额外信息
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)