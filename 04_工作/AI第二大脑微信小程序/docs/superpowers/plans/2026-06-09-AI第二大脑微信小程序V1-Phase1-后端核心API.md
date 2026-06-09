# AI第二大脑微信小程序 V1 实现计划 - Phase 1

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建后端核心 API + 数据库，支持用户认证、项目管理、Todo 任务、Inbox 笔记功能

**架构：** FastAPI + PostgreSQL，分层架构（Router → Service → Model），微信登录认证

**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy / PostgreSQL / Pydantic / Alembic

---

## 文件结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── database.py # 数据库连接
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # 依赖注入（获取当前用户）
│   │   ├── auth.py # 认证路由
│   │   ├── tasks.py         # 任务路由
│   │   ├── projects.py      # 项目路由
│   │   └── notes.py         # 笔记路由
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py        # SQLAlchemy 模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── task_service.py
│   │   ├── project_service.py
│   │   └── note_service.py
│   └── core/
│       ├── __init__.py
│       └── security.py      # JWT/微信验证
├── migrations/ # Alembic 迁移
│   └── versions/
├── requirements.txt
└── alembic.ini

frontend/
├── pages/
│   ├── index/              # 首页
│   ├── tasks/              # 任务中心
│   ├── calendar/           # 日历
│   └── mine/               # 我的
├── components/             # 组件
├── utils/                  # 工具函数
└── services/ # API 服务
```

---

## 任务 1：项目初始化与依赖

**文件：**
- 创建：`backend/requirements.txt`
- 创建：`backend/app/__init__.py`
- 创建：`backend/app/config.py`
- 创建：`backend/app/database.py`

- [ ] **步骤 1：创建依赖文件**

```txt
# backend/requirements.txt
fastapi==0.109.2
uvicorn[standard]==0.27.1
sqlalchemy==2.0.25
asyncpg==0.29.0
pydantic==2.6.1
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
alembic==1.13.1
python-multipart==0.0.9
wechatpayv3==1.2.15
httpx==0.26.0
```

- [ ] **步骤 2：创建配置管理**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "AI第二大脑"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/ai_brain"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080 # 7天
    
    # 微信小程序
    WX_APPID: str = ""
    WX_SECRET: str = ""
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

- [ ] **步骤 3：创建数据库连接**

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

- [ ] **步骤 4：创建主入口**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, tasks, projects, notes

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目"])
app.include_router(notes.router, prefix="/api/notes", tags=["笔记"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
```

- [ ] **步骤 5：Commit**

```bash
cd /mnt/e/黑曜石/04_工作/AI第二大脑微信小程序
git init2>/dev/null || true
git add -A
git commit -m "feat: init backend project structure"
```

---

## 任务 2：数据库模型

**文件：**
- 创建：`backend/app/models/models.py`
- 创建：`backend/app/models/__init__.py`

- [ ] **步骤 1：创建所有数据库模型**

