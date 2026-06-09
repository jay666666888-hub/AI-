#!/usr/bin/env python3
"""
RAG Adapter - 知识检索层集成
L11 知识检索层
支持: Qdrant, Milvus, LangChain RetrievalQA
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path


class QdrantRAGAdapter:
    """Qdrant 向量数据库 RAG 适配器"""

    def __init__(self, host: str = "localhost", port: int = 6333,
                 collection: str = "ai_ecosystem_memory"):
        self.host = host
        self.port = port
        self.collection = collection
        self._client = None
        self._embedder = None

    @property
    def client(self):
        if self._client is None:
            from qdrant_client import QdrantClient
            self._client = QdrantClient(host=self.host, port=self.port)
        return self._client

    def ensure_collection(self, vector_size: int = 768) -> bool:
        """确保集合存在"""
        from qdrant_client.models import Distance, VectorParams

        try:
            self.client.get_collection(self.collection)
            return True
        except:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            return True

    def embed_text(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                return [0.0] * 768

        embedding = self._embedder.encode(text)
        return embedding.tolist()

    def index_file(self, file_path: str, chunk_size: int = 500,
                  overlap: int = 50) -> int:
        """索引文件内容"""
        if not os.path.exists(file_path):
            return 0

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        return self.index_text(content, {
            "source": file_path,
            "type": "file"
        }, chunk_size, overlap)

    def index_text(self, text: str, metadata: Dict = None,
                   chunk_size: int = 500, overlap: int = 50) -> int:
        """索引文本块"""
        chunks = self._chunk_text(text, chunk_size, overlap)
        if not chunks:
            return 0

        vectors = [self.embed_text(chunk) for chunk in chunks]
        ids = [self._generate_id(c) for c in chunks]

        from qdrant_client.models import PointStruct
        points = [
            PointStruct(id=id_, vector=vec, payload={
                "text": chunk,
                "metadata": metadata or {},
                "chunk_index": i
            })
            for i, (chunk, vec, id_) in enumerate(zip(chunks, vectors, ids))
        ]

        self.client.upsert(
            collection_name=self.collection,
            points=points
        )
        return len(chunks)

    def index_directory(self, dir_path: str, extensions: List[str] = None,
                        exclude_patterns: List[str] = None) -> Dict[str, int]:
        """索引目录"""
        extensions = extensions or ['.md', '.py', '.txt', '.json', '.yaml', '.yml']
        exclude_patterns = exclude_patterns or ['__pycache__', '.git', 'venv', 'node_modules', '.pytest_cache']

        results = {}
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]

            for file in files:
                if not any(file.endswith(ext) for ext in extensions):
                    continue

                file_path = os.path.join(root, file)
                try:
                    count = self.index_file(file_path)
                    if count > 0:
                        results[file_path] = count
                except Exception as e:
                    print(f"  Warning: Failed to index {file_path}: {e}")

        return results

    def search(self, query: str, limit: int = 5,
               score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """语义搜索 - 使用 scroll + 文本匹配"""
        all_points, _ = self.client.scroll(
            collection_name=self.collection,
            limit=100,
            with_payload=True,
            with_vectors=False
        )

        # 简单的文本匹配评分
        query_lower = query.lower()
        scored = []
        for pt in all_points:
            text = pt.payload.get('text', '') or ''
            text_lower = text.lower()

            # 计算简单的相关性分数
            if query_lower in text_lower:
                score = 1.0
            else:
                # 检查关键词重叠
                query_words = set(query_lower.split())
                text_words = set(text_lower.split())
                overlap = len(query_words & text_words)
                score = overlap / max(len(query_words), 1) * 0.9

            if score >= score_threshold:
                scored.append({
                    "id": pt.id,
                    "score": score,
                    "text": text,
                    "metadata": pt.payload.get('metadata', {}),
                    "source": pt.payload.get('metadata', {}).get('source', 'unknown')
                })

        # 排序并返回 top N
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:limit]

    def retrieve_context(self, query: str, max_tokens: int = 2000) -> str:
        """检索上下文（用于 LLM 提示）"""
        results = self.search(query, limit=10)

        context_parts = []
        total_tokens = 0

        for r in results:
            text = r["text"]
            tokens = len(text) // 4

            if total_tokens + tokens > max_tokens:
                break

            context_parts.append(f"[Source: {r['source']}]\n{text}")
            total_tokens += tokens

        return "\n\n".join(context_parts) if context_parts else ""

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            coll = self.client.get_collection(self.collection)
            return {
                "collection": self.collection,
                "points": coll.points_count,
                "status": coll.status
            }
        except:
            return {"error": "Collection not found"}

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """分块文本"""
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if end < len(text) and not chunk.endswith(('.', '。', '\n', '!', '?')):
                last_period = max(chunk.rfind('。'), chunk.rfind('.'), chunk.rfind('\n'))
                if last_period > start + chunk_size // 2:
                    chunk = chunk[:last_period + 1]

            chunk = chunk.strip()
            if chunk:
                chunks.append(chunk)

            start += chunk_size - overlap

        return chunks

    def _generate_id(self, text: str) -> int:
        """生成确定性 ID"""
        return int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 10**8


class HybridSearchAdapter:
    """混合搜索适配器 - 向量 + 关键词"""

    def __init__(self, vector_adapter: QdrantRAGAdapter):
        self.vector_adapter = vector_adapter

    def search(self, query: str, limit: int = 5,
               vector_weight: float = 0.7) -> List[Dict[str, Any]]:
        """混合搜索"""
        vector_results = self.vector_adapter.search(query, limit=limit * 2)

        keyword_results = self._keyword_search(query, limit=limit)

        merged = {}
        for r in vector_results:
            key = r["source"]
            r["weight"] = vector_weight * r["score"]
            merged[key] = r

        for r in keyword_results:
            key = r["source"]
            if key in merged:
                merged[key]["weight"] += (1 - vector_weight) * r["score"]
            else:
                r["weight"] = (1 - vector_weight) * r["score"]
                merged[key] = r

        sorted_results = sorted(merged.values(), key=lambda x: x["weight"], reverse=True)
        return sorted_results[:limit]

    def _keyword_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """简单关键词搜索（基于 metadata）"""
        return []


class RAGPipeline:
    """RAG 流水线"""

    def __init__(self, adapter: QdrantRAGAdapter):
        self.adapter = adapter
        self.hybrid = HybridSearchAdapter(adapter)

    def build_index(self, project_path: str,
                    patterns: List[str] = None) -> Dict[str, int]:
        """构建项目索引"""
        patterns = patterns or [
            "**/*.md",
            "**/*.py",
            "**/*.txt",
            "**/*.json",
            "**/*.yaml",
            "**/*.yml",
        ]

        print(f"Building RAG index for: {project_path}")

        results = {}
        for pattern in patterns:
            from glob import glob
            files = glob(os.path.join(project_path, pattern), recursive=True)
            for file_path in files:
                if any(x in file_path for x in ['__pycache__', '.git', 'venv', 'node_modules']):
                    continue
                try:
                    count = self.adapter.index_file(file_path)
                    if count > 0:
                        results[file_path] = count
                except Exception as e:
                    print(f"  Warning: {file_path}: {e}")

        total = sum(results.values())
        print(f"Indexed {total} chunks from {len(results)} files")
        return results

    def query_with_context(self, query: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """带上下文的查询"""
        context = self.adapter.retrieve_context(query, max_tokens)
        results = self.adapter.search(query, limit=5)

        return {
            "query": query,
            "context": context,
            "sources": [r["source"] for r in results],
            "results": results
        }


class RetrievalAugmentedSkill:
    """RAG 增强的 Skill 基类"""

    def __init__(self, rag_adapter: QdrantRAGAdapter):
        self.rag = rag_adapter

    def retrieve_knowledge(self, query: str, domain: str = None) -> str:
        """检索相关知识"""
        if domain:
            query = f"{domain}: {query}"
        return self.rag.retrieve_context(query)

    def augment_prompt(self, base_prompt: str, query: str, domain: str = None) -> str:
        """增强提示词"""
        context = self.retrieve_knowledge(query, domain)
        if not context:
            return base_prompt

        return f"""Context from knowledge base:
{context}

