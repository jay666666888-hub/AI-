"""
AgentMemory 集成适配器
将 agentmemory (https://github.com/rohitg00/agentmemory) 集成到 Hermes 记忆系统
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import os
import time


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: str
    type: str  # short_term, long_term, semantic
    metadata: Dict[str, Any]
    timestamp: float


class AgentMemoryAdapter:
    """
    AgentMemory 适配器 - 为 AI 编码代理提供持久化记忆

    基于 agentmemory 的设计理念:
    - 短期记忆: 当前会话上下文
    - 长期记忆: 跨会话持久化
    - 语义记忆: 向量化的知识检索
    """

    def __init__(self, storage_path: str = "~/.hermes/memory"):
        self.storage_path = os.path.expanduser(storage_path)
        self.short_term: List[MemoryEntry] = []
        self.long_term: List[MemoryEntry] = []
        self.semantic_memory: List[MemoryEntry] = []

    def add_short_term(self, content: str, metadata: Optional[Dict] = None) -> MemoryEntry:
        """添加短期记忆（当前会话）"""
        entry = MemoryEntry(
            id=f"st_{len(self.short_term) + 1}",
            content=content,
            type="short_term",
            metadata=metadata or {},
            timestamp=time.time()
        )
        self.short_term.append(entry)
        return entry

    def add_long_term(self, content: str, metadata: Optional[Dict] = None) -> MemoryEntry:
        """添加长期记忆（持久化）"""
        entry = MemoryEntry(
            id=f"lt_{len(self.long_term) + 1}",
            content=content,
            type="long_term",
            metadata=metadata or {},
            timestamp=time.time()
        )
        self.long_term.append(entry)
        self._persist(entry)
        return entry

    def add_semantic(self, content: str, embedding: List[float], metadata: Optional[Dict] = None) -> MemoryEntry:
        """添加语义记忆（向量化）"""
        entry = MemoryEntry(
            id=f"sm_{len(self.semantic_memory) + 1}",
            content=content,
            type="semantic",
            metadata={**(metadata or {}), "embedding": embedding},
            timestamp=time.time()
        )
        self.semantic_memory.append(entry)
        return entry

    def retrieve(self, query: str, top_k: int = 5, memory_type: str = "all") -> List[MemoryEntry]:
        """检索记忆"""
        results = []

        if memory_type in ("all", "short_term"):
            results.extend(self._search(self.short_term, query))
        if memory_type in ("all", "long_term"):
            results.extend(self._search(self.long_term, query))
        if memory_type in ("all", "semantic"):
            results.extend(self._search_semantic(query, top_k))

        return results[:top_k]

    def _search(self, memory: List[MemoryEntry], query: str) -> List[MemoryEntry]:
        """简单文本搜索"""
        query_lower = query.lower()
        return [m for m in memory if query_lower in m.content.lower()]

    def _search_semantic(self, query: str, top_k: int) -> List[MemoryEntry]:
        """语义搜索（需要嵌入向量）"""
        # 预留：使用 Ollama 嵌入进行语义搜索
        return self.semantic_memory[:top_k]

    def _persist(self, entry: MemoryEntry) -> None:
        """持久化到磁盘"""
        os.makedirs(self.storage_path, exist_ok=True)
        file_path = os.path.join(self.storage_path, f"{entry.id}.json")

        with open(file_path, 'w') as f:
            json.dump({
                "id": entry.id,
                "content": entry.content,
                "type": entry.type,
                "metadata": entry.metadata,
                "timestamp": entry.timestamp
            }, f, ensure_ascii=False, indent=2)

    def load(self) -> int:
        """从磁盘加载长期记忆"""
        os.makedirs(self.storage_path, exist_ok=True)
        count = 0

        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                file_path = os.path.join(self.storage_path, filename)
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    entry = MemoryEntry(
                        id=data['id'],
                        content=data['content'],
                        type=data['type'],
                        metadata=data['metadata'],
                        timestamp=data['timestamp']
                    )
                    if entry.type == "long_term":
                        self.long_term.append(entry)
                    count += 1

        return count

    def clear(self, memory_type: str = "all") -> None:
        """清空记忆"""
        if memory_type in ("all", "short_term"):
            self.short_term = []
        if memory_type in ("all", "long_term"):
            self.long_term = []
            # 清空持久化文件
            for filename in os.listdir(self.storage_path):
                if filename.startswith('lt_'):
                    os.remove(os.path.join(self.storage_path, filename))
        if memory_type in ("all", "semantic"):
            self.semantic_memory = []

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        return {
            "short_term": len(self.short_term),
            "long_term": len(self.long_term),
            "semantic": len(self.semantic_memory),
            "total": len(self.short_term) + len(self.long_term) + len(self.semantic_memory)
        }


def integrate_with_hermes():
    """
    与 Hermes 记忆系统集成的示例
    将 AgentMemory 适配器注册到 HookManager
    """
    from src.hermes.hook_manager import HookManager

    memory_adapter = AgentMemoryAdapter()

    def pre_agent_memory_hook(context: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 执行前的记忆 hook"""
        task = context.get("task", "")
        # 检索相关记忆
        relevant = memory_adapter.retrieve(task, top_k=3)
        context["relevant_memories"] = [m.content for m in relevant]
        return context

    def post_agent_memory_hook(context: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 执行后的记忆 hook"""
        result = context.get("result", "")
        if result:
            # 存储重要结果到长期记忆
            memory_adapter.add_long_term(
                content=f"任务完成: {context.get('task', '')} -> {result}",
                metadata={"agent": context.get("agent_name"), "status": "success"}
            )
        return context

    # 注册到 HookManager
    hook_manager = HookManager()
    hook_manager.register("pre_agent", pre_agent_memory_hook)
    hook_manager.register("post_agent", post_agent_memory_hook)

    return hook_manager, memory_adapter


if __name__ == "__main__":
    print("=== AgentMemory 集成适配器 ===\n")

    # 测试
    adapter = AgentMemoryAdapter()

    # 添加各种记忆
    adapter.add_short_term("用户正在开发 AI 开发生态系统", {"source": "context"})
    adapter.add_long_term("用户偏好使用 Python 进行后端开发", {"source": "preference"})
    adapter.add_semantic("测试驱动开发 TDD 流程", [0.1] * 768, {"type": "methodology"})

    # 检索
    results = adapter.retrieve("用户偏好")
    print(f"检索到 {len(results)} 条记忆:")
    for r in results:
        print(f"  [{r.type}] {r.content[:50]}...")

    print(f"\n记忆统计: {adapter.get_stats()}")

    print("\n✓ AgentMemory 适配器就绪")
