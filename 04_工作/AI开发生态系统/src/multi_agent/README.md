# Multi-Agent Coordination System

> 基于 CrewAI 的多AI协调框架

---

## Agents

### 1. Coordinator (协调器)
- 任务分解与分配
- Agent 间通信协调
- 结果聚合与输出

### 2. Researcher (研究员)
- 信息收集与整理
- GitHub 项目分析
- 趋势研究

### 3. Coder (程序员)
- 代码生成与实现
- 自动化任务执行
- 测试编写

### 4. Reviewer (审查员)
- 代码审查
- 安全扫描
- 质量评估

### 5. Executor (执行者)
- CI/CD 任务执行
- 部署操作
- 系统集成

---

## 使用

```python
from src.multi_agent import AgentCoordinator

coordinator = AgentCoordinator()

# 运行研究任务
research_result = coordinator.run_task(
    task="分析 GitHub Trending 上的 AI 开发工具",
    agent="researcher"
)

# 运行编码任务
coding_result = coordinator.run_task(
    task="实现一个 CLI 工具",
    agent="coder"
)
```

---

## Tasks

- research_task: 信息收集与研究
- coding_task: 代码生成与实现
- review_task: 代码审查与反馈

---

*最后更新: 2026-05-14*