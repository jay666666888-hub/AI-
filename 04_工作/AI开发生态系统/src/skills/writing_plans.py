#!/usr/bin/env python3
"""
Writing Plans Skill - 任务规划
基于 Superpowers methodology
把大任务拆解成 2-5 分钟的小任务
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PlanTask:
    """计划任务"""
    id: str
    description: str
    file_path: str  # 具体文件路径
    verification_step: str  # 如何验证完成
    estimated_minutes: int
    priority: int
    status: str = "pending"  # pending, in_progress, completed, blocked
    depends_on: List[str] = None  # 依赖的任务 ID


class WritingPlansSkill:
    """
    writing-plans skill - 任务拆解
    
    工作流程:
    1. 分析需求
    2. 拆解成小任务 (每个 2-5 分钟)
    3. 每个任务有具体文件路径和验证步骤
    4. 输出可执行的任务列表
    """

    def __init__(self):
        self.tasks: List[PlanTask] = []

    def breakdown_task(self, requirement: str, context: Dict[str, Any] = None) -> List[PlanTask]:
        """
        拆解任务
        
        Args:
            requirement: 用户需求
            context: 上下文信息
            
        Returns:
            任务列表
        """
        tasks = []
        context = context or {}
        task_id = 1
        
        # 通用流程拆解
        base_tasks = [
            ("调研需求", "research", 2, 1, []),
            ("编写规格文档", "spec", 3, 2, ["research"]),
            ("创建测试文件", "test", 2, 3, ["spec"]),
            ("实现核心功能", "implement", 5, 4, ["spec"]),
            ("运行测试验证", "verify", 2, 5, ["implement"]),
            ("代码审查", "review", 3, 6, ["verify"]),
            ("修复问题", "fix", 2, 7, ["review"]),
            ("最终验证", "final", 2, 8, ["fix"]),
        ]
        
        for desc, task_type, mins, priority, depends in base_tasks:
            task = PlanTask(
                id=f"task-{task_id:03d}",
                description=desc,
                file_path=self._get_file_path(task_type, context),
                verification_step=self._get_verification(task_type, desc),
                estimated_minutes=mins,
                priority=priority,
                depends_on=depends,
                status="pending"
            )
            tasks.append(task)
            task_id += 1
        
        self.tasks = tasks
        return tasks

    def _get_file_path(self, task_type: str, context: Dict) -> str:
        """获取任务对应的文件路径"""
        file_map = {
            "research": "docs/research.md",
            "spec": "docs/spec.md",
            "test": "tests/test_feature.py",
            "implement": "src/feature.py",
            "verify": "tests/test_feature.py",
            "review": "src/feature.py",
            "fix": "src/feature.py",
            "final": "README.md"
        }
        return file_map.get(task_type, "src/")

    def _get_verification(self, task_type: str, description: str) -> str:
        """获取验证步骤"""
        verify_map = {
            "research": "确认需求文档已创建",
            "spec": "确认规格文档包含所有用例",
            "test": "确认测试文件可运行 `pytest tests/ -v`",
            "implement": "确认代码编译通过，flake8 通过",
            "verify": "确认所有测试通过 `pytest -v`",
            "review": "确认代码审查通过",
            "fix": "确认问题已修复",
            "final": "确认功能完整可用"
        }
        return verify_map.get(task_type, "人工验证")

    def format_tasks_for_user(self) -> str:
        """格式化任务列表"""
        output = "📋 任务计划:\n\n"
        for task in self.tasks:
            status_icon = {"pending": "⬜", "in_progress": "🔄", "completed": "✅", "blocked": "🚫"}.get(task.status, "⬜")
            deps = f" (依赖: {', '.join(task.depends_on)})" if task.depends_on else ""
            output += f"{status_icon} **{task.id}** {task.description}\n"
            output += f"   📁 {task.file_path}\n"
            output += f"   ✅ {task.verification_step}\n"
            output += f"   ⏱️ {task.estimated_minutes} 分钟\n"
            output += f"   📊 优先级: {task.priority}{deps}\n\n"
        return output

    def get_ready_tasks(self) -> List[PlanTask]:
        """获取可执行的任务（依赖已完成的）"""
        completed_ids = {t.id for t in self.tasks if t.status == "completed"}
        ready = []
        for task in self.tasks:
            if task.status == "pending":
                deps_done = all(d in completed_ids for d in task.depends_on)
                if not task.depends_on or deps_done:
                    ready.append(task)
        return ready

    def mark_completed(self, task_id: str) -> None:
        """标记任务完成"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = "completed"

    def get_next_task(self) -> Optional[PlanTask]:
        """获取下一个可执行任务"""
        ready = self.get_ready_tasks()
        return ready[0] if ready else None

    def run(self, requirement: str, context: Dict = None) -> Dict[str, Any]:
        """运行 writing-plans skill"""
        tasks = self.breakdown_task(requirement, context)
        ready = self.get_ready_tasks()
        
        return {
            "status": "plan_ready",
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks if t.status == "pending"]),
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "file_path": t.file_path,
                    "verification": t.verification_step,
                    "minutes": t.estimated_minutes,
                    "priority": t.priority,
                    "depends_on": t.depends_on,
                    "status": t.status
                }
                for t in tasks
            ],
            "next_task": ready[0].id if ready else None,
            "message": self.format_tasks_for_user()
        }


def run_writing_plans(requirement: str) -> Dict[str, Any]:
    """快捷函数"""
    skill = WritingPlansSkill()
    return skill.run(requirement)


if __name__ == "__main__":
    result = run_writing_plans("做个用户登录功能")
    print(result["message"])
