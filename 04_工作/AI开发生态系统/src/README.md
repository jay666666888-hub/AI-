# AI 开发生态系统 - 核心模块

> 基于 CrewAI + Qdrant 的多AI协调与向量记忆系统

---

## 项目状态

**状态**: 🚀 进行中
**创建日期**: 2026-05-14
**技术栈**: Python 3.12+ | CrewAI 1.14.4 | Qdrant

---

## 目录结构

```
AI开发生态系统/
├── venv/                          # Python 虚拟环境
├── src/
│   ├── __init__.py
│   ├── multi_agent/               # 多AI协调模块 (CrewAI)
│   │   ├── __init__.py
│   │   ├── coordinator.py         # Agent 协调器
│   │   ├── agents/
│   │   │   ├── researcher.py      # 研究员Agent
│   │   │   ├── coder.py           # 程序员Agent
│   │   │   ├── reviewer.py        # 审查员Agent
│   │   │   └── executor.py        # 执行者Agent
│   │   └── tasks/
│   │       ├── research_task.py   # 研究任务
│   │       ├── coding_task.py     # 编码任务
│   │       └── review_task.py     # 审查任务
│   ├── memory/                    # 记忆系统模块 (Qdrant)
│   │   ├── __init__.py
│   │   ├── vector_store.py        # 向量存储
│   │   ├── memory_agent.py        # 记忆Agent
│   │   └── retrieval.py          # 检索系统
│   └── hermes/                    # Hermes 集成层
│       ├── __init__.py
│       ├── hook_manager.py        # Hook 管理器
│       └── skill_loader.py        # Skill 加载器
├── config/
│   ├── agents.yaml                # Agent 配置
│   └── memory.yaml                # 记忆配置
├── tests/
│   ├── test_coordinator.py
│   ├── test_memory.py
│   └── test_integration.py
├── docs/
│   ├── README.md
│   └── ARCHITECTURE.md
├── .env.example                   # 环境变量模板
├── requirements.txt               # 依赖列表
└── README.md                      # 项目首页
```

---

## 核心功能

### 1. 多AI协调 (CrewAI)

```python
from src.multi_agent import AgentCoordinator

coordinator = AgentCoordinator()
result = coordinator.run_task("分析GitHub trending项目")
```

### 2. 向量记忆 (Qdrant)

```python
from src.memory import VectorMemory

memory = VectorMemory()
memory.store("用户偏好", [0.1, 0.2, 0.3])
results = memory.search("用户偏好", top_k=5)
```

### 3. Hermes Hook 集成

```python
from src.hermes import HookManager

hooks = HookManager()
hooks.register("pre_code", my_pre_hook)
```

---

## 快速开始

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行示例
python -m src.multi_agent.examples.basic

# 运行测试
pytest tests/
```

---

## 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 运行时 |
| CrewAI | 1.14.4 | 多AI协调 |
| Qdrant Client | Latest | 向量存储 |
| LangChain | Latest | LLM框架 |
| Pydantic | Latest | 数据验证 |

---

## 下一步

1. 实现 Agent 协调器核心逻辑
2. 配置 Qdrant 向量存储
3. 集成到 Hermes Hook 系统
4. 编写测试用例

---

*最后更新: 2026-05-14*

---
related::
← [[README.md]]
← [[状态矩阵.md]]
← [[03_执行日志.md]]
← [[Readme.md]]
← [[00_项目首页.md]]
← [[verification_20260514.md]]