```python
# backend/app/models/models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wx_openid = Column(String(100), unique=True)
    wx_unionid = Column(String(100), unique=True)
    nickname = Column(String(100))
    avatar_url = Column(String(500))
    phone = Column(String(20))
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    projects = relationship("Project", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    notes = relationship("Note", back_populates="user")
    memories = relationship("Memory", back_populates="user")
    reminders = relationship("Reminder", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    goal = Column(Text)
    status = Column(String(20), default="active")  # active/archived/completed
    progress = Column(Integer, default=0)  # 0-100
    tags = Column(ARRAY(String), default=[])
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")
    project_logs = relationship("ProjectLog", back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)

    type = Column(String(20), nullable=False)  # todo/habit/schedule/waiting/checklist
    title = Column(String(200), nullable=False)
    detail = Column(Text)
    detail_source = Column(String(20))  # manual/ai_generated/ai_rewritten
    status = Column(String(20), default="active")  # active/completed/cancelled/archived

    due_date = Column(DateTime, nullable=True)
    priority = Column(Integer, default=3)  # 1-5
    tags = Column(ARRAY(String), default=[])
    ai_metadata = Column(JSONB, nullable=True)

    # Habit 特有
    frequency = Column(String(20))  # daily/weekly/monthly/custom
    execution_mode = Column(String(20))  # timed/free
    scheduled_time = Column(String(10))  # 21:00
    target_type = Column(String(20))  # count/duration/custom
    target_value = Column(Integer)  # 如: 30

    # Schedule 特有
    location = Column(String(200))
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    # Waiting 特有
    wait_status = Column(String(20))  # waiting/recovered

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    habit_logs = relationship("HabitLog", back_populates="task")
    checklist_items = relationship("ChecklistItem", back_populates="task")


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    executed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="completed")  # completed/partial/missed/makeup
    ai_metadata = Column(JSONB, nullable=True)

    task = relationship("Task", back_populates="habit_logs")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    parent_id = Column(UUID(as_uuid=True), ForeignKey("checklist_items.id"), nullable=True)
    content = Column(String(500), nullable=False)
    is_done = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("Task", back_populates="checklist_items")


class Note(Base):
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    status = Column(String(20), default="inbox")  # inbox/processed/archived
    tags = Column(ARRAY(String), default=[])
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="notes")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    content = Column(Text)
    tags = Column(ARRAY(String), default=[])
    memory_type = Column(String(20))  # personal/family/project/important
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="memories")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    entity_type = Column(String(20))  # task/habit/schedule/note
    entity_id = Column(UUID(as_uuid=True))
    remind_at = Column(DateTime, nullable=False)
    repeat_rule = Column(JSONB)  # {"freq": "daily", "time": "21:00"}
    wx_template_id = Column(String(100))
    is_sent = Column(Boolean, default=False)
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="reminders")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(20))  # project/task/note/memory/log
    entity_id = Column(UUID(as_uuid=True))
    url = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_name = Column(String(200))
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectLog(Base):
    __tablename__ = "project_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    action = Column(String(50), nullable=False)  # created_task/completed_task/updated_project
    content = Column(Text)
    ai_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="project_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String(200), nullable=False)
    content = Column(Text)
    type = Column(String(20))  # reminder/system/project
    entity_type = Column(String(20))  # task/project/note
    entity_id = Column(UUID(as_uuid=True))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
```

- [ ] **步骤 2：Commit**

```bash
git add backend/app/models/
git commit -m "feat: add database models for all entities"
```

---

## 任务 3：Pydantic Schemas

**文件：**
- 创建：`backend/app/schemas/schemas.py`
- 创建：`backend/app/schemas/__init__.py`

- [ ] **步骤 1：创建 Pydantic Schemas**

```python
# backend/app/schemas/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# ============ User ============
class UserBase(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    wx_openid: Optional[str] = None
    wx_unionid: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    wx_openid: Optional[str] = None
    phone: Optional[str] = None
    ai_metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ============ Auth ============
class WxLoginRequest(BaseModel):
    code: str  # 微信授权码

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============ Project ============
class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    goal: Optional[str] = None
    tags: Optional[List[str]] = []

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    tags: Optional[List[str]] = None

class ProjectResponse(ProjectBase):
    id: UUID
    user_id: UUID
    status: str
    progress: int
    ai_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============ Task ============
class TaskBase(BaseModel):
    title: str
    detail: Optional[str] = None
    detail_source: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = 3
    tags: Optional[List[str]] = []
    project_id: Optional[UUID] = None

class TaskCreate(TaskBase):
    type: str = "todo"  # 默认 todo

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    detail: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None

class TaskResponse(TaskBase):
    id: UUID
    user_id: UUID
    type: str
    status: str
    ai_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============ Note ============
class NoteBase(BaseModel):
    content: str
    tags: Optional[List[str]] = []

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None

class NoteResponse(NoteBase):
    id: UUID
    user_id: UUID
    status: str
    ai_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============ Habit ============
class HabitLogCreate(BaseModel):
    status: str = "completed"  # completed/partial/missed/makeup

class HabitStatsResponse(BaseModel):
    task_id: UUID
    streak_days: int  # 连续天数
    total_completions: int  # 总完成次数
    completion_rate: float  # 完成率
```

