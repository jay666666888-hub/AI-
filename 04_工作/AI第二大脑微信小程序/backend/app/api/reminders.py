"""
提醒 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.models.models import User, Reminder
from app.schemas.schemas import ReminderCreate, ReminderResponse
from app.api.deps import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def reminder_to_dict(r: Reminder) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "entity_type": r.entity_type,
        "entity_id": r.entity_id,
        "remind_at": r.remind_at,
        "repeat_rule": r.repeat_rule,
        "wx_template_id": r.wx_template_id,
        "is_sent": r.is_sent,
        "ai_metadata": r.ai_metadata,
        "created_at": r.created_at,
        "sent_at": r.sent_at,
    }


@router.get("", response_model=List[ReminderResponse])
async def get_reminders(
    entity_type: Optional[str] = None,
    is_sent: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的提醒列表"""
    query = select(Reminder).where(Reminder.user_id == current_user.id)

    if entity_type:
        query = query.where(Reminder.entity_type == entity_type)
    if is_sent is not None:
        query = query.where(Reminder.is_sent == is_sent)

    query = query.order_by(Reminder.remind_at.asc())
    result = await db.execute(query)
    reminders = result.scalars().all()
    return [ReminderResponse.parse_obj(reminder_to_dict(r)) for r in reminders]


@router.post("", response_model=ReminderResponse)
@limiter.limit("20/minute")
async def create_reminder(
    request: Request,
    reminder_data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建提醒"""
    reminder = Reminder(
        user_id=current_user.id,
        entity_type=reminder_data.entity_type,
        entity_id=reminder_data.entity_id,
        remind_at=reminder_data.remind_at,
        repeat_rule=reminder_data.repeat_rule.dict() if reminder_data.repeat_rule else None,
        wx_template_id=reminder_data.wx_template_id,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return ReminderResponse.parse_obj(reminder_to_dict(reminder))


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除提醒"""
    query = select(Reminder).where(
        and_(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id
        )
    )
    result = await db.execute(query)
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")

    await db.delete(reminder)
    await db.commit()
    return {"message": "已删除"}


@router.post("/habits/daily-reminder")
@limiter.limit("5/minute")
async def send_habit_daily_reminder(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发送今日习惯打卡提醒"""
    from app.services.wx_notifier import send_habit_reminder

    # 获取今日未完成的习惯
    query = select(Reminder).where(
        and_(
            Reminder.user_id == current_user.id,
            Reminder.entity_type == "habit",
            Reminder.is_sent == False
        )
    )
    result = await db.execute(query)
    reminders = result.scalars().all()

    sent_count = 0
    for reminder in reminders:
        if current_user.wx_openid:
            success = await send_habit_reminder(
                current_user.wx_openid,
                f"习惯提醒 #{reminder.id}"
            )
            if success:
                reminder.is_sent = True
                reminder.sent_at = datetime.utcnow()
                sent_count += 1

    await db.commit()
    return {"sent": sent_count, "total": len(reminders)}