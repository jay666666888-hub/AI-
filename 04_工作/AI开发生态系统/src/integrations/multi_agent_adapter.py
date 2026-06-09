#!/usr/bin/env python3
"""
Multi-Agent Adapter - 多Agent协调层集成
L2 多Agent协调层
支持 CrewAI, gstack, 自定义Agent编排
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    """Agent 角色"""
    COORDINATOR = "coordinator"    # 协调者
    PLANNER = "planner"            # 规划者
    EXECUTOR = "executor"          # 执行者
    REVIEWER = "reviewer"          # 审查者
    RESEARCHER = "researcher"      # 研究者
    CODER = "coder"               # 开发者
    TESTER = "tester"             # 测试者
    DEPLOYER = "deployer"          # 部署者
    MONITOR = "monitor"              # 监控者


@dataclass
class AgentTask:
    """Agent 任务"""
    id: str
    role: AgentRole
    description: str
    input_data: Any
    dependencies: List[str] = None
    status: str = "pending"  # pending, running, completed, failed


@dataclass
class AgentResult:
    """Agent 执行结果"""
    agent_id: str
    role: AgentRole
    status: str
    output: Any
    error: str = ""
    duration_ms: int = 0


class BaseAgent:
    """Agent 基类"""

    def __init__(self, name: str, role: AgentRole, description: str = ""):
        self.name = name
        self.role = role
        self.description = description
        self.history: List[AgentResult] = []

    def execute(self, task: AgentTask) -> AgentResult:
        """执行任务"""
        raise NotImplementedError

    def can_handle(self, task: AgentTask) -> bool:
        """是否能处理该任务"""
        return True


class CrewAIAdapter:
    """
    CrewAI 适配器
    支持多Agent协作工作流
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.tasks: List[AgentTask] = []
        self.results: List[AgentResult] = []
        self._crew = None

    def add_agent(self, agent: BaseAgent) -> None:
        """添加 Agent"""
        self.agents[agent.name] = agent

    def create_task(self, role: AgentRole, description: str,
                   input_data: Any = None, dependencies: List[str] = None) -> AgentTask:
        """创建任务"""
        task_id = f"task_{len(self.tasks)}_{role.value}"
        task = AgentTask(
            id=task_id,
            role=role,
            description=description,
            input_data=input_data,
            dependencies=dependencies or []
        )
        self.tasks.append(task)
        return task

    def execute_workflow(self, tasks: List[AgentTask],
                        mode: str = "sequential") -> List[AgentResult]:
        """
        执行工作流

        Args:
            tasks: 任务列表
            mode: 执行模式 (sequential, parallel, hierarchical)
        """
        self.tasks = tasks
        self.results = []

        if mode == "sequential":
            return self._execute_sequential()
        elif mode == "parallel":
            return self._execute_parallel()
        elif mode == "hierarchical":
            return self._execute_hierarchical()
        else:
            raise ValueError(f"Unknown mode: {mode}")

    def _execute_sequential(self) -> List[AgentResult]:
        """顺序执行"""
        for task in self.tasks:
            result = self._execute_single_task(task)
            self.results.append(result)
        return self.results

    def _execute_parallel(self) -> List[AgentResult]:
        """并行执行（需等待依赖）"""
        pending = {t.id: t for t in self.tasks}
        completed = {}

        while pending:
            # 找出可以执行的任务（依赖已满足）
            ready = []
            for tid, task in pending.items():
                deps_done = all(dep in completed for dep in task.dependencies)
                if deps_done:
                    ready.append(task)

            if not ready:
                break  # 死锁保护

            for task in ready:
                result = self._execute_single_task(task)
                self.results.append(result)
                completed[task.id] = result
                del pending[task.id]

        return self.results

    def _execute_hierarchical(self) -> List[AgentResult]:
        """层级执行（协调者分配任务）"""
        # 第一阶段：协调者规划
        coordinator_tasks = [t for t in self.tasks if t.role == AgentRole.COORDINATOR]
        other_tasks = [t for t in self.tasks if t.role != AgentRole.COORDINATOR]

        # 协调者先执行
        for task in coordinator_tasks:
            result = self._execute_single_task(task)
            self.results.append(result)

        # 然后执行其他任务
        for task in other_tasks:
            result = self._execute_single_task(task)
            self.results.append(result)

        return self.results

    def _execute_single_task(self, task: AgentTask) -> AgentResult:
        """执行单个任务"""
        import time
        start = time.time()

        # 找到合适的 Agent
        agent = self._find_agent(task.role)

        if not agent:
            return AgentResult(
                agent_id=f"none_{task.role.value}",
                role=task.role,
                status="failed",
                output=None,
                error=f"No agent for role: {task.role.value}",
                duration_ms=int((time.time() - start) * 1000)
            )

        task.status = "running"

        try:
            result = agent.execute(task)
            task.status = "completed"
            return result
        except Exception as e:
            task.status = "failed"
            return AgentResult(
                agent_id=agent.name,
                role=task.role,
                status="failed",
                output=None,
                error=str(e),
                duration_ms=int((time.time() - start) * 1000)
            )

    def _find_agent(self, role: AgentRole) -> Optional[BaseAgent]:
        """根据角色查找 Agent"""
        for agent in self.agents.values():
            if agent.role == role:
                return agent
        return None

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "total_agents": len(self.agents),
            "total_tasks": len(self.tasks),
            "completed": sum(1 for r in self.results if r.status == "completed"),
            "failed": sum(1 for r in self.results if r.status == "failed"),
            "roles": list(set(a.role.value for a in self.agents.values()))
        }


