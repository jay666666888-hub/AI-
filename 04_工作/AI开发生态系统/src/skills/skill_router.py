#!/usr/bin/env python3
"""
Skill Router - 技能路由器 + 自动注册
根据任务类型自动路由到合适的 Skill、Agent 和 Layer
支持动态注册新组件
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import os
import importlib


class TaskType(Enum):
    """任务类型"""
    CREATE = "create"
    MODIFY = "modify"
    FIX = "fix"
    EXPLAIN = "explain"
    REFACTOR = "refactor"
    REVIEW = "review"
    TEST = "test"
    DEPLOY = "deploy"
    QUERY = "query"
    BUILD = "build"
    PLANNING = "planning"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    DEBUG = "debug"
    MONITOR = "monitor"
    UNKNOWN = "unknown"


@dataclass
class RouteRule:
    """路由规则"""
    task_type: TaskType
    keywords: List[str]
    recommended_skills: List[str]
    recommended_agents: List[str]
    recommended_layers: List[str]
    priority: int = 1


@dataclass
class ComponentRegistry:
    """组件注册表 - 支持动态注册"""
    skills: Dict[str, Any] = field(default_factory=dict)
    agents: Dict[str, Any] = field(default_factory=dict)
    layers: Dict[str, Any] = field(default_factory=dict)
    
    def register_skill(self, name: str, skill: Any) -> None:
        """注册 Skill"""
        self.skills[name] = skill
        
    def register_agent(self, name: str, agent: Any) -> None:
        """注册 Agent"""
        self.agents[name] = agent
        
    def register_layer(self, name: str, layer: Any) -> None:
        """注册 Layer"""
        self.layers[name] = layer
        
    def get_skill(self, name: str) -> Optional[Any]:
        return self.skills.get(name)
    
    def get_agent(self, name: str) -> Optional[Any]:
        return self.agents.get(name)
    
    def get_layer(self, name: str) -> Optional[Any]:
        return self.layers.get(name)
    
    def list_skills(self) -> List[str]:
        return list(self.skills.keys())
    
    def list_agents(self) -> List[str]:
        return list(self.agents.keys())
    
    def list_layers(self) -> List[str]:
        return list(self.layers.keys())


class SkillRouter:
    """
    技能路由器 - 支持动态注册
    根据任务内容自动选择合适的技能、Agent 和 Layer
    """

    DEFAULT_RULES = [
        # 基础任务类型
        RouteRule(TaskType.CREATE, ["创建", "新建", "开发", "实现", "做个", "create", "new", "implement"],
                  ["brainstorming", "writing_plans", "tdd", "build", "verification"],
                  ["planner", "code-architect"], ["L4_intent", "L5_planning", "L12_container", "L14_deploy"], 1),
        RouteRule(TaskType.FIX, ["修复", "修", "fix", "bug", "错误", "解决", "问题"],
                  ["systematic_debugging", "tdd", "verification"], ["build-error-resolver", "tdd-guide"],
                  ["L4_intent", "L9_testing", "L10_monitoring"], 1),
        RouteRule(TaskType.MODIFY, ["修改", "改动", "调整", "更新", "modify", "change", "update", "edit"],
                  ["brainstorming", "build", "verification"], ["planner", "code-reviewer"],
                  ["L4_intent", "L5_planning"], 1),
        RouteRule(TaskType.REFACTOR, ["重构", "优化", "重写", "refactor", "optimize"],
                  ["brainstorming", "verification", "code_review"], ["planner", "refactor-cleaner"],
                  ["L5_planning", "L9_review"], 2),
        RouteRule(TaskType.REVIEW, ["审查", "检查", "review", "audit", "检查代码"],
                  ["code_review", "verification"], ["code-reviewer", "security-reviewer"],
                  ["L9_review", "L8_security"], 1),
        RouteRule(TaskType.TEST, ["测试", "test", "单元测试", "e2e"],
                  ["tdd", "e2e_test"], ["tdd-guide", "e2e-runner"],
                  ["L9_testing", "L9_e2e", "L10_monitoring"], 1),
        RouteRule(TaskType.DEPLOY, ["部署", "上线", "发布", "deploy", "release"],
                  ["build", "verification", "e2e_test"], ["architect"],
                  ["L12_container", "L14_deploy", "L14_k8s", "L10_uptime"], 2),
        RouteRule(TaskType.EXPLAIN, ["解释", "说明", "什么是", "为什么", "explain", "what", "why"],
                  ["brainstorming"], ["code-explorer", "docs-lookup"], ["L3_memory"], 3),
        RouteRule(TaskType.BUILD, ["构建", "编译", "build", "compile"],
                  ["build", "verification"], ["build-error-resolver"], ["L12_container", "L14_deploy"], 1),
        RouteRule(TaskType.PLANNING, ["规划", "计划", "方案", "planning", "plan"],
                  ["brainstorming", "writing_plans"], ["planner", "gan-planner"], ["L5_planning"], 1),
        
        # 专业任务类型
        RouteRule(TaskType.SECURITY, ["安全", "漏洞", "密码", "security", "secret", "扫描"],
                  ["code_review"], ["security-reviewer", "opensource-sanitizer"], ["L8_security"], 1),
        RouteRule(TaskType.PERFORMANCE, ["性能", "优化", "speed", "performance", "优化"],
                  ["verification", "code_review"], ["performance-optimizer"], ["L10_monitoring"], 1),
        RouteRule(TaskType.DATABASE, ["数据库", "db", "sql", "query", "database"],
                  ["verification"], ["database-reviewer"], ["L11_knowledge"], 1),
        RouteRule(TaskType.FRONTEND, ["前端", "react", "vue", "html", "css", "frontend", "界面"],
                  ["tdd", "verification"], ["typescript-reviewer", "a11y-architect"], ["L15_frontend"], 1),
        RouteRule(TaskType.BACKEND, ["后端", "api", "server", "backend", "fastapi"],
                  ["tdd", "verification"], ["python-reviewer", "fastapi-reviewer"], ["L14_deploy"], 1),
        RouteRule(TaskType.DEVOPS, ["运维", "k8s", "docker", "ci/cd", "devops", "部署"],
                  ["build", "verification"], ["network-architect", "harness-optimizer"],
                  ["L12_container", "L14_k8s", "L10_uptime"], 1),
        RouteRule(TaskType.DEBUG, ["调试", "debug", "排错", "排除"],
                  ["systematic_debugging"], ["build-error-resolver", "silent-failure-hunter"],
                  ["L10_monitoring", "L4_intent"], 1),
        RouteRule(TaskType.MONITOR, ["监控", "monitor", "观测", "metrics", "日志"],
                  ["verification"], ["performance-optimizer"],
                  ["L10_monitoring", "L10_uptime"], 1),
        RouteRule(TaskType.QUERY, ["查询", "搜索", "query", "search", "find", "找"],
                  ["brainstorming"], ["code-explorer"],
                  ["L4_intent", "L3_memory"], 1),
    ]

    def __init__(self, skills: Dict[str, Any] = None):
        self.skills = skills or {}
        self.rules = self.DEFAULT_RULES.copy()
        self.custom_rules: List[RouteRule] = []
        self._agents_cache = None
        self._registry = ComponentRegistry()
        # 进化相关
        self._evolution_enabled = True
        self._evolution_skill = None

    @property
    def agents(self) -> Dict[str, Any]:
        if self._agents_cache is None:
            try:
                from .agent_registry import get_registry
                self._agents_cache = get_registry().agents
            except:
                self._agents_cache = {}
        return self._agents_cache

    def add_rule(self, rule: RouteRule) -> None:
        """添加自定义路由规则"""
        self.custom_rules.append(rule)

    def add_skill(self, name: str, skill: Any) -> None:
        """动态添加 Skill"""
        self.skills[name] = skill
        self._registry.register_skill(name, skill)

    def add_agent(self, name: str, agent: Any) -> None:
        """动态添加 Agent"""
        self.agents[name] = agent
        self._registry.register_agent(name, agent)

    def add_layer(self, name: str, layer: Any) -> None:
        """动态添加 Layer"""
        self.layers[name] = layer
        self._registry.register_layer(name, layer)

    def auto_discover_skills(self, package: str = "src.skills") -> List[str]:
        """自动发现并注册新 Skills"""
        import sys
        from pathlib import Path
        
        discovered = []
        try:
            # 获取 skills 目录
            skills_dir = Path(package.replace(".", "/"))
            if not skills_dir.exists():
                skills_dir = Path("src/skills")
            
            for py_file in skills_dir.glob("*_skill.py"):
                skill_name = py_file.stem
                if skill_name not in self.skills:
                    try:
                        module = importlib.import_module(f"{package}.{skill_name}")
                        # 查找 Skill 类
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and 
                                attr_name.endswith("Skill") and 
                                attr_name != "SkillRouter"):
                                self.add_skill(skill_name, attr())
                                discovered.append(skill_name)
                                break
                    except Exception as e:
                        print(f"  Failed to load {skill_name}: {e}")
        except Exception as e:
            print(f"Auto-discovery failed: {e}")
        
        return discovered

    def route(self, task: str) -> Dict[str, Any]:
        """路由任务"""
        task_lower = task.lower()
        matched_rules = []

        for rule in self.rules + self.custom_rules:
            matches = sum(1 for kw in rule.keywords if kw in task_lower)
            if matches > 0:
                matched_rules.append((rule, matches))

        matched_rules.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

        if not matched_rules:
            return self._unknown_route(task)

        best_rule = matched_rules[0][0]

        # 过滤可用的组件
        available_skills = [s for s in best_rule.recommended_skills if s in self.skills]
        available_agents = [a for a in best_rule.recommended_agents if a in self.agents]
        
        available_layers = [l for l in best_rule.recommended_layers if self._is_layer_available(l)]

        # 自适应调整 - 基于进化历史
        final_skills = self._adaptive_adjust(best_rule.recommended_skills, best_rule.task_type.value)
        
        return {
            "task_type": best_rule.task_type.value,
            "task": task,
            "recommended_skills": available_skills or final_skills,
            "recommended_agents": available_agents or best_rule.recommended_agents,
            "recommended_layers": available_layers or best_rule.recommended_layers,
            "confidence": min(matched_rules[0][1] * 0.3, 0.95),
            "routing_reason": f"匹配: {[kw for kw in best_rule.keywords if kw in task_lower]}",
            "all_agents_count": len(self.agents),
            "all_skills_count": len(self.skills),
            "all_layers_count": len(self._get_all_layers()),
            "pipeline": final_skills + best_rule.recommended_agents + best_rule.recommended_layers,
            "evolution_enabled": self._evolution_enabled
        }

    def _adaptive_adjust(self, skills: List[str], task_type: str) -> List[str]:
        """基于进化历史调整 skills 推荐"""
        if not self._evolution_enabled or not skills:
            return skills
        
        try:
            from .evolution_skill import get_evolution_skill
            evol = get_evolution_skill()
            return evol.get_adaptive_skills(skills, task_type)
        except:
            return skills

    def _is_layer_available(self, layer: str) -> bool:
        """检查 layer 是否可用"""
        # 可用的 layers
        available = [
            "L4_intent", "L5_planning", "L9_testing", "L9_review", "L9_e2e",
            "L10_monitoring", "L10_uptime", "L12_container", "L14_deploy",
            "L14_k8s", "L8_security", "L1_github", "L3_memory",
            "L15_frontend", "L16_creative", "L17_data", "L18_aiops"
        ]
        return layer in available

    def _get_all_layers(self) -> List[str]:
        """获取所有已注册的 layers"""
        return [
            "L4_intent", "L5_planning", "L9_testing", "L9_review", "L9_e2e",
            "L10_monitoring", "L10_uptime", "L12_container", "L14_deploy",
            "L14_k8s", "L8_security", "L1_github", "L3_memory",
            "L15_frontend", "L16_creative", "L17_data", "L18_aiops"
        ]

    def _unknown_route(self, task: str) -> Dict[str, Any]:
        return {
            "task_type": TaskType.UNKNOWN.value,
            "task": task,
            "recommended_skills": ["brainstorming"],
            "recommended_agents": ["planner"],
            "recommended_layers": ["L5_planning"],
            "confidence": 0.3,
            "routing_reason": "无匹配关键词，使用默认",
            "all_agents_count": len(self.agents),
            "all_skills_count": len(self.skills),
            "all_layers_count": len(self._get_all_layers()),
            "pipeline": ["brainstorming", "planner", "L5_planning"]
        }

    def route_batch(self, tasks: List[str]) -> List[Dict[str, Any]]:
        return [self.route(task) for task in tasks]

    def get_status(self) -> Dict[str, Any]:
        """获取路由系统状态"""
        return {
            "total_rules": len(self.rules),
            "custom_rules": len(self.custom_rules),
            "registered_skills": len(self.skills),
            "registered_agents": len(self.agents),
            "available_layers": len(self._get_all_layers()),
            "task_types_covered": len(set(r.task_type for r in self.rules)),
            "auto_discover_available": True
        }


def route_task(task: str, skills: Dict[str, Any] = None) -> Dict[str, Any]:
    """快捷路由函数"""
    router = SkillRouter(skills)
    return router.route(task)