- [ ] **步骤 2：Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add pydantic schemas"
```

---

## 任务 4：认证 API

**文件：**
- 创建：`backend/app/core/security.py`
- 创建：`backend/app/api/deps.py`
- 创建：`backend/app/api/auth.py`

- [ ] **步骤 1：创建安全模块**

```python
# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

- [ ] **步骤 2：创建依赖注入**

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import verify_token
from app.models.models import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return user
```

- [ ] **步骤 3：创建认证路由**

```python
# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import WxLoginRequest, AuthResponse, UserResponse
from app.core.security import create_access_token
from app.config import settings

router = APIRouter()

@router.post("/wx-login", response_model=AuthResponse)
async def wx_login(request: WxLoginRequest, db: AsyncSession = Depends(get_db)):
    """微信登录"""
    # 调用微信接口获取 openid
    async with httpx.AsyncClient() as client:
        wx_url = f"https://api.weixin.qq.com/sns/jscode2session?appid={settings.WX_APPID}&secret={settings.WX_SECRET}&js_code={request.code}&grant_type=authorization_code"
        response = await client.get(wx_url)
        wx_data = response.json()
    
    if "openid" not in wx_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="微信登录失败"
        )
    
    openid = wx_data["openid"]
    unionid = wx_data.get("unionid")
    
    # 查询或创建用户
    result = await db.execute(select(User).where(User.wx_openid == openid))
    user = result.scalar_one_or_none()
    
    if user is None:
        # 新用户
        user = User(wx_openid=openid, wx_unionid=unionid)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # 生成 JWT
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return AuthResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )

@router.post("/bind-phone", response_model=UserResponse)
async def bind_phone(
    phone: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """绑定手机号"""
    current_user.phone = phone
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)
```

- [ ] **步骤 4：Commit**

```bash
git add backend/app/core/ backend/app/api/auth.py backend/app/api/deps.py
git commit -m "feat: add authentication API with WeChat login"
```

---

## 任务 5：项目 API

**文件：**
- 创建：`backend/app/api/projects.py`

- [ ] **步骤 1：创建项目路由**

```python
# backend/app/api/projects.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.models import User, Project, ProjectLog
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[ProjectResponse])
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的所有项目"""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .where(Project.deleted_at.is_(None))
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p) for p in projects]

@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建项目"""
    project = Project(**project_data.model_dump(), user_id=current_user.id)
    db.add(project)
    
    # 记录日志
    log = ProjectLog(
        project_id=project.id,
        action="created_project",
        content=f"创建项目: {project_data.title}"
    )
    db.add(log)
    
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目详情"""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .where(Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ProjectResponse.model_validate(project)

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新项目"""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .where(Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    # 记录日志
    log = ProjectLog(
        project_id=project_id,
        action="updated_project",
        content=f"更新项目"
    )
    db.add(log)
    
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)

