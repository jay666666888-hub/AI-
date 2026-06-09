"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
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
    ai_metadata: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


# ============== Habit Schemas ==============

class HabitLogCreate(BaseModel):
    """Schema for creating a habit log."""
    status: str = "completed"


class HabitStatsResponse(BaseModel):
    """Schema for habit statistics response."""
    task_id: UUID
    streak_days: int
    total_completions: int
    completion_rate: float