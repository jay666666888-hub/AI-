"""
AI 开发生态系统 - Skills
基于 Superpowers methodology + everything-claude-code 模式
整合 11 Skills + 58 Agents + 17 Layers + 智能路由
"""

from .brainstorming import BrainstormingSkill, run_brainstorming
from .writing_plans import WritingPlansSkill, run_writing_plans
from .systematic_debugging import SystematicDebuggingSkill, run_debugging
from .gateguard import GateGuardSkill, GateDecision, run_gateguard
from .agent_loop import ContinuousAgentLoop, run_agent_loop
from .tdd_skill import TDDGuideSkill, run_tdd
from .code_review_skill import CodeReviewSkill, run_code_review
from .verification_skill import VerificationSkill, run_verification
from .build_skill import BuildSkill, run_build
from .memory_skill import MemorySkill, run_memory
from .e2e_skill import E2ETestSkill, run_e2e_test
from .agent_registry import AgentRegistry, get_registry, find_agents_for_task, list_all_agents
from .skill_router import SkillRouter, TaskType, route_task, RouteRule, ComponentRegistry

__all__ = [
    # Superpowers workflow
    "BrainstormingSkill", "run_brainstorming",
    "WritingPlansSkill", "run_writing_plans",
    "SystematicDebuggingSkill", "run_debugging",
    
    # Superpowers TDD
    "TDDGuideSkill", "run_tdd",
    
    # Superpowers Code Review
    "CodeReviewSkill", "run_code_review",
    
    # Superpowers Verification
    "VerificationSkill", "run_verification",
    
    # Superpowers Build
    "BuildSkill", "run_build",
    
    # Superpowers E2E Test
    "E2ETestSkill", "run_e2e_test",
    
    # ECC Memory
    "MemorySkill", "run_memory",
    
    # everything-claude-code patterns
    "GateGuardSkill", "GateDecision", "run_gateguard",
    "ContinuousAgentLoop", "run_agent_loop",
    
    # Agent Registry (58 Claude Code Agents)
    "AgentRegistry", "get_registry", "find_agents_for_task", "list_all_agents",
    
    # Skill Router (智能路由 + 自动注册)
    "SkillRouter", "TaskType", "route_task", "RouteRule", "ComponentRegistry",
]
