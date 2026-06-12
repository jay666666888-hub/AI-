from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.models import User, Project, ProjectLog
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.api.deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

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
    # Convert SQLAlchemy models to dicts for Pydantic v1
    return [
        ProjectResponse.parse_obj({
            "id": p.id,
            "user_id": p.user_id,
            "title": p.title,
            "description": p.description,
            "goal": p.goal,
            "status": p.status,
            "progress": p.progress,
            "tags": list(p.tags) if p.tags else [],
            "ai_metadata": dict(p.ai_metadata) if p.ai_metadata else None,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        })
        for p in projects
    ]

@router.post("", response_model=ProjectResponse)
@limiter.limit("20/minute")
async def create_project(
    request: Request,
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建项目"""
    try:
        project = Project(**project_data.dict(), user_id=current_user.id)
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
        # Convert SQLAlchemy model to dict for Pydantic v1
        project_dict = {
            "id": project.id,
            "user_id": project.user_id,
            "title": project.title,
            "description": project.description,
            "goal": project.goal,
            "status": project.status,
            "progress": project.progress,
            "tags": list(project.tags) if project.tags else [],
            "ai_metadata": dict(project.ai_metadata) if project.ai_metadata else None,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        return ProjectResponse.parse_obj(project_dict)
    except Exception as e:
        raise

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
    # Convert SQLAlchemy model to dict
    project_dict = {
        "id": project.id,
        "user_id": project.user_id,
        "title": project.title,
        "description": project.description,
        "goal": project.goal,
        "status": project.status,
        "progress": project.progress,
        "tags": list(project.tags) if project.tags else [],
        "ai_metadata": dict(project.ai_metadata) if project.ai_metadata else None,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    return ProjectResponse.parse_obj(project_dict)

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

    update_data = project_data.dict(exclude_unset=True)
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
    # Convert SQLAlchemy model to dict
    project_dict = {
        "id": project.id,
        "user_id": project.user_id,
        "title": project.title,
        "description": project.description,
        "goal": project.goal,
        "status": project.status,
        "progress": project.progress,
        "tags": list(project.tags) if project.tags else [],
        "ai_metadata": dict(project.ai_metadata) if project.ai_metadata else None,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    return ProjectResponse.parse_obj(project_dict)

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