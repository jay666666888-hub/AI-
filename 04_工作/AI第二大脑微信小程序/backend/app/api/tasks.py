from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import User, Task, HabitLog, ProjectLog
from app.schemas.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, HabitLogCreate, HabitStatsResponse,
    HabitCreate, HabitUpdate
)
from app.api.deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def task_to_dict(task: Task) -> dict:
    """Convert SQLAlchemy Task model to dict for Pydantic v1"""
    return {
        "id": task.id,
        "user_id": task.user_id,
        "project_id": task.project_id,
        "type": task.type,
        "title": task.title,
        "detail": task.detail,
        "detail_source": task.detail_source,
        "status": task.status,
        "due_date": task.due_date,
        "priority": task.priority,
        "tags": task.tags,
        "ai_metadata": task.ai_metadata,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "frequency": task.frequency,
        "execution_mode": task.execution_mode,
        "scheduled_time": task.scheduled_time,
        "target_type": task.target_type,
        "target_value": task.target_value,
    }


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
    return [TaskResponse.parse_obj(task_to_dict(t)) for t in tasks]


@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
    task = Task(**task_data.dict(), user_id=current_user.id)
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
    return TaskResponse.parse_obj(task_to_dict(task))


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
    return TaskResponse.parse_obj(task_to_dict(task))


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

    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return TaskResponse.parse_obj(task_to_dict(task))


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

    habit_log = HabitLog(
        task_id=task_id,
        status=log_data.status,
        executed_at=log_data.executed_at or datetime.utcnow()
    )
    db.add(habit_log)
    await db.commit()
    await db.refresh(habit_log)
    return {
        "message": "已记录",
        "log_id": str(habit_log.id),
        "executed_at": habit_log.executed_at.isoformat()
    }


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

    # 获取所有 log，按时间倒序
    result = await db.execute(
        select(HabitLog)
        .where(HabitLog.task_id == task_id)
        .order_by(HabitLog.executed_at.desc())
    )
    logs = result.scalars().all()

    frequency = task.frequency or "daily"
    now = datetime.utcnow()
    today = now.date()

    # 计算本周开始和结束
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # 计算本月开始和结束
    month_start = today.replace(day=1)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

    # 根据频率计算期望次数
    def get_expected_count(start_date, end_date, freq):
        """按频次计算期望次数：
        - daily: 日历跨度（每天1次）
        - weekly: 本周期=1（每周1次）
        - monthly: 本周期=1（每月1次）
        """
        if freq == "daily":
            return (end_date - start_date).days + 1
        elif freq == "weekly":
            # 每周1次，本周=1
            return 1
        elif freq == "monthly":
            # 每月1次，本月=1
            return 1
        return 1

    # 计算本周应完成次数
    weekly_expected = get_expected_count(week_start, today, frequency)
    # 计算本月应完成次数
    monthly_expected = get_expected_count(month_start, today, frequency)

    # 统计完成次数
    weekly_completed = 0
    monthly_completed = 0
    total_completions = 0
    today_logs = []

    for log in logs:
        log_date = log.executed_at.date()
        if log.status == "completed":
            total_completions += 1
            if week_start <= log_date <= today:
                weekly_completed += 1
            if month_start <= log_date <= today:
                monthly_completed += 1
            if log_date == today:
                today_logs.append(log)

    # 计算完成率
    weekly_completion_rate = weekly_completed / weekly_expected if weekly_expected > 0 else 0
    monthly_completion_rate = monthly_completed / monthly_expected if monthly_expected > 0 else 0

    # 按天去重统计 completed_dates（统一数据源）
    completed_dates = set()
    for log in logs:
        if log.status == "completed":
            completed_dates.add(log.executed_at.date())

    # 周期内去重天数
    weekly_completed = len([d for d in completed_dates if week_start <= d <= today])
    monthly_completed = len([d for d in completed_dates if month_start <= d <= today])
    total_completions = len(completed_dates)

    # 计算连续天数 (从今天往前数)
    streak_days = 0
    weekly_streak = 0
    check_date = today

    if frequency == "daily":
        # 计算连续天数
        while check_date >= week_start:
            if check_date in completed_dates:
                streak_days += 1
                check_date -= timedelta(days=1)
            else:
                break

        # 本周连续
        weekly_streak = streak_days

    elif frequency == "weekly":
        # 连续周数
        completed_weeks = set()
        for log in logs:
            if log.status == "completed":
                log_date = log.executed_at.date()
                week_num = log_date.isocalendar()[1]
                year = log_date.isocalendar()[0]
                completed_weeks.add((year, week_num))

        # 计算连续周
        current_week = today.isocalendar()
        check_week = current_week
        while True:
            if (check_week[0], check_week[1]) in completed_weeks:
                weekly_streak += 1
                check_week = (check_week[0], check_week[1] - 1) if check_week[1] > 1 else (check_week[0] - 1, 52)
                if weekly_streak > 20:  # 防止无限循环
                    break
            else:
                break
        streak_days = weekly_streak

    # 累计应完成次数 - 按自然日计算，不依赖log起点
    total_expected = get_expected_count(week_start, today, frequency)

    return HabitStatsResponse(
        task_id=task_id,
        streak_days=streak_days,
        weekly_streak=weekly_streak,
        weekly_completion_rate=round(min(weekly_completion_rate, 1.0), 2),
        monthly_completion_rate=round(min(monthly_completion_rate, 1.0), 2),
        total_completions=total_completions,
        total_expected=total_expected
    )


