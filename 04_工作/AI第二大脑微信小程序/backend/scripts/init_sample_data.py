#!/usr/bin/env python3
"""示例数据初始化脚本
运行: python3 scripts/init_sample_data.py <user_id>

注意: 需要先通过微信登录获取 user_id
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.models import Task, Project, Note
from uuid import uuid4

engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def create_sample_data(user_id):
    async with async_session() as db:
        projects = [
            Project(id=str(uuid4()), user_id=user_id, name="AI 第二大脑开发", description="微信小程序和后端开发项目", color="#3B82F6", status="active"),
            Project(id=str(uuid4()), user_id=user_id, name="学习提升", description="个人学习和成长计划", color="#10B981", status="active")
        ]
        for p in projects:
            db.add(p)

        tasks = [
            Task(id=str(uuid4()), user_id=user_id, type="todo", title="完成任务列表页面", detail="修复任务筛选bug，优化UI", status="active", priority="high"),
            Task(id=str(uuid4()), user_id=user_id, type="todo", title="配置微信提醒", detail="获取template_id并配置", status="pending", priority="medium"),
            Task(id=str(uuid4()), user_id=user_id, type="habit", title="每日阅读", detail="每天阅读30分钟", status="active", frequency="daily", execution_mode="free"),
            Task(id=str(uuid4()), user_id=user_id, type="habit", title="晨间冥想", detail="早上冥想10分钟", status="active", frequency="daily", execution_mode="timed", scheduled_time="07:00")
        ]
        for t in tasks:
            db.add(t)

        notes = [
            Note(id=str(uuid4()), user_id=user_id, content="GitHub Webhook 配置完成，每次推送自动部署", source="manual"),
            Note(id=str(uuid4()), user_id=user_id, content="习惯打卡功能已上线，每天22:00提醒", source="manual")
        ]
        for n in notes:
            db.add(n)

        await db.commit()
        print(f"Created {len(projects)} projects, {len(tasks)} tasks, {len(notes)} notes")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/init_sample_data.py <user_id>")
        sys.exit(1)
    asyncio.run(create_sample_data(sys.argv[1]))
