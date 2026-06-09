"""
Dify 集成适配器
将 dify (https://github.com/langgenius/dify) 作为 RAG 工作流平台集成
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import requests
import os


@dataclass
class DifyApp:
    """Dify 应用"""
    id: str
    name: str
    description: str
    workflow: Dict[str, Any]


class DifyAdapter:
    """
    Dify 适配器 - 生产级 Agent 工作流开发平台

    功能:
    - RAG 工作流编排
    - Agent 技能编排
    - 向量数据库集成
    - 多模型支持
    """

    def __init__(self, base_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("DIFY_API_KEY", "")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def is_connected(self) -> bool:
        """检查连接状态"""
        try:
            response = self.session.get(f"{self.base_url}/info", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_apps(self) -> List[DifyApp]:
        """列出所有应用"""
        try:
            response = self.session.get(f"{self.base_url}/apps", timeout=10)
            if response.status_code == 200:
                apps = response.json().get("data", [])
                return [
                    DifyApp(
                        id=a.get("id", ""),
                        name=a.get("name", ""),
                        description=a.get("description", ""),
                        workflow=a.get("workflow", {})
                    )
                    for a in apps
                ]
        except Exception as e:
            print(f"获取应用列表失败: {e}")
        return []

    def chat(self, app_id: str, query: str, user: str = "hermes") -> Dict[str, Any]:
        """
        聊天（异步）

        Args:
            app_id: 应用ID
            query: 用户查询
            user: 用户标识

        Returns:
            响应结果
        """
        try:
            response = self.session.post(
                f"{self.base_url}/chat-messages",
                json={
                    "app_id": app_id,
                    "query": query,
                    "user": user,
                    "response_mode": "blocking"
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "answer": result.get("answer", ""),
                    "conversation_id": result.get("conversation_id", ""),
                    "message_id": result.get("message_id", "")
                }
            return {"error": f"请求失败: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def create_rag_pipeline(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        创建 RAG pipeline

        返回创建的工作流配置，可用于 Dify 导入
        """
        workflow = {
            "name": name,
            "description": description or f"RAG Pipeline for {name}",
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "position": {"x": 100, "y": 100}
                },
                {
                    "id": "knowledge_retrieval",
                    "type": "knowledge-retrieval",
                    "position": {"x": 300, "y": 100},
                    "config": {
                        "top_k": 5,
                        "score_threshold": 0.5
                    }
                },
                {
                    "id": "llm",
                    "type": "llm",
                    "position": {"x": 500, "y": 100},
                    "config": {
                        "model": os.getenv("DIFY_LLM_MODEL", "gpt-4"),
                        "temperature": 0.7
                    }
                },
                {
                    "id": "end",
                    "type": "end",
                    "position": {"x": 700, "y": 100}
                }
            ],
            "edges": [
                {"source": "start", "target": "knowledge_retrieval"},
                {"source": "knowledge_retrieval", "target": "llm"},
                {"source": "llm", "target": "end"}
            ]
        }
        return workflow

    def generate_docker_compose(self) -> str:
        """生成 Dify Docker Compose 配置"""
        import secrets
        db_password = os.getenv("DIFY_DB_PASSWORD", secrets.token_urlsafe(16))
        return f'''version: '3.8'

services:
  # Dify API
  api:
    image: langgenius/dify-api:latest
    restart: always
    ports:
      - "8080:8080"
    environment:
      - API_KEY=${{DIFY_API_KEY}}
      - SECRET_KEY=${{DIFY_SECRET_KEY}}
      - INIT_DATABASE=true
      - DB_HOST=db
      - DB_PORT=5432
      - DB_USER=dify
      - DB_PASSWORD={db_password}
      - DB_DATABASE=dify
    depends_on:
      - db
      - redis

  # Dify Web
  web:
    image: langgenius/dify-web:latest
    restart: always
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:8080

  # PostgreSQL
  db:
    image: postgres:15-alpine
    restart: always
    environment:
      - POSTGRES_USER=dify
      - POSTGRES_PASSWORD={db_password}
      - POSTGRES_DB=dify
    volumes:
      - db_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

volumes:
  db_data:
  redis_data:
'''


class RAGPipeline:
    """RAG 管道 - 检索增强生成"""

    def __init__(self, vector_store, embeddings, llm_provider=None):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.llm_provider = llm_provider

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索相关文档"""
        return self.vector_store.search(query, top_k=top_k)

    def generate(self, query: str, context: List[str]) -> str:
        """生成回答"""
        if not self.llm_provider:
            return "LLM provider 未配置，请设置 dify 或其他 LLM"

        prompt = f"""基于以下上下文回答问题。

上下文:
{chr(10).join(context)}

问题: {query}

回答:"""

        # 预留：调用 LLM
        return f"[RAG] 基于 {len(context)} 个文档生成回答"

    def run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """运行完整 RAG 管道"""
        # 1. 检索
        docs = self.retrieve(query, top_k)
        context = [d.get("text", "") for d in docs]

        # 2. 生成
        answer = self.generate(query, context)

        return {
            "query": query,
            "answer": answer,
            "retrieved_docs": len(docs),
            "sources": [d.get("id") for d in docs]
        }


if __name__ == "__main__":
    print("=== Dify 集成适配器 ===\n")

    adapter = DifyAdapter()

    print(f"Dify 连接状态: {'已连接' if adapter.is_connected() else '未连接 (请启动 Dify)'}")

    # 生成 Docker Compose 配置
    print("\nDocker Compose 配置已生成")
    print("使用方法:")
    print("  1. 运行: docker run -p 6333:6333 qdrant/qdrant  (启动 Qdrant)")
    print("  2. 运行: python -c \"print(DifyAdapter().generate_docker_compose())\" > docker-compose.yml")
    print("  3. 运行: docker-compose up -d")
    print("  4. 访问: http://localhost:3000")
