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