"""
Database Models for AI第二大脑
All models inherit from app.database.Base
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, ForeignKey,
    JSON, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY as PG_ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wx_openid = Column(String(128), unique=True, nullable=True, index=True)
    wx_unionid = Column(String(128), unique=True, nullable=True, index=True)
    nickname = Column(String(64), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    phone = Column(String(32), nullable=True, index=True)
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    projects = relationship("Project", back_populates="user", lazy="selectin")
    tasks = relationship("Task", back_populates="user", lazy="selectin")
    notes = relationship("Note", back_populates="user", lazy="selectin")
    memories = relationship("Memory", back_populates="user", lazy="selectin")
    reminders = relationship("Reminder", back_populates="user", lazy="selectin")
    notifications = relationship("Notification", back_populates="user", lazy="selectin")


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    status = Column(String(32), default="active")  # active/archived/completed
    progress = Column(Integer, default=0)  # 0-100
    tags = Column(PG_ARRAY(String), default=[])
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", lazy="selectin")
    project_logs = relationship("ProjectLog", back_populates="project", lazy="selectin")


class Task(Base):
    """统一任务表 (Todo/Habit/Schedule/Waiting/Checklist)"""
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(32), nullable=False, index=True)  # todo/habit/schedule/waiting/checklist
    title = Column(String(256), nullable=False)
    detail = Column(Text, nullable=True)
    detail_source = Column(String(32), nullable=True)  # manual/ai_generated/ai_rewritten
    status = Column(String(32), default="active")  # active/completed/cancelled/archived
    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=3)  # 1-5
    tags = Column(PG_ARRAY(String), default=[])
    ai_metadata = Column(JSONB, nullable=True)

    # Habit-specific fields
    frequency = Column(String(32), nullable=True)  # daily/weekly/monthly
    execution_mode = Column(String(32), nullable=True)  # manual/auto
    scheduled_time = Column(String(16), nullable=True)  # HH:MM format
    target_type = Column(String(32), nullable=True)  # count/duration
    target_value = Column(Integer, nullable=True)

    # Schedule-specific fields
    location = Column(String(256), nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    # Waiting-specific fields
    wait_status = Column(String(32), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    habit_logs = relationship("HabitLog", back_populates="task", lazy="selectin")
    checklist_items = relationship("ChecklistItem", back_populates="task", lazy="selectin", foreign_keys="ChecklistItem.task_id")


class HabitLog(Base):
    """Habit执行记录表"""
    __tablename__ = "habit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    executed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="completed")  # completed/partial/missed/makeup
    ai_metadata = Column(JSONB, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="habit_logs")


class ChecklistItem(Base):
    """清单子项表"""
    __tablename__ = "checklist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("checklist_items.id", ondelete="CASCADE"), nullable=True, index=True)
    content = Column(String(512), nullable=False)
    is_done = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="checklist_items", foreign_keys=[task_id])
    parent = relationship("ChecklistItem", remote_side=[id], foreign_keys=[parent_id])


class Note(Base):
    """快速记录表"""
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    status = Column(String(32), default="inbox")  # inbox/processed/archived
    tags = Column(PG_ARRAY(String), default=[])
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notes")


class Memory(Base):
    """长期记忆表"""
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=True)
    tags = Column(PG_ARRAY(String), default=[])
    memory_type = Column(String(32), nullable=True)  # personal/family/project/important
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="memories")


class Reminder(Base):
    """统一提醒表"""
    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(32), nullable=True, index=True)  # task/habit/schedule/note
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    remind_at = Column(DateTime, nullable=False, index=True)
    repeat_rule = Column(JSONB, nullable=True)  # {"freq": "daily", "time": "21:00"}
    wx_template_id = Column(String(64), nullable=True)
    is_sent = Column(Boolean, default=False)
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="reminders")


class Attachment(Base):
    """通用附件表"""
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(32), nullable=True, index=True)  # project/task/note/memory/log
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    url = Column(String(1024), nullable=False)
    file_type = Column(String(64), nullable=True)
    file_name = Column(String(256), nullable=True)
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectLog(Base):
    """项目日志表"""
    __tablename__ = "project_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(64), nullable=False)  # created_task/completed_task/updated_project
    content = Column(Text, nullable=True)
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="project_logs")


class Notification(Base):
    """通知中心表"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    content = Column(Text, nullable=True)
    type = Column(String(32), nullable=True)  # reminder/system/project
    entity_type = Column(String(32), nullable=True)  # task/project/note
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")