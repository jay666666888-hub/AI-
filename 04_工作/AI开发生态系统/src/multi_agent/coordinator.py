"""
Agent Coordinator - 协调多个AI Agent协作
集成开发流程工具: TDDWorkflow, CodeReviewer, CICDExecutor, HookManager
"""

from typing import Optional, Dict, Any, List
from crewai import Agent, Task, Crew
from crewai.llm import LLM
import os

from src.workflow.tdd import TDDWorkflow, TDDPhase
from src.workflow.code_review import CodeReviewer
from src.workflow.cicd import CICDExecutor
from src.hermes.hook_manager import HookManager, HookType


class AgentCoordinator:
    """多AI协调器，负责分解任务并协调多个Agent执行"""

    def __init__(self):
        self.agents = {}
        self.tasks = {}

        # 初始化工作流工具
        self.tdd = TDDWorkflow()
        self.code_reviewer = CodeReviewer()
        self.cicd = CICDExecutor()
        self.hook_manager = HookManager()

        # 配置 MiniMax API - 从环境变量读取
        self.llm = LLM(
            model="minimax/DeepThinker",
            api_key=os.getenv("MINIMAX_API_KEY", ""),
            base_url="https://api.minimaxi.com/anthropic"
        )

        self._setup_agents()
        self._register_hooks()

    def _register_hooks(self):
        """注册Hermes hooks连接工作流工具"""

        # Coder执行前触发TDD RED阶段
        def pre_coder_hook(context: Dict[str, Any]) -> Dict[str, Any]:
            if context.get("agent") == "coder" and context.get("task"):
                tdd_state = self.tdd.start_cycle(context["task"])
                return {"tdd_phase": tdd_state}
            return {"status": "skipped"}

        # Coder执行后触发TDD GREEN阶段
        def post_coder_hook(context: Dict[str, Any]) -> Dict[str, Any]:
            if context.get("agent") == "coder" and context.get("result"):
                green_state = self.tdd.proceed_to_green("")
                return {"tdd_phase": green_state}
            return {"status": "skipped"}

        # Reviewer执行时触发代码审查
        def post_reviewer_hook(context: Dict[str, Any]) -> Dict[str, Any]:
            if context.get("agent") == "reviewer" and context.get("code"):
                report = self.code_reviewer.review(context["code"])
                return {"review_report": report}
            return {"status": "skipped"}

        # Executor执行后触发CI/CD
        def post_executor_hook(context: Dict[str, Any]) -> Dict[str, Any]:
            if context.get("agent") == "executor" and context.get("pipeline"):
                result = self.cicd.run_pipeline(context["pipeline"])
                return {"pipeline_result": result}
            return {"status": "skipped"}

        self.hook_manager.register("pre_agent", pre_coder_hook)
        self.hook_manager.register("post_agent", post_coder_hook)
        self.hook_manager.register("post_agent", post_reviewer_hook)
        self.hook_manager.register("post_agent", post_executor_hook)

    def _setup_agents(self):
        """初始化所有Agent"""

        # 研究员Agent - 负责信息收集和分析
        self.researcher = Agent(
            role="Researcher",
            goal="收集和分析GitHub上的热门AI开发工具项目",
            backstory="""你是一位经验丰富的技术研究员，擅长发现和评估
            开源项目。你会分析项目的Stars、活跃度、技术栈和实用性。""",
            llm=self.llm,
            verbose=True
        )

        # 程序员Agent - 负责代码生成和实现 (TDD模式)
        self.coder = Agent(
            role="Coder",
            goal="根据需求使用TDD方法生成高质量的生产级代码",
            backstory="""你是一位资深的全栈工程师，精通TypeScript、Python、Go
            等多种语言。你严格遵循TDD流程：红(写测试)→绿(写实现)→重构。
            每个功能都要先写测试，确保80%+覆盖率。""",
            llm=self.llm,
            verbose=True
        )

        # 审查员Agent - 负责代码审查和质量把控
        self.reviewer = Agent(
            role="Reviewer",
            goal="确保代码质量、安全性和可维护性",
            backstory="""你是代码审查专家，精通多种编程语言和安全最佳实践。
            你会检查代码的漏洞、性能问题和可维护性风险。
            你使用自动化代码审查工具辅助人工审查。""",
            llm=self.llm,
            verbose=True
        )

        # 执行者Agent - 负责任务执行和部署
        self.executor = Agent(
            role="Executor",
            goal="高效执行CI/CD任务和部署操作",
            backstory="""你是DevOps专家，擅长自动化部署和CI/CD流程。
            你使用标准化流水线执行构建、测试、部署任务。
            你确保任务正确执行并提供详细的执行报告。""",
            llm=self.llm,
            verbose=True
        )

        self.agents = {
            "researcher": self.researcher,
            "coder": self.coder,
            "reviewer": self.reviewer,
            "executor": self.executor
        }

    def run_task(self, task: str, agent: str = "researcher",
                 code: str = None, pipeline: Any = None) -> Dict[str, Any]:
        """
        运行指定任务

        Args:
            task: 任务描述
            agent: 使用的Agent类型 (researcher/coder/reviewer/executor)
            code: 要审查的代码（用于reviewer）
            pipeline: CI/CD流水线（用于executor）

        Returns:
            执行结果字典
        """
        if agent not in self.agents:
            return {"error": f"Unknown agent: {agent}"}

        agent_obj = self.agents[agent]

        # 触发pre_agent hook
        pre_context = {"agent": agent, "task": task, "code": code, "pipeline": pipeline}
        pre_result = self.hook_manager.trigger("pre_agent", pre_context)

        # 创建任务
        crew_task = Task(description=task, agent=agent_obj, expected_output="任务执行结果")

        # 创建Crew并执行
        crew = Crew(agents=[agent_obj], tasks=[crew_task], verbose=True)
        try:
            result = crew.kickoff()
        except Exception as e:
            # 触发on_error hook
            self.hook_manager.trigger("on_error", {"agent": agent, "error": str(e)})
            return {
                "agent": agent,
                "task": task,
                "result": None,
                "status": "error",
                "error": str(e),
                "hooks": pre_result
            }

        # 触发post_agent hook
        post_context = {"agent": agent, "task": task, "result": result, "code": code, "pipeline": pipeline}
        post_result = self.hook_manager.trigger("post_agent", post_context)

        return {
            "agent": agent,
            "task": task,
            "result": result,
            "status": "success",
            "hooks": {
                "pre": pre_result,
                "post": post_result
            }
        }

    def run_multi_agent_task(self, task: str, agent_sequence: List[str]) -> Dict[str, Any]:
        """
        运行多Agent协作任务

        Args:
            task: 主任务描述
            agent_sequence: Agent执行顺序列表

        Returns:
            聚合结果字典
        """
        results = []

        for agent_type in agent_sequence:
            result = self.run_task(task, agent_type)
            results.append(result)

            # 触发on_success或on_error hook
            if result.get("status") == "success":
                self.hook_manager.trigger("on_success", {"agent": agent_type, "result": result})
            else:
                self.hook_manager.trigger("on_error", {"agent": agent_type, "result": result})

            # 如果是审查任务，根据结果决定是否继续
            if agent_type == "reviewer":
                review_report = result.get("hooks", {}).get("post", {}).get("results", [{}])[0] if result.get("hooks", {}).get("post", {}).get("results") else {}
                if review_report.get("review_report", {}).get("approval") == "BLOCKED":
                    return {
                        "status": "rejected",
                        "results": results,
                        "reason": "Review BLOCKED - critical issues found"
                    }

        return {
            "status": "success",
            "results": results
        }

    def run_tdd_cycle(self, feature: str, test_code: str, implementation: str) -> Dict[str, Any]:
        """
        运行完整的TDD周期

        Args:
            feature: 功能描述
            test_code: 测试代码
            implementation: 实现代码

        Returns:
            TDD周期结果
        """
        # RED阶段
        red_state = self.tdd.start_cycle(feature)

        # GREEN阶段
        green_state = self.tdd.proceed_to_green(test_code)

        # REFACTOR阶段
        refactor_state = self.tdd.proceed_to_refactor(implementation)

        return {
            "red": red_state,
            "green": green_state,
            "refactor": refactor_state,
            "complete": self.tdd.complete_cycle()
        }

    def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        审查代码

        Args:
            code: 要审查的代码
            language: 编程语言

        Returns:
            审查报告
        """
        return self.code_reviewer.review(code, language)

    def create_pipeline(self, name: str, steps: List[Dict[str, Any]]):
        """创建CI/CD流水线"""
        return self.cicd.create_pipeline(name, steps)

    def run_pipeline(self, pipeline) -> Dict[str, Any]:
        """运行CI/CD流水线"""
        return self.cicd.run_pipeline(pipeline)

    def generate_dockerfile(self, language: str, port: int = 8000) -> str:
        """生成Dockerfile"""
        return self.cicd.generate_dockerfile(language, port)

    def list_agents(self) -> List[str]:
        """列出所有可用Agent"""
        return list(self.agents.keys())

    def get_hook_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取Hook执行历史"""
        return self.hook_manager.get_history(limit)


