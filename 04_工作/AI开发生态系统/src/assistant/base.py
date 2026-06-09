#!/usr/bin/env python3
"""AI Assistant - 基类和消息模型"""
import os
import sys
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Context:
    """执行上下文"""
    task: str
    messages: List[Message] = field(default_factory=list)
    memory: Dict[str, Any] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    layers: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)

    def add_message(self, role: MessageRole, content: str, **metadata):
        """添加消息"""
        self.messages.append(Message(role=role, content=content, metadata=metadata))


class Assistant:
    """
    AI 助手基类
    基于 18 层架构，提供多角色支持
    """

    def __init__(
        self,
        role: str = "coder",
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        memory_enabled: bool = True,
        tools_enabled: bool = True
    ):
        self.role = role
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.memory_enabled = memory_enabled
        self.tools_enabled = tools_enabled
        self.context = Context(task="")
        self._skills = []
        self._layers = []
        self._skill_router = None
        self._init_skills()

    def _init_skills(self):
        """初始化 Skills"""
        try:
            from skills import (
                BrainstormingSkill, WritingPlansSkill, TDDGuideSkill,
                CodeReviewSkill, VerificationSkill, MemorySkill,
                SkillRouter
            )
            self._skills = {
                "brainstorming": BrainstormingSkill(),
                "planning": WritingPlansSkill(),
                "tdd": TDDGuideSkill(),
                "code_review": CodeReviewSkill(),
                "verification": VerificationSkill(),
                "memory": MemorySkill(),
            }
            # 初始化路由
            self._skill_router = SkillRouter(self._skills)
        except ImportError as e:
            print(f"警告: 技能模块加载失败: {e}")

    def set_task(self, task: str):
        """设置任务"""
        self.context.task = task
        self.context.add_message(MessageRole.USER, task)

    def run(self, task: str, **kwargs) -> str:
        """运行任务"""
        self.set_task(task)

        # 使用路由选择最佳技能
        if self._skill_router:
            route = self._skill_router.route(task)
            recommended_skills = route.get("recommended_skills", [])

            # 执行推荐的技能链
            results = []
            for skill_name in recommended_skills:
                if skill_name in self._skills:
                    skill = self._skills[skill_name]
                    if hasattr(skill, "run"):
                        result = skill.run(task)
                        results.append(f"{skill_name}: {result}")

            if results:
                return "\n".join(results)

        return f"[{self.role}] 处理任务: {task}"

    def chat(self, message: str) -> str:
        """对话"""
        self.context.add_message(MessageRole.USER, message)
        return f"[{self.role}] 回复: {message}"

    def get_context(self) -> Dict[str, Any]:
        """获取上下文"""
        return {
            "task": self.context.task,
            "messages": [m.to_dict() for m in self.context.messages],
            "role": self.role,
            "model": self.model
        }

    def brainstorm(self, topic: str) -> str:
        """头脑风暴"""
        if "brainstorming" in self._skills:
            return self._skills["brainstorming"].run(topic)
        return f"头脑风暴: {topic}"

    def create_plan(self, goal: str, tasks: List[str] = None) -> Dict[str, Any]:
        """创建计划"""
        if "planning" in self._skills:
            return self._skills["planning"].create_plan(goal, "", tasks or [])
        return {"goal": goal, "tasks": tasks or []}

    def review_code(self, code: str) -> Dict[str, Any]:
        """代码审查"""
        if "code_review" in self._skills:
            return self._skills["code_review"].review(code)
        return {"status": "no_review", "code": code[:100]}

    def verify(self, code: str) -> Dict[str, Any]:
        """验证代码"""
        if "verification" in self._skills:
            return self._skills["verification"].verify(code)
        return {"status": "verified"}


class AIAgent(Assistant):
    """
    AI Agent - 智能代理
    基于 18 层架构，支持完整工作流
    """

    def __init__(self, name: str = "agent", role: str = "coordinator", **kwargs):
        super().__init__(role=role, **kwargs)
        self.name = name
        self._orchestrator = None
        self._memory_store = []

    def load_orchestrator(self):
        """加载编排器"""
        try:
            from src.ecosystem_orchestrator import EcosystemOrchestrator
            self._orchestrator = EcosystemOrchestrator()
            self._orchestrator.load_adapters()
        except ImportError as e:
            print(f"警告: 编排器加载失败: {e}")

    def execute(self, task: str) -> Dict[str, Any]:
        """执行任务"""
        self.set_task(task)

        result = {
            "task": task,
            "agent": self.name,
            "role": self.role,
            "context": self.get_context(),
            "memory": self._memory_store.copy(),
        }

        # 如果有编排器，执行完整工作流
        if self._orchestrator:
            route = self._orchestrator.route_task(task)
            result["route"] = route

            # 执行工作流
            workflow_result = self._orchestrator.run_workflow(task, mode="auto")
            result["workflow"] = workflow_result
        else:
            # 使用内置技能
            result["output"] = self.run(task)

        # 保存到记忆
        self._memory_store.append({
            "task": task,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        return result

    def remember(self, key: str, value: Any) -> None:
        """保存记忆"""
        self._memory_store.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })

    def recall(self, key: str) -> Optional[Any]:
        """回忆记忆"""
        for mem in reversed(self._memory_store):
            if mem.get("key") == key:
                return mem.get("value")
        return None
