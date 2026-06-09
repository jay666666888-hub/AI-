"""
AI 开发生态系统 - 快速示例
展示如何使用多AI协调和记忆系统
"""

import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from src.multi_agent.coordinator import AgentCoordinator
from src.memory.vector_store import VectorMemory
from src.memory.retrieval import MemoryRetriever
from src.hermes.hook_manager import HookManager
from src.hermes.skill_loader import SkillLoader


def example_multi_agent():
    """多AI协调示例"""
    print("=" * 60)
    print("示例1: 多AI协调 (CrewAI)")
    print("=" * 60)

    # 初始化协调器
    coordinator = AgentCoordinator()

    # 列出可用Agent
    print(f"可用Agent: {coordinator.list_agents()}")

    # 注意: 实际运行需要配置 OpenAI API Key
    # result = coordinator.run_task(
    #     task="分析GitHub上最火的AI开发工具",
    #     agent="researcher"
    # )
    # print(result)


def example_vector_memory():
    """向量记忆示例"""
    print("\n" + "=" * 60)
    print("示例2: 向量记忆 (Qdrant)")
    print("=" * 60)

    # 注意: 实际运行需要 Qdrant 服务运行在 localhost:6333
    # memory = VectorMemory(host="localhost", port=6333)
    #
    # # 存储记忆
    # memory.store(
    #     text="用户偏好使用TypeScript进行开发",
    #     metadata={"source": "user_preference"}
    # )
    #
    # # 搜索
    # results = memory.search("用户喜欢什么语言")
    # print(results)

    print("要运行此示例，请确保 Qdrant 服务已启动:")
    print("  docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant")


def example_memory_retriever():
    """记忆检索示例"""
    print("\n" + "=" * 60)
    print("示例3: 记忆检索 (短期+长期)")
    print("=" * 60)

    # memory = VectorMemory(host="localhost", port=6333)
    # retriever = MemoryRetriever(memory)
    #
    # # 添加短期记忆
    # retriever.add_to_short_term("用户正在开发AI项目", {"type": "project"})
    #
    # # 检索
    # results = retriever.retrieve("用户在做什么")
    # print(results)
    #
    # # 获取上下文
    # context = retriever.get_context("用户项目", max_context_items=5)
    # print(context)

    print("短期记忆和长期记忆的整合系统")


def example_hook_manager():
    """Hook管理器示例"""
    print("\n" + "=" * 60)
    print("示例4: Hook管理器")
    print("=" * 60)

    # 初始化Hook管理器
    hook_manager = HookManager()

    # 定义自定义hook
    def my_pre_agent_hook(context):
        print(f"[Hook] Agent '{context.get('agent_name')}' 即将执行任务: {context.get('task')}")
        return {"status": "allowed"}

    def my_post_agent_hook(context):
        print(f"[Hook] Agent '{context.get('agent_name')}' 执行完成")
        return {"status": "recorded"}

    # 注册hooks
    hook_manager.register("pre_agent", my_pre_agent_hook)
    hook_manager.register("post_agent", my_post_agent_hook)

    # 触发hook
    result = hook_manager.trigger("pre_agent", {
        "agent_name": "researcher",
        "task": "分析GitHub趋势"
    })

    print(f"触发结果: {result}")

    # 查看历史
    history = hook_manager.get_history()
    print(f"事件历史: {len(history)} 条记录")


def example_skill_loader():
    """Skill加载器示例"""
    print("\n" + "=" * 60)
    print("示例5: Skill加载器")
    print("=" * 60)

    loader = SkillLoader()

    # 尝试从默认路径加载
    count = loader.load_from_path()
    print(f"加载了 {count} 个 skills")

    # 列出类别
    categories = loader.list_categories()
    print(f"Categories: {categories[:5] if categories else 'None'}...")  # 只显示前5个


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("AI 开发生态系统 - 示例演示")
    print("=" * 60)

    # 运行所有示例
    example_multi_agent()
    example_vector_memory()
    example_memory_retriever()
    example_hook_manager()
    example_skill_loader()

    print("\n" + "=" * 60)
    print("示例完成!")
    print("=" * 60)

    print("""
下一步:
1. 确保 Qdrant 服务运行: docker run -p 6333:6333 qdrant/qdrant
2. 配置 OpenAI API Key: export OPENAI_API_KEY=your_key
3. 运行完整示例: python -m src.multi_agent.examples.basic
""")


if __name__ == "__main__":
    main()