# ============ 专用 Habit API ============

@router.post("/habits", response_model=TaskResponse)
async def create_habit(
    habit_data: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建 Habit"""
    # 验证
    if habit_data.execution_mode == "timed" and not habit_data.scheduled_time:
        raise HTTPException(status_code=400, detail="定时模式必须指定 scheduled_time")

    # 创建 task (type=habit)
    task = Task(
        user_id=current_user.id,
        type="habit",
        title=habit_data.title,
        detail=habit_data.detail,
        status="active",
        tags=habit_data.tags or [],
        project_id=habit_data.project_id,
        frequency=habit_data.frequency,
        execution_mode=habit_data.execution_mode,
        scheduled_time=habit_data.scheduled_time,
        target_type=habit_data.target_type,
        target_value=habit_data.target_value,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return TaskResponse.parse_obj(task_to_dict(task))


@router.put("/habits/{task_id}", response_model=TaskResponse)
async def update_habit(
    task_id: UUID,
    habit_data: HabitUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新 Habit"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == current_user.id)
        .where(Task.type == "habit")
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Habit 不存在")

    update_data = habit_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return TaskResponse.parse_obj(task_to_dict(task))


@router.get("/habits/today")
async def get_today_habits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取今日 Habits状态"""
    today = datetime.utcnow().date()

    # 获取所有 active habits
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .where(Task.type == "habit")
        .where(Task.status == "active")
        .where(Task.deleted_at.is_(None))
    )
    habits = result.scalars().all()

    # 获取今日的 habit logs
    result = await db.execute(
        select(HabitLog)
        .where(HabitLog.task_id.in_([h.id for h in habits]))
        .where(HabitLog.executed_at >= datetime.combine(today, datetime.min.time()))
    )
    today_logs = result.scalars().all()
    today_log_map = {log.task_id: log for log in today_logs}

    # 获取需要提醒的 habits (scheduled_time <= now for timed habits)
    current_time = datetime.utcnow().strftime("%H:%M")

    habit_statuses = []
    for habit in habits:
        log = today_log_map.get(habit.id)
        is_completed = log and log.status == "completed"

        # 判断是否需要提醒
        need_reminder = False
        if not is_completed:
            if habit.execution_mode == "timed" and habit.scheduled_time:
                # 定时模式：已过 scheduled_time
                need_reminder = habit.scheduled_time <= current_time
            elif habit.execution_mode == "free":
                # 自由模式：22:00 后提醒
                need_reminder = current_time >= "22:00"

        habit_statuses.append({
            "id": str(habit.id),
            "title": habit.title,
            "frequency": habit.frequency,
            "execution_mode": habit.execution_mode,
            "scheduled_time": habit.scheduled_time,
            "target_type": habit.target_type,
            "target_value": habit.target_value,
            "is_completed_today": is_completed,
            "need_reminder": need_reminder,
            "log": {
                "id": str(log.id) if log else None,
                "status": log.status if log else None,
                "executed_at": log.executed_at.isoformat() if log else None
            } if log else None
        })

    return {
        "date": today.isoformat(),
        "total": len(habits),
        "completed": sum(1 for h in habit_statuses if h["is_completed_today"]),
        "pending": sum(1 for h in habit_statuses if not h["is_completed_today"]),
        "habits": habit_statuses
    }


@router.get("/habits/pending")
async def get_pending_habits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取需要提醒的 Habits (用于定时任务触发)"""
    today = datetime.utcnow().date()
    current_time = datetime.utcnow().strftime("%H:%M")

    # 获取所有 active habits
    result = await db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .where(Task.type == "habit")
        .where(Task.status == "active")
        .where(Task.deleted_at.is_(None))
    )
    habits = result.scalars().all()

    # 获取今日 logs
    result = await db.execute(
        select(HabitLog)
        .where(HabitLog.task_id.in_([h.id for h in habits]))
        .where(HabitLog.executed_at >= datetime.combine(today, datetime.min.time()))
    )
    today_logs = result.scalars().all()
    completed_today = {log.task_id for log in today_logs if log.status == "completed"}

    pending = []
    for habit in habits:
        if habit.id in completed_today:
            continue

        if habit.execution_mode == "timed" and habit.scheduled_time:
            # 22:00 最终提醒
            if current_time >= "22:00":
                pending.append({
                    "id": str(habit.id),
                    "title": habit.title,
                    "scheduled_time": habit.scheduled_time,
                    "reminder_type": "final"
                })
        elif habit.execution_mode == "free":
            # 22:00 第一次提醒, 23:00 最终提醒
            if current_time >= "22:00":
                pending.append({
                    "id": str(habit.id),
                    "title": habit.title,
                    "reminder_type": "final" if current_time >= "23:00" else "reminder"
                })

    return {
        "current_time": current_time,
        "pending_habits": pending
    }