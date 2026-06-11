"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# ============== User Schemas ==============

class UserBase(BaseModel):
    """Base user schema with common fields."""
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    wx_openid: Optional[str] = None
    wx_unionid: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    wx_openid: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    ai_metadata: Optional[dict] = None
    created_at: Optional[datetime] = None


# ============== Auth Schemas ==============

class WxLoginRequest(BaseModel):
    """WeChat login request schema."""
    code: str


class AuthResponse(BaseModel):
    """Authentication response schema."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============== Project Schemas ==============

class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    title: str
    description: Optional[str] = None
    goal: Optional[str] = None
    tags: Optional[List[str]] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    title: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    tags: Optional[List[str]] = None


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    tags: Optional[List[str]] = None
    ai_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None



# ============== Task Schemas ==============

class TaskBase(BaseModel):
    """Base task schema with common fields."""
    title: str
    detail: Optional[str] = None
    detail_source: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(default=3, ge=1, le=5)
    tags: Optional[List[str]] = None
    project_id: Optional[UUID] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    type: str = "todo"
    # Habit-specific fields (when type="habit")
    frequency: Optional[str] = None # daily/weekly/monthly/custom
    execution_mode: Optional[str] = None   # timed/free
    scheduled_time: Optional[str] = None  # HH:MM
    target_type: Optional[str] = None      # count/duration
    target_value: Optional[int] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = None
    detail: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    tags: Optional[List[str]] = None


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: UUID
    user_id: UUID
    title: str
    detail: Optional[str] = None
    detail_source: Optional[str] = None
    type: str
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    project_id: Optional[UUID] = None
    ai_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Habit fields
    frequency: Optional[str] = None
    execution_mode: Optional[str] = None
    scheduled_time: Optional[str] = None
    target_type: Optional[str] = None
    target_value: Optional[int] = None



# ============== Note Schemas ==============

class NoteBase(BaseModel):
    """Base note schema with common fields."""
    content: str
    tags: Optional[List[str]] = None


class NoteCreate(NoteBase):
    """Schema for creating a note."""
    pass


class NoteUpdate(BaseModel):
    """Schema for updating a note."""
    content: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteResponse(BaseModel):
    """Schema for note response."""
    id: UUID
    user_id: UUID
    content: str
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    ai_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None



# ============== Habit Schemas ==============

class HabitLogCreate(BaseModel):
    """Schema for creating a habit log."""
    status: str = "completed"
    executed_at: Optional[datetime] = None  # 可选，用于补录


class HabitStatsResponse(BaseModel):
    """Schema for habit statistics response."""
    task_id: UUID
    streak_days: int          # 连续完成天数
    weekly_streak: int        # 本周连续天数
    weekly_completion_rate: float  # 本周完成率 (0-1)
    monthly_completion_rate: float # 本月完成率 (0-1)
    total_completions: int    # 累计完成次数
    total_expected: int      # 累计应完成次数


class HabitCreate(BaseModel):
    """Schema for creating a habit."""
    title: str
    frequency: str = "daily"           # daily/weekly/monthly/custom
    execution_mode: str = "free"        # timed/free
    scheduled_time: Optional[str] = None  # HH:MM 格式，仅 timed模式
    target_type: Optional[str] = None  # count/duration
    target_value: Optional[int] = None # 如30(分钟)、1(次)
    detail: Optional[str] = None
    tags: Optional[List[str]] = None
    project_id: Optional[UUID] = None


class HabitUpdate(BaseModel):
    """Schema for updating a habit."""
    title: Optional[str] = None
    frequency: Optional[str] = None
    execution_mode: Optional[str] = None
    scheduled_time: Optional[str] = None
    target_type: Optional[str] = None
    target_value: Optional[int] = None
    detail: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


# ============== Note Conversion Schemas ==============

class NoteConvertRequest(BaseModel):
    """Schema for converting a note to another type."""
    target_type: str # task, project, or memory
    title: Optional[str] = None  # Optional title override
    task_type: Optional[str] = "todo"  # Only for task conversion
    project_id: Optional[UUID] = None  # Only for task conversion


class NoteConvertResponse(BaseModel):
    """Schema for note conversion response."""
    original_note_id: UUID
    converted_to: str  # task, project, or memory
    converted_id: UUID
    message: str


# ============== Notification Schemas ==============

class NotificationResponse(BaseModel):
    """Schema for notification response."""
    id: UUID
    user_id: UUID
    title: str
    content: Optional[str] = None
    type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    is_read: bool
    created_at: datetime



class NotificationReadResponse(BaseModel):
    """Schema for marking notifications as read."""
    updated_count: int


# ============== Reminder Schemas ==============

class RepeatRule(BaseModel):
    """Schema for repeat rule."""
    freq: str  # daily/weekly/monthly
    time: str  # HH:MM


class ReminderCreate(BaseModel):
    """Schema for creating a reminder."""
    entity_type: Optional[str] = None  # task/habit/schedule/note
    entity_id: Optional[UUID] = None
    remind_at: datetime
    repeat_rule: Optional[RepeatRule] = None
    wx_template_id: Optional[str] = None


class ReminderResponse(BaseModel):
    """Schema for reminder response."""
    id: UUID
    user_id: UUID
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    remind_at: datetime
    repeat_rule: Optional[dict] = None
    wx_template_id: Optional[str] = None
    is_sent: bool
    ai_metadata: Optional[dict] = None
    created_at: datetime
    sent_at: Optional[datetime] = None


# ============== DailyLog Schemas ==============

class DailyLogResponse(BaseModel):
    """Schema for daily log response."""
    id: UUID
    user_id: UUID
    date: date
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    title: str
    completed_at: datetime
    created_at: datetime


class DailyLogStatsResponse(BaseModel):
    """Schema for daily log statistics."""
    today_completed: int
    week_completed: int
    month_completed: int
    logs: List[DailyLogResponse]


# ============== Memory Schemas ==============

class MemoryBase(BaseModel):
    """Base memory schema."""
    title: str
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    memory_type: Optional[str] = None  # personal/family/project/important


class MemoryCreate(MemoryBase):
    """Schema for creating a memory."""
    pass


class MemoryUpdate(BaseModel):
    """Schema for updating a memory."""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    memory_type: Optional[str] = None


class MemoryResponse(BaseModel):
    """Schema for memory response."""
    id: UUID
    user_id: UUID
    title: str
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    memory_type: Optional[str] = None
    ai_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None