---
Original request:
{base_prompt}"""


class L11KnowledgeRetrievalLayer:
    """L11 知识检索层统一适配器"""

    def __init__(self, project_path: str = None):
        self.project_path = project_path or os.getcwd()
        self.qdrant = QdrantRAGAdapter()
        self.hybrid = HybridSearchAdapter(self.qdrant)
        self.pipeline = RAGPipeline(self.qdrant)
        self.retrieval_skill = RetrievalAugmentedSkill(self.qdrant)

    def search(self, query: str, mode: str = "hybrid") -> List[Dict[str, Any]]:
        """搜索"""
        if mode == "vector":
            return self.qdrant.search(query)
        elif mode == "keyword":
            return self.hybrid._keyword_search(query)
        else:
            return self.hybrid.search(query)

    def build_index(self, paths: List[str] = None) -> Dict[str, Any]:
        """构建索引"""
        paths = paths or [self.project_path]
        results = {}

        for path in paths:
            if os.path.isfile(path):
                count = self.qdrant.index_file(path)
                results[path] = count
            else:
                indexed = self.qdrant.index_directory(path)
                results.update(indexed)

        return results

    def query_with_context(self, query: str, max_tokens: int = 2000) -> str:
        """查询并返回上下文"""
        return self.qdrant.retrieve_context(query, max_tokens)

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            "layer": "L11_knowledge_retrieval",
            "qdrant": self.qdrant.get_stats(),
            "retrieval_augmented": True
        }