@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除项目（软删除）"""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .where(Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    from datetime import datetime
    project.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "项目已删除"}

@router.get("/{project_id}/logs")
async def get_project_logs(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目日志"""
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .where(Project.user_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    result = await db.execute(
        select(ProjectLog)
        .where(ProjectLog.project_id == project_id)
        .order_by(ProjectLog.created_at.desc())
    )
    logs = result.scalars().all()
    return [{"id": str(log.id), "action": log.action, "content": log.content, "created_at": log.created_at.isoformat()} for log in logs]
```

- [ ] **步骤 2：Commit**

```bash
git add backend/app/api/projects.py
git commit -m "feat: add project CRUD API"
```

---

## 任务 6：任务 API

**文件：**
- 创建：`backend/app/api/tasks.py`

- [ ] **步骤 1：创建任务路由**

```python
# backend/app/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.models import User, Task, HabitLog, ProjectLog
from app.schemas.schemas import TaskCreate, TaskUpdate, TaskResponse, HabitLogCreate, HabitStatsResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    type: str = None,
    status: str = None,
    project_id: UUID = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    query = select(Task).where(Task.user_id == current_user.id).where(Task.deleted_at.is_(None))
    
    if type:
        query = query.where(Task.type == type)
    if status:
        query = query.where(Task.status == status)
    if project_id:
        query = query.where(Task.project_id == project_id)
    
    query = query.order_by(Task.created_at.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]

@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
    task = Task(**task_data.model_dump(), user_id=current_user.id)
    db.add(task)
    
    # 如果关联了项目，记录日志
    if task_data.project_id:
        log = ProjectLog(
            project_id=task_data.project_id,
            action="created_task",
            content=f"创建任务: {task_data.title}"
        )
        db.add(log)
    
    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskResponse.model_validate(task)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新任务"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)

@router.post("/{task_id}/complete")
async def complete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """完成任务"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task.status = "completed"
    
    # 如果关联了项目，记录日志
    if task.project_id:
        log = ProjectLog(
            project_id=task.project_id,
            action="completed_task",
            content=f"完成任务: {task.title}"
        )
        db.add(log)
    
    await db.commit()
    return {"message": "任务已完成"}

@router.delete("/{task_id}")
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除任务（软删除）"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "任务已删除"}

# ============ Habit 专用 API ============

@router.post("/habits/{task_id}/log")
async def log_habit(
    task_id: UUID,
    log_data: HabitLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """记录 Habit 执行"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
        .where(Task.type == "habit")
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Habit 不存在")
    
    habit_log = HabitLog(task_id=task_id, status=log_data.status)
    db.add(habit_log)
    await db.commit()
    return {"message": "已记录"}

@router.get("/habits/{task_id}/stats", response_model=HabitStatsResponse)
async def get_habit_stats(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取 Habit 统计"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
        .where(Task.type == "habit")
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Habit 不存在")
    
    # 获取所有 log
    result = await db.execute(
        select(HabitLog)
        .where(HabitLog.task_id == task_id)
        .order_by(HabitLog.executed_at.desc())
    )
    logs = result.scalars().all()
    
    total = len(logs)
    completed = sum(1 for log in logs if log.status == "completed")
    
    # 计算连续天数
    streak_days = 0
    if logs:
        from datetime import timedelta
        today = datetime.utcnow().date()
        check_date = today
        for log in logs:
            log_date = log.executed_at.date()
            if log_date == check_date:
                if log.status == "completed":
                    streak_days += 1
                    check_date -= timedelta(days=1)
                else:
                    break
            else:
                break
    
    completion_rate = completed / total if total > 0 else 0
    
    return HabitStatsResponse(
        task_id=task_id,
        streak_days=streak_days,
        total_completions=completed,
        completion_rate=round(completion_rate, 2)
    )
```

- [ ] **步骤 2：Commit**

```bash
git add backend/app/api/tasks.py
git commit -m "feat: add task CRUD API with habit support"
```

---

## 任务 7：笔记 API

**文件：**
- 创建：`backend/app/api/notes.py`

- [ ] **步骤 1：创建笔记路由**

```python
# backend/app/api/notes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.models import User, Note
from app.schemas.schemas import NoteCreate, NoteUpdate, NoteResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("")
async def get_notes(
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取笔记列表"""
    query = select(Note).where(Note.user_id == current_user.id).where(Note.deleted_at.is_(None))
    
    if status:
        query = query.where(Note.status == status)
    
    query = query.order_by(Note.created_at.desc())
    result = await db.execute(query)
    notes = result.scalars().all()
    return [NoteResponse.model_validate(n) for n in notes]

@router.post("")
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建笔记（默认进入 Inbox）"""
    note = Note(**note_data.model_dump(), user_id=current_user.id, status="inbox")
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)

@router.put("/{note_id}")
async def update_note(
    note_id: UUID,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新笔记"""
    result = await db.execute(
        select(Note)
        .where(Note.id == note_id)
        .where(Note.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)

@router.delete("/{note_id}")
async def delete_note(
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除笔记（软删除）"""
    result = await db.execute(
        select(Note)
        .where(Note.id == note_id)
        .where(Note.user_id == current_user.id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    note.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "笔记已删除"}

@router.get("/inbox/count")
async def get_inbox_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取 Inbox数量"""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(Note.id))
        .where(Note.user_id == current_user.id)
        .where(Note.status == "inbox")
        .where(Note.deleted_at.is_(None))
    )
    count = result.scalar()
    return {"count": count}
```

- [ ] **步骤 2：Commit**

```bash
git add backend/app/api/notes.py
git commit -m "feat: add note/inbox API"
```

---

## 任务 8：数据库迁移

**文件：**
- 创建：`backend/migrations/env.py`
- 创建：`backend/migrations/script.py.mako`
- 创建：`backend/alembic.ini`

- [ ] **步骤 1：初始化 Alembic**

```bash
cd /mnt/e/黑曜石/04_工作/AI第二大脑微信小程序/backend
alembic init migrations
```

- [ ] **步骤 2：配置 alembic.ini**

```ini
# backend/alembic.ini
[alembic]
script_location = migrations
sqlalchemy.url = postgresql+asyncpg://user:pass@localhost:5432/ai_brain
```

- [ ] **步骤 3：创建初始迁移**

```bash
alembic revision --autogenerate -m "init all tables"
```

- [ ] **步骤 4：Commit**

```bash
git add backend/migrations/ backend/alembic.ini
git commit -m "feat: add database migrations"
```

---

## 任务 9：前端基础框架

**文件：**
- 创建：`frontend/app.js`
- 创建：`frontend/project.config.js`
- 创建：`frontend/utils/api.js`
- 创建：`frontend/utils/auth.js`
- 创建：`frontend/utils/constants.js`

- [ ] **步骤 1：创建项目配置**

```javascript
// frontend/project.config.js
module.exports = {
  appid: "your-appid",
  projectname: "ai-brain",
  description: "AI第二大脑微信小程序",
  setting: {
    urlCheck: true,
    es6: true,
    postcss: true,
    minified": true
  },
  compileType: "miniprogram"
}
```

- [ ] **步骤 2：创建 app.js**

```javascript
// frontend/app.js
App({
  globalData: {
    userInfo: null,
    token: null,
    baseUrl: "http://localhost:8000/api"
  },
  
  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
  },
  
  login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: async (res) => {
          if (res.code) {
            try {
              const response = await this.request('/auth/wx-login', {
                method: 'POST',
                body: { code: res.code }
              })
              this.globalData.token = response.access_token
              this.globalData.userInfo = response.user
              wx.setStorageSync('token', response.access_token)
              resolve(response)
            } catch (e) {
              reject(e)
            }
          } else {
            reject(new Error('微信登录失败'))
          }
        }
      })
    })
  },
  
  request(url, options = {}) {
    return new Promise((resolve, reject) => {
      const { baseUrl, token } = this.globalData
      wx.request({
        url: `${baseUrl}${url}`,
        header: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...options.header
        },
        ...options,
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data)
          } else if (res.statusCode === 401) {
            this.login().then(resolve).catch(reject)
          } else {
            reject(res.data)
          }
        },
        fail: reject
      })
    })
  }
})
```

- [ ] **步骤 3：创建工具函数**

```javascript
// frontend/utils/constants.js
module.exports = {
  TASK_TYPES: {
    TODO: 'todo',
    HABIT: 'habit',
    SCHEDULE: 'schedule',
    WAITING: 'waiting',
    CHECKLIST: 'checklist'
  },
  TASK_STATUS: {
    ACTIVE: 'active',
    COMPLETED: 'completed',
    CANCELLED: 'cancelled',
    ARCHIVED: 'archived'
  },
  PRIORITY: {
    LOW: 5,
    NORMAL: 3,
    HIGH: 1
  }
}

// frontend/utils/api.js
const app = getApp()

module.exports = {
  // 认证
  wxLogin: (code) => app.request('/auth/wx-login', { method: 'POST', body: { code } }),
  
  // 项目
  getProjects: () => app.request('/projects'),
  createProject: (data) => app.request('/projects', { method: 'POST', body: data }),
  updateProject: (id, data) => app.request(`/projects/${id}`, { method: 'PUT', body: data }),
  
  // 任务
  getTasks: (params) => app.request('/tasks?' + new URLSearchParams(params)),
  createTask: (data) => app.request('/tasks', { method: 'POST', body: data }),
  updateTask: (id, data) => app.request(`/tasks/${id}`, { method: 'PUT', body: data }),
  completeTask: (id) => app.request(`/tasks/${id}/complete`, { method: 'POST' }),
  
  // 笔记
  getNotes: (status) => app.request('/notes' + (status ? `?status=${status}` : '')),
  createNote: (data) => app.request('/notes', { method: 'POST', body: data }),
  updateNote: (id, data) => app.request(`/notes/${id}`, { method: 'PUT', body: data }),
  getInboxCount: () => app.request('/notes/inbox/count'),
  
  // 习惯
  logHabit: (taskId, data) => app.request(`/tasks/habits/${taskId}/log`, { method: 'POST', body: data }),
  getHabitStats: (taskId) => app.request(`/tasks/habits/${taskId}/stats`)
}

// frontend/utils/auth.js
const app = getApp()

module.exports = {
  checkSession: () => {
    return new Promise((resolve, reject) => {
      wx.checkSession({
        success: resolve,
        fail: reject
      })
    })
  },
  
  requireAuth: async () => {
    try {
      await module.exports.checkSession()
      if (!app.globalData.token) {
        await app.login()
      }
    } catch (e) {
      await app.login()
    }
  }
}
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/app.js frontend/project.config.js frontend/utils/
git commit -m "feat: init frontend base framework"
```

---

## 任务 10：首页开发

**文件：**
- 创建：`frontend/pages/index/index.js`
- 创建：`frontend/pages/index/index.wxml`
- 创建：`frontend/pages/index/index.wxss`

- [ ] **步骤 1：创建首页逻辑**

```javascript
// frontend/pages/index/index.js
const app = getApp()
const api = require('../../utils/api')
const { getInboxCount } = api

Page({
  data: {
    inboxCount: 0,
    todayTimedTasks: [],
    todayFreeTasks: [],
    projects: []
  },
  
  onLoad() {
    this.loadData()
  },
  
  onShow() {
    this.loadData()
  },
  
  async loadData() {
    try {
      // 加载 Inbox 数量
      const inboxRes = await getInboxCount()
      this.setData({ inboxCount: inboxRes.count })
      
      // 加载今日任务
      const tasks = await api.getTasks({ status: 'active' })
      const today = new Date().toISOString().split('T')[0]
      
      const timedTasks = tasks.filter(t => t.type === 'schedule' && t.scheduled_time)
        .sort((a, b) => a.scheduled_time.localeCompare(b.scheduled_time))
      
      const freeTasks = tasks.filter(t => t.type === 'todo' && !t.due_date)
      
      this.setData({
        todayTimedTasks: timedTasks,
        todayFreeTasks: freeTasks
      })
      
      // 加载进行中的项目
      const projects = await api.getProjects()
      const activeProjects = projects.filter(p => p.status === 'active').slice(0, 5)
      this.setData({ projects: activeProjects })
      
    } catch (e) {
      console.error('加载数据失败', e)
    }
  },
  
  goToInbox() {
    wx.navigateTo({ url: '/pages/tasks/index?type=inbox' })
  },
  
  goToProject(e) {
    const { id } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/tasks/index?projectId=${id}` })
  },
  
  quickAdd() {
    wx.navigateTo({ url: '/pages/tasks/create' })
  }
})
```

- [ ] **步骤 2：创建首页模板**

```html
<!-- frontend/pages/index/index.wxml -->
<view class="container">
  <!-- Inbox 入口 -->
  <view class="inbox-card" bindtap="goToInbox">
    <view class="inbox-icon">📥</view>
    <view class="inbox-info">
      <text class="inbox-title">Inbox（待整理）</text>
      <text class="inbox-count">{{inboxCount}}条</text>
    </view>
    <view class="arrow">›</view>
  </view>
  
  <!-- 今日定时任务 -->
  <view class="section">
    <text class="section-title">今日定时任务</text>
    <view class="task-list" wx:if="{{todayTimedTasks.length}}">
      <view class="task-item" wx:for="{{todayTimedTasks}}" wx:key="id">
        <text class="task-time">{{item.scheduled_time}}</text>
        <text class="task-title">{{item.title}}</text>
      </view>
    </view>
    <view class="empty" wx:else>
      <text>暂无定时任务</text>
    </view>
  </view>
  
  <!-- 今日自由任务 -->
  <view class="section">
    <text class="section-title">今日自由任务</text>
    <view class="task-list" wx:if="{{todayFreeTasks.length}}">
      <view class="task-item" wx:for="{{todayFreeTasks}}" wx:key="id">
        <checkbox-group>
          <label>
            <checkbox checked="{{item.status === 'completed'}}"/>
           <text class="task-title">{{item.title}}</text>
          </label>
        </checkbox-group>
      </view>
    </view>
    <view class="empty" wx:else>
      <text>暂无自由任务</text>
    </view>
  </view>
  
  <!-- 进行中的项目 -->
  <view class="section">
    <text class="section-title">进行中的项目</text>
    <view class="project-list" wx:if="{{projects.length}}">
      <view class="project-item" wx:for="{{projects}}" wx:key="id" bindtap="goToProject" data-id="{{item.id}}">
        <text class="project-title">{{item.title}}</text>
        <view class="progress-bar">
          <view class="progress-fill" style="width: {{item.progress}}%"></view>
        </view>
        <text class="progress-text">{{item.progress}}%</text>
      </view>
    </view>
    <view class="empty" wx:else>
      <text>暂无项目</text>
    </view>
  </view>
  
  <!-- 快速添加按钮 -->
  <view class="fab" bindtap="quickAdd">+</view>
</view>
```

- [ ] **步骤 3：创建首页样式**

```css
/* frontend/pages/index/index.wxss */
.container {
  padding: 20rpx;
  background: #f5f5f5;
  min-height: 100vh;
}

.inbox-card {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30rpx;
  border-radius: 16rpx;
  margin-bottom: 30rpx;
}

.inbox-icon {
  font-size: 48rpx;
  margin-right: 20rpx;
}

.inbox-info {
  flex: 1;
}

.inbox-title {
  font-size: 32rpx;
  font-weight: 600;
  display: block;
}

.inbox-count {
  font-size: 24rpx;
  opacity: 0.8;
}

.arrow {
  font-size: 48rpx;
  opacity: 0.8;
}

.section {
  background: white;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}

.task-item {
  display: flex;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.task-item:last-child {
  border-bottom: none;
}

.task-time {
  width: 100rpx;
  color: #667eea;
  font-weight: 500;
}

.task-title {
  flex: 1;
  color: #333;
}

.project-item {
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.project-item:last-child {
  border-bottom: none;
}

.project-title {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 12rpx;
  display: block;
}

.progress-bar {
  height: 8rpx;
  background: #f0f0f0;
  border-radius: 4rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.progress-text {
  font-size: 22rpx;
  color: #999;
  margin-top: 8rpx;
}

.empty {
  text-align: center;
  color: #999;
  padding: 40rpx 0;
}

.fab {
  position: fixed;
  right: 40rpx;
  bottom: 60rpx;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 20rpx rgba(102, 126, 234, 0.4);
}
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/pages/index/
git commit -m "feat: add homepage with inbox, tasks and projects"
```

---

## 自检清单

1. **规格覆盖度检查：**
   - [x] 用户登录（微信登录） -任务 4
   - [x] 项目 CRUD + 日志 - 任务 5
   - [x] 任务 CRUD + 完成任务 - 任务 6
   - [x] Habit 记录 + 统计 - 任务 6
   - [x] 笔记/Inbox CRUD - 任务 7
   - [x] 首页展示 - 任务 10
   - [x] 数据库模型 - 任务 2
   - [x] API 路由 - 任务 4-7

2. **占位符扫描：** 无 TODO/TBD/待定

3. **类型一致性：** 无不一致

---

## 执行选项

**计划已完成并保存到 `docs/superpowers/plans/2026-06-09-AI第二大脑微信小程序V1-Phase1-后端核心API.md`**

两种执行方式：

**1. 子代理驱动（推荐）** - 每个任务调度一个新的子代理，任务间进行审查，快速迭代

**2. 内联执行** - 在当前会话中使用 executing-plans 执行任务，批量执行并设有检查点

**选哪种方式？**