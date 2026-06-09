# AI 开发生态系统 - Assistant 模块
"""
AI 助手模块：基于 18 层架构的智能开发助手

核心功能:
- 多角色支持 (Coordinator/Researcher/Coder/Reviewer/Executor)
- 记忆集成 (Qdrant 向量数据库)
- 工具调用 (Git/Docker/Security)
- 工作流编排

Usage:
    from src.assistant import Assistant, AIAgent, Role

    # 基础助手
    assistant = Assistant(role=Role.CODER)
    response = assistant.run("实现用户认证模块")

    # 智能 Agent
    agent = AIAgent(name="我的助手", role="coordinator")
    result = agent.execute("做个 AI 助手")
"""

import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field

from .base import Assistant, AIAgent, Message, MessageRole, Context
from .roles import Role, AgentConfig
from .config import AssistantConfig

__version__ = "1.1.0"

# Role 枚举
class Role(str, Enum):
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    DEBUGGER = "debugger"
    ARCHITECT = "architect"
    SECURITY = "security"

# Agent 配置
@dataclass
class AgentConfig:
    name: str
    role: Role
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    layers: List[str] = field(default_factory=list)

__all__ = [
    # 核心类
    "Assistant",
    "AIAgent",
    "Message",
    "MessageRole",
    "Context",

    # 角色和配置
    "Role",
    "AgentConfig",
    "AssistantConfig",

    # 版本
    "__version__",
]
