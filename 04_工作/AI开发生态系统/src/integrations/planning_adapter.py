#!/usr/bin/env python3
"""
Planning Adapter - 规划推理层集成
L5 规划推理层
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Task:
    id: str
    description: str
    priority: int
    status: str
    depends_on: List[str]
    tags: List[str]
    created_at: str
    updated_at: str


@dataclass
class Plan:
    id: str
    title: str
    description: str
    tasks: List[Task]
    phase: str
    created_at: str
    updated_at: str


class BeadsAdapter:
    """Beads 任务管理适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.beads_dir = os.path.join(self.project_path, ".beads")
        self.tasks_file = os.path.join(self.beads_dir, "tasks.json")

    def _ensure_beads_dir(self) -> None:
        Path(self.beads_dir).mkdir(parents=True, exist_ok=True)

    def list_tasks(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.tasks_file):
            return []
        with open(self.tasks_file, "r", encoding="utf-8") as f:
            return json.load(f).get("tasks", [])

    def add_task(self, description: str, priority: int = 3,
                 tags: List[str] = None) -> Dict[str, Any]:
        self._ensure_beads_dir()
        tasks = self.list_tasks()
        task_id = f"task-{len(tasks) + 1:03d}"

        task = Task(
            id=task_id,
            description=description,
            priority=priority,
            status="pending",
            depends_on=[],
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        tasks.append(asdict(task))
        self._save_tasks(tasks)
        return asdict(task)

    def complete_task(self, task_id: str) -> bool:
        tasks = self.list_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["updated_at"] = datetime.now().isoformat()
                break
        self._save_tasks(tasks)
        return True

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        tasks = self.list_tasks()
        return [t for t in tasks if t["status"] == "pending"]

    def _save_tasks(self, tasks: List[Dict]) -> None:
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks, "updated_at": datetime.now().isoformat()}, f, indent=2)


class OpenSpecAdapter:
    """OpenSpec Spec 驱动开发框架适配器"""

    def __init__(self, spec_path: str = None):
        self.spec_path = spec_path or ".openspec"
        Path(self.spec_path).mkdir(parents=True, exist_ok=True)

    def create_spec(self, name: str, description: str,
                   requirements: List[str]) -> Dict[str, Any]:
        spec = {
            "name": name,
            "description": description,
            "version": "1.0.0",
            "requirements": requirements,
            "created_at": datetime.now().isoformat(),
            "files": []
        }
        spec_file = os.path.join(self.spec_path, f"{name}.md")
        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(f"# {name}\n\n{description}\n\n## Requirements\n\n")
            for i, req in enumerate(requirements, 1):
                f.write(f"{i}. {req}\n")
        return spec


class RalphImportAdapter:
    """Ralph PRD 导入适配器"""

    def __init__(self, ralph_path: str = "/home/admin1/.claude/plugins/marketplaces/ralph-claude-code"):
        self.ralph_path = ralph_path
        self.import_script = os.path.join(ralph_path, "ralph_import.sh")

    def import_prd(self, prd_path: str) -> List[Dict[str, Any]]:
        """从 PRD 导入任务"""
        if not os.path.exists(self.import_script):
            return self._fallback_import(prd_path)

        import subprocess
        result = subprocess.run(
            [self.import_script, prd_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return self._parse_tasks_from_output(result.stdout)
        return self._fallback_import(prd_path)

    def _fallback_import(self, prd_path: str) -> List[Dict[str, Any]]:
        """降级解析：当 ralph_import 不可用时"""
        tasks = []
        with open(prd_path, "r", encoding="utf-8") as f:
            content = f.read()

        task_pattern = r'-\s*\[?\s*\]?\s*(.+)'
        matches = re.findall(task_pattern, content)

        for i, match in enumerate(matches, 1):
            task_text = match.strip()
            if task_text:
                tasks.append({
                    "id": f"task-{i:03d}",
                    "description": task_text,
                    "priority": min(i, 5),
                    "status": "pending"
                })
        return tasks

    def _parse_tasks_from_output(self, output: str) -> List[Dict[str, Any]]:
        tasks = []
        for i, line in enumerate(output.splitlines(), 1):
            if line.strip().startswith("-"):
                task_text = line.strip().lstrip("- ").strip()
                if task_text:
                    tasks.append({
                        "id": f"task-{i:03d}",
                        "description": task_text,
                        "priority": min(i, 5),
                        "status": "pending"
                    })
        return tasks


class PlanningAdapter:
    """规划推理层统一适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.beads = BeadsAdapter(project_path)
        self.openspec = OpenSpecAdapter(
            os.path.join(self.project_path, ".openspec")
        )
        self.ralph_import = RalphImportAdapter()

    def create_plan(self, title: str, description: str,
                    tasks: List[str]) -> Plan:
        plan_id = f"plan-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        plan_tasks = []

        for i, task_desc in enumerate(tasks, 1):
            task = Task(
                id=f"{plan_id}-task-{i:02d}",
                description=task_desc,
                priority=min(i, 5),
                status="pending",
                depends_on=[],
                tags=["planned"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            plan_tasks.append(task)

        return Plan(
            id=plan_id,
            title=title,
            description=description,
            tasks=plan_tasks,
            phase="planning",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    def export_plan(self, plan: Plan, format: str = "json") -> Dict:
        plan_dict = asdict(plan)
        if format == "json":
            return plan_dict
        elif format == "markdown":
            md = f"# {plan.title}\n\n{plan.description}\n\n## Tasks\n\n"
            for task in plan.tasks:
                status_icon = "DONE" if task.status == "completed" else "TODO"
                md += f"- [{status_icon}] {task.description} (P{task.priority})\n"
            return {"markdown": md}
        return plan_dict