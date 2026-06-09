#!/usr/bin/env python3
"""
Agent Registry - Claude Code Agents 注册表
自动发现并注册所有 agents 和 skills
"""

import os
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentInfo:
    """Agent 信息"""
    name: str
    description: str
    tools: List[str]
    model: str
    file_path: str
    tags: List[str]


class AgentRegistry:
    """
    Agent 注册表
    自动扫描 ~/.claude/agents/ 下所有 agent
    """

    AGENTS_DIR = os.path.expanduser("~/.claude/agents")

    # 任务类型到 Agent 的映射
    TASK_AGENT_MAPPING = {
        "create": ["planner", "code-architect"],
        "fix": ["build-error-resolver", "tdd-guide"],
        "refactor": ["planner", "refactor-cleaner"],
        "review": ["code-reviewer", "security-reviewer"],
        "test": ["tdd-guide", "e2e-runner"],
        "deploy": ["architect", "planner"],
        "explain": ["code-explorer", "docs-lookup"],
        "performance": ["performance-optimizer"],
        "security": ["security-reviewer"],
        "database": ["database-reviewer"],
        "architecture": ["architect", "code-architect"],
        "planning": ["planner", "gan-planner"],
        "build": ["build-error-resolver"],
        "debug": ["build-error-resolver", "silent-failure-hunter"],
        "frontend": ["typescript-reviewer", "a11y-architect"],
        "backend": ["python-reviewer", "fastapi-reviewer"],
        "mobile": ["kotlin-reviewer", "swift-reviewer"],
        "devops": ["network-architect", "harness-optimizer"],
        "security_audit": ["security-reviewer", "opensource-sanitizer"],
        "open_source": ["opensource-forker", "opensource-packager"],
    }

    def __init__(self):
        self.agents: Dict[str, AgentInfo] = {}
        self._scan_agents()

    def _scan_agents(self):
        """扫描所有 agents"""
        agents_dir = Path(self.AGENTS_DIR)
        if not agents_dir.exists():
            return

        for agent_file in agents_dir.glob("*.md"):
            try:
                agent_info = self._parse_agent(agent_file)
                if agent_info:
                    self.agents[agent_info.name] = agent_info
            except Exception:
                pass

    def _parse_agent(self, file_path: Path) -> Optional[AgentInfo]:
        """解析 agent 文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析 frontmatter
        name = file_path.stem
        description = ""
        tools = []
        model = "sonnet"
        tags = []

        # 提取 description
        desc_match = re.search(r"description:\s*(.+)", content)
        if desc_match:
            description = desc_match.group(1).strip()

        # 提取 tools
        tools_match = re.search(r"tools:\s*\[(.*?)\]", content, re.DOTALL)
        if tools_match:
            tools = [t.strip().strip('"') for t in tools_match.group(1).split(",")]

        # 提取 model
        model_match = re.search(r"model:\s*(\w+)", content)
        if model_match:
            model = model_match.group(1)

        # 提取 tags
        tag_matches = re.findall(r"tags:\s*\[(.*?)\]", content, re.DOTALL)
        if tag_matches:
            tags = [t.strip().strip('"') for t in tag_matches[0].split(",")]

        return AgentInfo(
            name=name,
            description=description,
            tools=tools,
            model=model,
            file_path=str(file_path),
            tags=tags
        )

    def get_agent(self, name: str) -> Optional[AgentInfo]:
        """获取指定 agent"""
        return self.agents.get(name)

    def get_agents_for_task(self, task_type: str) -> List[AgentInfo]:
        """获取任务类型对应的 agents"""
        agent_names = self.TASK_AGENT_MAPPING.get(task_type, [])
        return [self.agents[name] for name in agent_names if name in self.agents]

    def search_agents(self, query: str) -> List[AgentInfo]:
        """搜索 agents"""
        query_lower = query.lower()
        results = []
        for agent in self.agents.values():
            if (query_lower in agent.name.lower() or
                query_lower in agent.description.lower() or
                any(query_lower in tag for tag in agent.tags)):
                results.append(agent)
        return results

    def get_all_agents(self) -> List[AgentInfo]:
        """获取所有 agents"""
        return list(self.agents.values())

    def get_count(self) -> int:
        """获取 agent 总数"""
        return len(self.agents)


# 快捷函数
def get_registry() -> AgentRegistry:
    """获取全局注册表"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


_agent_registry = None


def find_agents_for_task(task: str) -> List[Dict[str, Any]]:
    """根据任务找到合适的 agents"""
    registry = get_registry()

    # 先用路由判断任务类型
    from .skill_router import SkillRouter
    router = SkillRouter()
    route = router.route(task)

    task_type = route["task_type"]

    # 获取对应的 agents
    agents = registry.get_agents_for_task(task_type)

    return [
        {
            "name": a.name,
            "description": a.description,
            "model": a.model,
            "tools": a.tools
        }
        for a in agents
    ]


def list_all_agents() -> List[str]:
    """列出所有 agent 名称"""
    return list(get_registry().agents.keys())
