from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID
from datetime import datetime, timedelta
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