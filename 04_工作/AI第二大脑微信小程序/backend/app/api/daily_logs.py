"""
每日完成日志 API
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models.models import User, DailyLog
from app.schemas.schemas import DailyLogResponse, DailyLogStatsResponse
from app.api.deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def log_to_dict(log: DailyLog) -> dict:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "date": log.date,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "title": log.title,
        "completed_at": log.completed_at,
        "created_at": log.created_at,
    }


@router.get("", response_model=List[DailyLogResponse])
async def get_daily_logs(
    request: Request,
    log_date: Optional[str] = None,  # YYYY-MM-DD format
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定日期的日志"""
    query = select(DailyLog).where(DailyLog.user_id == current_user.id)

    if log_date:
        try:
            target_date = datetime.strptime(log_date, "%Y-%m-%d").date()
            query = query.where(DailyLog.date == target_date)
        except ValueError:
            pass  # 忽略无效日期格式

    query = query.order_by(DailyLog.completed_at.desc())
    result = await db.execute(query)
    logs = result.scalars().all()
    return [DailyLogResponse.parse_obj(log_to_dict(log)) for log in logs]


@router.get("/stats", response_model=DailyLogStatsResponse)
async def get_daily_log_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取完成统计"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # 今日完成数
    today_query = select(func.count()).where(
        and_(
            DailyLog.user_id == current_user.id,
            DailyLog.date == today
        )
    )
    today_result = await db.execute(today_query)
    today_completed = today_result.scalar() or 0

    # 本周完成数
    week_query = select(func.count()).where(
        and_(
            DailyLog.user_id == current_user.id,
            DailyLog.date >= week_start
        )
    )
    week_result = await db.execute(week_query)
    week_completed = week_result.scalar() or 0

    # 本月完成数
    month_query = select(func.count()).where(
        and_(
            DailyLog.user_id == current_user.id,
            DailyLog.date >= month_start
        )
    )
    month_result = await db.execute(month_query)
    month_completed = month_result.scalar() or 0

    # 获取今日日志
    logs_query = select(DailyLog).where(
        and_(
            DailyLog.user_id == current_user.id,
            DailyLog.date == today
        )
    ).order_by(DailyLog.completed_at.desc())
    logs_result = await db.execute(logs_query)
    logs = logs_result.scalars().all()

    return DailyLogStatsResponse(
        today_completed=today_completed,
        week_completed=week_completed,
        month_completed=month_completed,
        logs=[DailyLogResponse.parse_obj(log_to_dict(log)) for log in logs]
    )


@router.get("/dates")
async def get_log_dates(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定日期范围内有日志的日期列表"""
    query = select(DailyLog.date).where(
        DailyLog.user_id == current_user.id
    ).distinct()

    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.where(DailyLog.date >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.where(DailyLog.date <= end)
        except ValueError:
            pass

    query = query.order_by(DailyLog.date)
    result = await db.execute(query)
    dates = [str(row[0]) for row in result.fetchall()]
    return {"dates": dates}