if __name__ == "__main__":
    # 示例用法
    coordinator = AgentCoordinator()

    print("=" * 60)
    print("AI 开发生态系统 - 多Agent协调器")
    print("=" * 60)
    print(f"可用Agent: {coordinator.list_agents()}")
    print(f"TDD工具: {coordinator.tdd is not None}")
    print(f"代码审查: {coordinator.code_reviewer is not None}")
    print(f"CI/CD: {coordinator.cicd is not None}")
    print(f"Hook管理器: {len(coordinator.hook_manager.hooks)} 种Hook类型")
    print("=" * 60)

    # TDD示例
    print("\n--- TDD周期示例 ---")
    tdd_result = coordinator.run_tdd_cycle(
        feature="用户登录功能",
        test_code="def test_login(): assert authenticate('user', 'pass')",
        implementation="def authenticate(u, p): return u == 'user' and p == 'pass'"
    )
    print(f"RED: {tdd_result['red']['phase']}")
    print(f"GREEN: {tdd_result['green']['phase']}")
    print(f"REFACTOR: {tdd_result['refactor']['phase']}")

    # 代码审查示例
    print("\n--- 代码审查示例 ---")
    sample_code = "api_key = 'sk-12345'  # hardcoded"
    review = coordinator.review_code(sample_code)
    print(f"审查结果: {review['approval']}")
    print(f"问题: {review['summary']}")

    # Dockerfile生成示例
    print("\n--- Dockerfile生成示例 ---")
    dockerfile = coordinator.generate_dockerfile("python", 8000)
    print(dockerfile)