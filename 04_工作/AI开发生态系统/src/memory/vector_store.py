"""
Vector Memory - 向量记忆存储
使用 Qdrant 进行高效的向量存储和检索
支持 Ollama 本地嵌入和确定性本地嵌入
"""

from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from dotenv import load_dotenv

load_dotenv()

# 导入 embeddings provider
from .embeddings import get_embeddings_provider, OllamaEmbeddings, LocalEmbeddings


class VectorMemory:
    """向量记忆存储器，基于 Qdrant + 可配置嵌入"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "ai_ecosystem_memory",
        vector_size: int = 768
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size

        # 初始化嵌入模型（自动检测 Ollama 或使用本地）
        self.embeddings = get_embeddings_provider()

        # 初始化 Qdrant 客户端
        self.client = QdrantClient(host=host, port=port, check_compatibility=False)

        # 确保collection存在
        self._ensure_collection()

    def _ensure_collection(self):
        """确保collection存在，不存在则创建"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"Warning: Could not check/create collection: {e}")

    def store(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        collection: Optional[str] = None
    ) -> str:
        """
        存储文本到向量数据库

        Args:
            text: 要存储的文本
            metadata: 元数据
            collection: 集合名称（默认使用self.collection_name）

        Returns:
            存储的ID
        """
        collection_name = collection or self.collection_name

        # 生成嵌入向量
        vector = self.embeddings.embed_query(text)

        # 存储到Qdrant
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    {
                        "id": hash(text) % 1000000,
                        "vector": vector,
                        "payload": {
                            "text": text,
                            "metadata": metadata or {}
                        }
                    }
                ]
            )
            return f"stored_{hash(text) % 1000000}"
        except Exception as e:
            print(f"Error storing: {e}")
            return f"error_{hash(text) % 1000000}"

    def search(
        self,
        query: str,
        top_k: int = 5,
        collection: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索最相关的向量

        Args:
            query: 搜索查询
            top_k: 返回结果数量
            collection: 集合名称

        Returns:
            搜索结果列表
        """
        collection_name = collection or self.collection_name

        # 生成查询向量
        query_vector = self.embeddings.embed_query(query)

        try:
            # 搜索 (新版本 Qdrant 使用 query_points)
            results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=top_k
            )

            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "text": r.payload.get("text", "") if r.payload else "",
                    "metadata": r.payload.get("metadata", {}) if r.payload else {}
                }
                for r in results.points
            ]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def delete(self, point_id: int, collection: Optional[str] = None) -> bool:
        """删除指定ID的记忆"""
        try:
            collection_name = collection or self.collection_name
            self.client.delete(
                collection_name=collection_name,
                points=[point_id]
            )
            return True
        except Exception:
            return False

    def clear(self, collection: Optional[str] = None) -> bool:
        """清空collection"""
        try:
            collection_name = collection or self.collection_name
            self.client.delete_collection(collection_name)
            self._ensure_collection()
            return True
        except Exception:
            return False


if __name__ == "__main__":
    # 示例用法
    print("初始化向量记忆...")
    memory = VectorMemory(host="localhost", port=6333)

    print(f"嵌入模型: {type(memory.embeddings).__name__}")

    print("存储测试记忆...")
    memory.store(
        text="用户偏好使用Python进行开发",
        metadata={"source": "user_preference", "timestamp": "2026-05-14"}
    )

    print("搜索记忆...")
    results = memory.search("用户喜欢什么编程语言", top_k=5)
    print(f"找到 {len(results)} 条结果")
    for r in results:
        print(f"  - [{r.get('score', 0):.2f}] {r.get('text', '')[:50]}...")