class MultiAgentCoordinator:
    """
    多Agent协调器
    整合多种Agent框架
    """

    def __init__(self):
        self.crewai = CrewAIAdapter()
        self._setup_default_agents()

    def _setup_default_agents(self):
        """设置默认 Agents"""
        # 添加内置Agent
        self.crewai.add_agent(CoordinatorAgent())
        self.crewai.add_agent(PlannerAgent())
        self.crewai.add_agent(ExecutorAgent())
        self.crewai.add_agent(ReviewerAgent())
        self.crewai.add_agent(ResearcherAgent())
        self.crewai.add_agent(CoderAgent())
        self.crewai.add_agent(TesterAgent())
        self.crewai.add_agent(DeployerAgent())
        self.crewai.add_agent(MonitorAgent())

    def create_workflow(self, task: str, intent_type: str) -> List[AgentTask]:
        """根据意图类型创建工作流"""
        workflows = {
            "create": self._create_workflow_create,
            "fix": self._create_workflow_fix,
            "test": self._create_workflow_test,
            "deploy": self._create_workflow_deploy,
            "review": self._create_workflow_review,
            "security": self._create_workflow_security,
        }

        creator = workflows.get(intent_type, self._create_workflow_default)
        return creator(task)

    def _create_workflow_create(self, task: str) -> List[AgentTask]:
        """创建 - 创建工作流"""
        return [
            self.crewai.create_task(AgentRole.RESEARCHER, f"调研: {task}"),
            self.crewai.create_task(AgentRole.PLANNER, f"规划: {task}", dependencies=["task_researcher"]),
            self.crewai.create_task(AgentRole.CODER, f"实现: {task}", dependencies=["task_planner"]),
            self.crewai.create_task(AgentRole.TESTER, f"测试: {task}", dependencies=["task_coder"]),
            self.crewai.create_task(AgentRole.REVIEWER, f"审查: {task}", dependencies=["task_tester"]),
        ]

    def _create_workflow_fix(self, task: str) -> List[AgentTask]:
        """修复 - 调试工作流"""
        return [
            self.crewai.create_task(AgentRole.RESEARCHER, f"收集症状: {task}"),
            self.crewai.create_task(AgentRole.PLANNER, f"分析根因: {task}", dependencies=["task_researcher"]),
            self.crewai.create_task(AgentRole.CODER, f"修复: {task}", dependencies=["task_planner"]),
            self.crewai.create_task(AgentRole.TESTER, f"验证修复: {task}", dependencies=["task_coder"]),
        ]

    def _create_workflow_test(self, task: str) -> List[AgentTask]:
        """测试 - 测试工作流"""
        return [
            self.crewai.create_task(AgentRole.PLANNER, f"设计测试: {task}"),
            self.crewai.create_task(AgentRole.TESTER, f"执行测试: {task}", dependencies=["task_planner"]),
            self.crewai.create_task(AgentRole.REVIEWER, f"审查测试: {task}", dependencies=["task_tester"]),
        ]

    def _create_workflow_deploy(self, task: str) -> List[AgentTask]:
        """部署 - 部署工作流"""
        return [
            self.crewai.create_task(AgentRole.RESEARCHER, f"检查环境: {task}"),
            self.crewai.create_task(AgentRole.CODER, f"构建: {task}", dependencies=["task_researcher"]),
            self.crewai.create_task(AgentRole.DEPLOYER, f"部署: {task}", dependencies=["task_coder"]),
            self.crewai.create_task(AgentRole.MONITOR, f"监控: {task}", dependencies=["task_deployer"]),
        ]

    def _create_workflow_review(self, task: str) -> List[AgentTask]:
        """审查 - 审查工作流"""
        return [
            self.crewai.create_task(AgentRole.RESEARCHER, f"获取代码: {task}"),
            self.crewai.create_task(AgentRole.REVIEWER, f"执行审查: {task}", dependencies=["task_researcher"]),
        ]

    def _create_workflow_security(self, task: str) -> List[AgentTask]:
        """安全 - 安全工作流"""
        return [
            self.crewai.create_task(AgentRole.RESEARCHER, f"收集信息: {task}"),
            self.crewai.create_task(AgentRole.REVIEWER, f"安全扫描: {task}", dependencies=["task_researcher"]),
            self.crewai.create_task(AgentRole.PLANNER, f"分析风险: {task}", dependencies=["task_reviewer"]),
        ]

    def _create_workflow_default(self, task: str) -> List[AgentTask]:
        """默认工作流"""
        return [
            self.crewai.create_task(AgentRole.EXECUTOR, f"执行: {task}"),
            self.crewai.create_task(AgentRole.REVIEWER, f"审查: {task}", dependencies=["task_executor"]),
        ]

    def execute(self, task: str, intent_type: str,
                mode: str = "sequential") -> Dict[str, Any]:
        """执行完整工作流"""
        tasks = self.create_workflow(task, intent_type)
        results = self.crewai.execute_workflow(tasks, mode)

        return {
            "task": task,
            "intent_type": intent_type,
            "tasks_count": len(tasks),
            "results": [
                {"role": r.role.value, "status": r.status, "error": r.error}
                for r in results
            ],
            "success": all(r.status == "completed" for r in results),
            "crew_status": self.crewai.get_status()
        }


