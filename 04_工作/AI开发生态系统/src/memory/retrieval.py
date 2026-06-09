"""
Memory Retriever - 记忆检索器
提供高级记忆检索功能
"""

from typing import List, Dict, Any, Optional
from .vector_store import VectorMemory


class MemoryRetriever:
    """记忆检索器，提供语义搜索和上下文管理"""

    def __init__(self, vector_memory: VectorMemory = None):
        self.vector_memory = vector_memory
        self.short_term_memory: List[Dict[str, Any]] = []
        self.long_term_threshold = 0.85

    def add_to_short_term(self, text: str, metadata: Optional[Dict] = None):
        """添加到短期记忆"""
        self.short_term_memory.append({
            "text": text,
            "metadata": metadata or {},
            "timestamp": self._get_timestamp()
        })

    def promote_to_long_term(self, text: str, metadata: Optional[Dict] = None):
        """将短期记忆提升到长期记忆"""
        self.vector_memory.store(text=text, metadata=metadata)

    def retrieve(self, query: str, use_short_term: bool = True, top_k: int = 5) -> Dict[str, Any]:
        """
        检索记忆

        Args:
            query: 搜索查询
            use_short_term: 是否使用短期记忆
            top_k: 返回结果数量

        Returns:
            包含短期和长期记忆结果的字典
        """
        results = {
            "short_term": [],
            "long_term": [],
            "combined": []
        }

        # 短期记忆搜索（精确匹配）
        if use_short_term:
            short_term_matches = [
                item for item in self.short_term_memory
                if query.lower() in item["text"].lower()
            ]
            results["short_term"] = short_term_matches[:top_k]

        # 长期记忆搜索（向量相似度）
        long_term_results = self.vector_memory.search(query=query, top_k=top_k)
        results["long_term"] = long_term_results

        # 合并结果
        for item in results["short_term"]:
            item["source"] = "short_term"
            results["combined"].append(item)

        for item in results["long_term"]:
            item["source"] = "long_term"
            results["combined"].append(item)

        return results

    def consolidate_short_term(self, threshold: float = 5):
        """
        整理短期记忆，将重要内容提升到长期记忆

        Args:
            threshold: 访问次数阈值，超过则提升
        """
        to_promote = []
        for item in self.short_term_memory:
            if item.get("access_count", 0) >= threshold:
                to_promote.append(item)

        # 提升到长期记忆
        for item in to_promote:
            self.promote_to_long_term(item["text"], item.get("metadata"))
            self.short_term_memory.remove(item)

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_context(self, query: str, max_context_items: int = 10) -> str:
        """
        获取检索到的上下文，用于填充LLM的context window

        Args:
            query: 搜索查询
            max_context_items: 最大上下文项数

        Returns:
            格式化的上下文字符串
        """
        results = self.retrieve(query=query, top_k=max_context_items)

        context_parts = []
        context_parts.append("=== 短期记忆 ===")
        for item in results["short_term"]:
            context_parts.append(f"- {item['text']}")

        context_parts.append("\n=== 长期记忆 ===")
        for item in results["long_term"]:
            context_parts.append(f"- [{item['score']:.2f}] {item['text']}")

        return "\n".join(context_parts)


if __name__ == "__main__":
    # 示例用法
    memory = VectorMemory(host="localhost", port=6333)
    retriever = MemoryRetriever(memory)

    # 添加短期记忆
    retriever.add_to_short_term("用户喜欢使用Python", {"type": "preference"})
    retriever.add_to_short_term("用户正在开发AI项目", {"type": "project"})

    # 检索
    results = retriever.retrieve("用户喜欢什么编程语言")
    print(results)

    # 获取上下文
    context = retriever.get_context("用户编程偏好", max_context_items=5)
    print(context)