from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.api import auth, tasks, projects, notes, notifications
from app.api import reminders, daily_logs, memories, audit
from app.core.logging import logger

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.APP_NAME)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])
app.include_router(projects.router, prefix="/api/projects", tags=["项目"])
app.include_router(notes.router, prefix="/api/notes", tags=["笔记"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["通知"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["提醒"])
app.include_router(daily_logs.router, prefix="/api/daily-logs", tags=["时间线"])
app.include_router(memories.router, prefix="/api/memories", tags=["记忆库"])
app.include_router(audit.router, prefix="/api", tags=["审计"])

@app.on_event("startup")
async def startup_event():
    """启动时运行调度器"""
    logger.info("Application starting...")
    print("[Startup] Starting reminder scheduler...")
    from app.services.reminder_scheduler import start_scheduler
    start_scheduler()
    print("[Startup] Reminder scheduler started")
    logger.info("Application started successfully")

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}