# 内置 Agent 实现

class CoordinatorAgent(BaseAgent):
    """协调者 Agent"""

    def __init__(self):
        super().__init__("coordinator", AgentRole.COORDINATOR, "协调多Agent工作流")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "coordinated", "task_id": task.id}
        )


class PlannerAgent(BaseAgent):
    """规划者 Agent"""

    def __init__(self):
        super().__init__("planner", AgentRole.PLANNER, "任务规划和分解")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "planned", "task_id": task.id}
        )


class ExecutorAgent(BaseAgent):
    """执行者 Agent"""

    def __init__(self):
        super().__init__("executor", AgentRole.EXECUTOR, "执行具体任务")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "executed", "task_id": task.id}
        )


class ReviewerAgent(BaseAgent):
    """审查者 Agent"""

    def __init__(self):
        super().__init__("reviewer", AgentRole.REVIEWER, "代码审查和质量检查")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "reviewed", "task_id": task.id}
        )


if __name__ == "__main__":
    # 测试
    coordinator = MultiAgentCoordinator()

    print("=== 多Agent协调测试 ===\n")

    # 测试创建工作流
    tasks = coordinator.create_workflow("做个用户管理模块", "create")
    print(f"创建工作流: {len(tasks)} 个任务")
    for t in tasks:
        deps = f" (依赖: {t.dependencies})" if t.dependencies else ""
        print(f"  {t.role.value}: {t.description}{deps}")

    # 执行工作流
    print("\n执行工作流...")
    result = coordinator.execute("做个用户管理模块", "create")

    print(f"\n结果:")
    print(f"  成功: {result['success']}")
    print(f"  任务数: {result['tasks_count']}")

    for r in result['results']:
        print(f"  - {r['role']}: {r['status']}")

    print(f"\nCrew状态: {result['crew_status']}")


class ResearcherAgent(BaseAgent):
    """研究者 Agent"""

    def __init__(self):
        super().__init__("researcher", AgentRole.RESEARCHER, "研究分析")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "researched", "task_id": task.id}
        )


class CoderAgent(BaseAgent):
    """开发者 Agent"""

    def __init__(self):
        super().__init__("coder", AgentRole.CODER, "代码开发")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "coded", "task_id": task.id}
        )


class TesterAgent(BaseAgent):
    """测试者 Agent"""

    def __init__(self):
        super().__init__("tester", AgentRole.TESTER, "测试验证")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "tested", "task_id": task.id}
        )


class DeployerAgent(BaseAgent):
    """部署者 Agent"""

    def __init__(self):
        super().__init__("deployer", AgentRole.DEPLOYER, "部署发布")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "deployed", "task_id": task.id}
        )


class MonitorAgent(BaseAgent):
    """监控者 Agent"""

    def __init__(self):
        super().__init__("monitor", AgentRole.MONITOR, "监控观察")

    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(
            agent_id=self.name,
            role=self.role,
            status="completed",
            output={"action": "monitored", "task_id": task.id}
        )



