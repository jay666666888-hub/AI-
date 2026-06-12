"""
提醒调度器 - 检查并发送到期提醒
Python 3.6.8 compatible version
"""
import asyncio
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.models import Reminder, User, Task
from app.services.wx_notifier import send_reminder_notification

engine = create_async_engine(settings.DATABASE_URL)
# Use sessionmaker with AsyncSession as replacement for async_sessionmaker
async_session_local = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def check_and_send_reminders():
    """检查并发送到期提醒"""
    now = datetime.utcnow()

    async with async_session_local() as db:
        # 查询未发送且到期的提醒
        query = select(Reminder).where(
            and_(
                Reminder.is_sent == False,
                Reminder.remind_at <= now
            )
        )
        result = await db.execute(query)
        reminders = result.scalars().all()

        for reminder in reminders:
            try:
                # 获取用户信息
                user_query = select(User).where(User.id == reminder.user_id)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()

                if not user or not user.wx_openid:
                    continue

                # 获取关联实体信息
                entity_title = "任务提醒"
                if reminder.entity_type == "task" and reminder.entity_id:
                    task_query = select(Task).where(Task.id == reminder.entity_id)
                    task_result = await db.execute(task_query)
                    task = task_result.scalar_one_or_none()
                    if task:
                        entity_title = task.title

                # 发送微信通知
                success = await send_reminder_notification(
                    wx_openid=user.wx_openid,
                    title=entity_title,
                    remind_time=reminder.remind_at.strftime("%Y-%m-%d %H:%M")
                )

                if success:
                    reminder.is_sent = True
                    reminder.sent_at = datetime.utcnow()
                    await db.commit()
                    print(f"[ReminderScheduler] Sent reminder {reminder.id}")
                else:
                    print(f"[ReminderScheduler] Failed to send reminder {reminder.id}")

            except Exception as e:
                print(f"[ReminderScheduler] Error processing reminder {reminder.id}: {e}")
                continue

async def run_scheduler():
    """运行调度器 - 每分钟检查一次"""
    print("[ReminderScheduler] Starting scheduler...")
    while True:
        try:
            await check_and_send_reminders()
        except Exception as e:
            print(f"[ReminderScheduler] Scheduler error: {e}")
        await asyncio.sleep(60)  # 每分钟检查一次

def start_scheduler():
    """启动调度器（在应用启动时调用）"""
    loop = asyncio.get_event_loop()
    loop.create_task(run_scheduler())