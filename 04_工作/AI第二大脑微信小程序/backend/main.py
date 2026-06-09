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