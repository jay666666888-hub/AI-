"""
Ollama Embeddings - 本地向量嵌入
使用 Ollama 服务进行本地向量嵌入（免费）
"""

from typing import List
import os


class OllamaEmbeddings:
    """Ollama Embedding 客户端 - 本地免费 embeddings"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url
        self.model = model
        self.dimension = 768  # nomic-embed-text 默认维度

    def embed_query(self, text: str) -> List[float]:
        """将单个文本转换为向量"""
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=60
            )
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                # 返回基于文本的确定性向量（备用）
                return self._text_to_vector(text)
        except Exception as e:
            print(f"Ollama error: {e}")
            # 返回基于文本的确定性向量（备用）
            return self._text_to_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量转换文档为向量"""
        return [self.embed_query(text) for text in texts]

    def _text_to_vector(self, text: str) -> List[float]:
        """基于文本内容生成确定性向量（备用方案）"""
        import hashlib
        # 使用文本hash生成种子
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        import random
        random.seed(seed)
        return [random.uniform(-1, 1) for _ in range(self.dimension)]


class LocalEmbeddings:
    """本地确定性嵌入 - 不依赖外部服务"""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        """基于文本内容生成确定性向量"""
        import hashlib
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        import random
        random.seed(seed)
        return [random.uniform(-1, 1) for _ in range(self.dimension)]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量转换"""
        return [self.embed_query(text) for text in texts]


def get_embeddings_provider():
    """获取可用的 embeddings provider"""
    # 优先检查 Ollama 是否可用
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            has_embed_model = any("nomic" in m.get("name", "").lower() for m in models)
            if has_embed_model:
                print("使用 Ollama nomic-embed-text 嵌入")
                return OllamaEmbeddings()
    except Exception as e:
        print(f"Ollama 检测失败: {e}")

    # 如果 Ollama 不可用，使用本地确定性嵌入
    print("使用本地确定性嵌入")
    return LocalEmbeddings()