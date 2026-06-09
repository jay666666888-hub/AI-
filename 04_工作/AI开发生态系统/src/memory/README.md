# Memory System - Vector Store

> 基于 Qdrant 的向量记忆存储与检索系统

---

## 功能

- 向量存储：使用 Qdrant 进行高效向量存储
- 语义检索：基于相似度的语义搜索
- 记忆管理：短期/长期记忆分离
- 上下文管理：跨会话上下文保持

---

## 使用

```python
from src.memory import VectorMemory

memory = VectorMemory(host="localhost", port=6333)
memory.store(collection="knowledge", text="示例文本", metadata={"source": "test"})
results = memory.search(collection="knowledge", query="搜索内容", top_k=5)
```

---

*最后更新: 2026-05-14*