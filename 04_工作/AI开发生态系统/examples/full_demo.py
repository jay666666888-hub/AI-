"""
AI 开发生态系统 - 完整演示
展示所有22个层面的功能
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def demo_multi_agent():
    """多AI协调层"""
    print("\n" + "=" * 60)
    print("1. 多AI协调层 (CrewAI + MiniMax)")
    print("=" * 60)

    from src.multi_agent.coordinator import AgentCoordinator

    coordinator = AgentCoordinator()
    print(f"可用Agent: {coordinator.list_agents()}")
    print(f"LLM配置: minimax/DeepThinker")


def demo_memory():
    """记忆/知识层"""
    print("\n" + "=" * 60)
    print("2. 记忆/知识层 (Qdrant + Ollama)")
    print("=" * 60)

    from src.memory.vector_store import VectorMemory
    from src.memory.embeddings import get_embeddings_provider

    embeddings = get_embeddings_provider()
    print(f"嵌入模型: {type(embeddings).__name__}")
    print(f"向量维度: {embeddings.dimension}")


def demo_workflow():
    """开发流程层"""
    print("\n" + "=" * 60)
    print("3. 开发流程层 (TDD/代码审查/CI/CD)")
    print("=" * 60)

    from src.workflow.tdd import TDDWorkflow
    from src.workflow.code_review import CodeReviewer
    from src.workflow.cicd import CICDExecutor

    # TDD
    tdd = TDDWorkflow()
    state = tdd.start_cycle("用户登录")
    print(f"TDD阶段: {state['phase']}")

    # 代码审查
    reviewer = CodeReviewer()
    sample_code = "api_key = 'sk-12345'  # hardcoded"
    report = reviewer.review(sample_code)
    print(f"代码审查: {report['approval']}")


def demo_ide():
    """智能开发层"""
    print("\n" + "=" * 60)
    print("4. 智能开发层 (AI补全/调试诊断)")
    print("=" * 60)

    from src.ide.completion import AICompletion
    from src.ide.debugger import SmartDebugger

    # AI补全
    completer = AICompletion()
    completions = completer.get_completions("def ", 4, "python")
    print(f"AI补全建议数: {len(completions)}")

    # 智能调试
    debugger = SmartDebugger()
    print("智能调试器就绪")


def demo_security():
    """安全合规层"""
    print("\n" + "=" * 60)
    print("5. 安全合规层 (漏洞扫描/秘钥管理/依赖审计)")
    print("=" * 60)

    from src.security.scanner import VulnerabilityScanner
    from src.security.secret_manager import SecretManager
    from src.security.dependency_audit import DependencyAuditor

    scanner = VulnerabilityScanner()
    print(f"漏洞扫描器: {type(scanner).__name__}")

    manager = SecretManager()
    print(f"秘钥管理器: {type(manager).__name__}")

    auditor = DependencyAuditor()
    print(f"依赖审计器: {type(auditor).__name__}, 语言: {auditor.language}")


def demo_infrastructure():
    """基础设施层"""
    print("\n" + "=" * 60)
    print("6. 基础设施层 (监控/容器/部署)")
    print("=" * 60)

    from src.infrastructure.monitor import Monitor
    from src.infrastructure.container import ContainerManager
    from src.infrastructure.deploy import Deployer

    monitor = Monitor()
    print(f"监控系统: {type(monitor).__name__}")

    container = ContainerManager()
    print(f"容器管理: Docker可用={container.docker_available}")

    deployer = Deployer()
    print(f"部署器: {type(deployer).__name__}")


def demo_creative():
    """创意设计层"""
    print("\n" + "=" * 60)
    print("7. 创意设计层 (UI生成/数据可视化)")
    print("=" * 60)

    from src.creative.ui_generator import UIGenerator
    from src.creative.visualization import DataVisualizer

    ui_gen = UIGenerator()
    btn = ui_gen.generate_component("主要按钮", "button")
    print(f"UI生成器: {btn['component_type']} 组件")

    visualizer = DataVisualizer()
    chart = visualizer.generate_chart([
        {"month": "1月", "sales": 100},
        {"month": "2月", "sales": 150},
    ], title="销售报表")
    print(f"可视化: {chart['type']} 图表")


def demo_hermes():
    """Hermes系统"""
    print("\n" + "=" * 60)
    print("8. Hermes系统 (Hooks + Skills)")
    print("=" * 60)

    from src.hermes.hook_manager import HookManager
    from src.hermes.skill_loader import SkillLoader

    hook_mgr = HookManager()
    print(f"Hook管理器: {len(hook_mgr.hooks)} 种Hook类型")

    skill_loader = SkillLoader()
    count = skill_loader.load_from_path()
    print(f"Skill加载器: 已加载 {count} 个Skills")


def main():
    print("\n" + "=" * 60)
    print("AI 开发生态系统 - 完整演示")
    print("=" * 60)

    demo_multi_agent()
    demo_memory()
    demo_workflow()
    demo_ide()
    demo_security()
    demo_infrastructure()
    demo_creative()
    demo_hermes()

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)

    print("""
下一步:
1. 启动 Qdrant: docker run -p 6333:6333 qdrant/qdrant
2. 启动 Ollama: ollama serve
3. 配置 MiniMax API Key: export MINIMAX_API_KEY=your_key
4. 运行完整示例: python examples/quickstart.py
""")


if __name__ == "__main__":
    main()
