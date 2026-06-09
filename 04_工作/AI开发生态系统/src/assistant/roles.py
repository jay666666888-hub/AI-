#!/usr/bin/env python3
"""AI Assistant - 角色定义"""
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field


class Role(str, Enum):
    """AI 助手角色"""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    CODER = "coder"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    DEBUGGER = "debugger"
    ARCHITECT = "architect"
    SECURITY = "security"


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    role: Role
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    layers: List[str] = field(default_factory=list)


ROLE_DESCRIPTIONS = {
    Role.COORDINATOR: "协调者 - 负责任务分配和流程协调",
    Role.RESEARCHER: "研究员 - 负责信息收集和分析",
    Role.CODER: "编码者 - 负责代码实现",
    Role.REVIEWER: "审查者 - 负责代码审查和质量把控",
    Role.EXECUTOR: "执行者 - 负责任务执行和验证",
    Role.DEBUGGER: "调试者 - 负责问题定位和修复",
    Role.ARCHITECT: "架构师 - 负责系统设计和架构决策",
    Role.SECURITY: "安全专家 - 负责安全分析和漏洞修复",
}


def get_role_description(role: Role) -> str:
    return ROLE_DESCRIPTIONS.get(role, "未知角色")


def create_agent_config(name: str, role: Role, **kwargs) -> AgentConfig:
    return AgentConfig(name=name, role=role, **kwargs)
