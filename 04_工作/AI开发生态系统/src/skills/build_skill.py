#!/usr/bin/env python3
"""
Build Skill - 增量实现技能
真实创建源代码文件
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import os
import re


class BuildPhase(Enum):
    PLAN = "plan"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    REFACTOR = "refactor"


@dataclass
class BuildTask:
    description: str
    file_path: str
    status: str
    dependencies: List[str]
    verification: str
    code_template: str = ""


class BuildSkill:
    """增量构建技能 - 真实创建源代码文件"""

    def __init__(self):
        self.tasks: List[BuildTask] = []
        self.current_phase = BuildPhase.PLAN
        self.project_path = "/mnt/e/黑曜石/04_工作/AI开发生态系统"
        self.created_files: List[str] = []

    def create_plan(self, goal: str, tasks: List[str]) -> Dict[str, Any]:
        """创建构建计划并真实生成代码文件"""
        self.tasks = []
        self.created_files = []

        for i, task_desc in enumerate(tasks, 1):
            file_path = self._extract_file_path(task_desc)
            code_template = self._generate_code_template(task_desc, file_path)

            task = BuildTask(
                description=task_desc,
                file_path=file_path,
                status="pending",
                dependencies=[],
                verification=self._create_verification(task_desc),
                code_template=code_template
            )
            self.tasks.append(task)

        for i, task in enumerate(self.tasks):
            if i > 0:
                task.dependencies = [self.tasks[i-1].description]

        for task in self.tasks:
            if task.file_path and task.code_template:
                self._write_file_if_not_exists(task.file_path, task.code_template)
                self.created_files.append(task.file_path)

        return {
            "goal": goal,
            "phases": ["PLAN", "IMPLEMENT", "VERIFY", "REFACTOR"],
            "tasks": [{"id": i, "description": t.description, "file": t.file_path, "status": t.status}
                      for i, t in enumerate(self.tasks)],
            "next_phase": BuildPhase.IMPLEMENT.value,
            "created_files": self.created_files
        }

    def _extract_file_path(self, description: str) -> str:
        paths = re.findall(r"src/[\w/]+\.py", description)
        return paths[0] if paths else ""

    def _create_verification(self, description: str) -> str:
        if "test" in description.lower():
            return "运行测试验证"
        elif "api" in description.lower():
            return "验证端点响应"
        return "代码审查通过"

    def _generate_code_template(self, description: str, file_path: str) -> str:
        desc_lower = description.lower()
        module_name = file_path.replace('.py', '').split('/')[-1] if file_path else "module"
        class_name = ''.join(word.capitalize() for word in re.findall(r'[a-zA-Z]+', module_name)) or "NewClass"

        templates = {
            'adapter': f'''#!/usr/bin/env python3
"""
{class_name} Adapter
自动生成 by BuildSkill
"""

from typing import Dict, Any


class {class_name}Adapter:
    def __init__(self):
        self.config = {{}}
        self.initialized = False

    def initialize(self, config: Dict[str, Any] = None) -> bool:
        if config:
            self.config.update(config)
        self.initialized = True
        return True

    def connect(self) -> bool:
        return self.initialized

    def execute(self, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        return {{"status": "success", "action": action}}

    def get_status(self) -> Dict[str, Any]:
        return {{"initialized": self.initialized}}
''',
            'skill': f'''#!/usr/bin/env python3
"""
{class_name} Skill
自动生成 by BuildSkill
"""

from typing import Dict, Any


class {class_name}Skill:
    def __init__(self):
        self.state = None
        self.history = []

    def run(self, input_data: Any) -> Dict[str, Any]:
        result = {{"status": "success", "output": None}}
        self.history.append({{"input": input_data, "output": result}})
        return result

    def get_status(self) -> Dict[str, Any]:
        return {{"status": "active", "history_count": len(self.history)}}
''',
            'manager': f'''#!/usr/bin/env python3
"""
{class_name} Manager
自动生成 by BuildSkill
"""

from typing import Dict, Any, List, Optional


class {class_name}Manager:
    def __init__(self):
        self.items: Dict[str, Any] = {{}}

    def add(self, key: str, value: Any) -> bool:
        self.items[key] = value
        return True

    def get(self, key: str) -> Optional[Any]:
        return self.items.get(key)

    def remove(self, key: str) -> bool:
        if key in self.items:
            del self.items[key]
            return True
        return False

    def list_all(self) -> List[str]:
        return list(self.items.keys())

    def get_status(self) -> Dict[str, Any]:
        return {{"count": len(self.items)}}
''',
            'api': f'''#!/usr/bin/env python3
"""
{class_name} API
自动生成 by BuildSkill
"""

from typing import Dict, Any
from dataclasses import dataclass


class {class_name}API:
    def __init__(self):
        self.endpoints = {{}}

    def register(self, action: str, handler):
        self.endpoints[action] = handler

    def handle(self, request) -> Dict[str, Any]:
        if request.action in self.endpoints:
            return {{"status": "success", "result": self.endpoints[request.action](request.params)}}
        return {{"status": "error", "message": "Unknown action"}}

    def get_status(self) -> Dict[str, Any]:
        return {{"endpoints": list(self.endpoints.keys())}}
''',
            'workflow': f'''#!/usr/bin/env python3
"""
{class_name} Workflow
自动生成 by BuildSkill
"""

from typing import Dict, Any
from enum import Enum


class {class_name}Phase(Enum):
    START = "start"
    PROCESS = "process"
    COMPLETE = "complete"


class {class_name}Workflow:
    def __init__(self):
        self.phase = {class_name}Phase.START
        self.context = {{}}

    def execute(self, input_data: Any) -> Dict[str, Any]:
        self.phase = {class_name}Phase.PROCESS
        result = {{"status": "success", "phase": self.phase.value}}
        self.phase = {class_name}Phase.COMPLETE
        return result

    def get_status(self) -> Dict[str, Any]:
        return {{"phase": self.phase.value}}
'''
        }

        for key, template in templates.items():
            if key in desc_lower:
                return template

        return f'''#!/usr/bin/env python3
"""
{class_name}
自动生成 by BuildSkill
"""

from typing import Dict, Any


class {class_name}:
    def __init__(self):
        self.data = {{}}

    def process(self, input_data: Any) -> Dict[str, Any]:
        return {{"status": "success"}}

    def get_status(self) -> Dict[str, Any]:
        return {{"initialized": True}}
'''

    def _write_file_if_not_exists(self, file_path: str, content: str) -> bool:
        try:
            full_path = os.path.join(self.project_path, file_path)
            if os.path.exists(full_path):
                return False
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📝 创建文件: {file_path}")
            return True
        except Exception as e:
            print(f"  ❌ 创建文件失败 {file_path}: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_tasks": len(self.tasks),
            "completed": sum(1 for t in self.tasks if t.status == "done"),
            "created_files": self.created_files
        }


def run_build(goal: str, tasks: List[str]) -> Dict[str, Any]:
    skill = BuildSkill()
    return skill.create_plan(goal, tasks)
