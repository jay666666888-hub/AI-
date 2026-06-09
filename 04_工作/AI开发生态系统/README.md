# AI 开发生态系统 v4.0

> 基于 **18 层架构** + **Superpowers 工作流** + **智能路由**
> 集成 58 个 Claude Code Agents + 11 个 Skills + 54+ 适配器

---

## 项目状态

| 指标 | 状态 |
|------|------|
| 版本 | v4.0 |
| Skills | 11 个 ✅ |
| Agents | 58 个 ✅ |
| Layers | 13 个可用 |
| 外部依赖 | 已安装 (hvac, docker, kubernetes) |

**运行检查**: `python src/ecosystem_doctor.py`

---

## 快速启动

### Windows (PowerShell)

```powershell
cd E:\黑曜石\04_工作\AI开发生态系统

# 使用 venv
.\venv\Scripts\python.exe src\ecosystem_doctor.py
.\venv\Scripts\python.exe src\ecosystem.py

# 或直接
python src\ecosystem.py
```

### WSL / Linux

```bash
# 项目根目录 (根据实际挂载点调整)
export PROJECT_DIR="/mnt/e/黑曜石/04_工作/AI开发生态系统"
cd $PROJECT_DIR

# 激活虚拟环境
source venv/bin/activate

# 运行
python src/ecosystem_doctor.py
python src/ecosystem.py
```

---

## 系统架构

```
用户任务 → Skill Router → Superpowers 工作流 → 18 层执行 → 结果

┌──────────────────────────────────────────────────────┐
│  Skill Router (智能路由)                            │
│  自动识别: fix/create/review/security/deploy...     │
│  路由到: Skills + Agents + Layers                 │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Superpowers 工作流                                 │
│  brainstorming → writing_plans → TDD →            │
│  code_review → verification → deploy              │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  18 层架构                                        │
│  L4 意图理解 → L5 规划 → L9 测试 → L12 容器 → L14 部署 │
└──────────────────────────────────────────────────────┘
```

---

## 核心文件

| 文件 | 说明 |
|------|------|
| `src/ecosystem.py` | 主入口 |
| `src/ecosystem_orchestrator.py` | 编排器 |
| `src/ecosystem_doctor.py` | 健康检查 |
| `src/skills/` | 11 个 Skills |
| `src/integrations/` | 54+ 适配器 |
| `docs/状态矩阵.md` | 各层状态 |

---

## 环境变量配置

复制 `.env.example` 为 `.env`:

```bash
# LLM (默认 MiniMax)
LLM_PROVIDER=minimax
LLM_MODEL=minimax/DeepThinker
MINIMAX_API_KEY=your_key_here

# 或使用 OpenAI (备选)
OPENAI_API_KEY=your_key_here

# Qdrant (向量数据库)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## 已验证可用的服务

| 服务 | 状态 | 启动命令 |
|------|------|----------|
| Docker | ✅ | `docker ps` |
| Qdrant | ✅ | `docker run -d -p 6333:6333 qdrant/qdrant` |
| Skills | ✅ | 内置 |
| Agents | ✅ | 58 个已注册 |

## 待配置的服务

| 服务 | 状态 | 说明 |
|------|------|------|
| Vault | 🔶 | 需要 Vault Token |
| MiniMax API | 🔶 | 需要 API Key |
| K8s/ArgoCD | 🔶 | 需要集群 |

---

## 目录结构

```
AI开发生态系统/
├── src/
│   ├── ecosystem.py              # 主入口
│   ├── ecosystem_orchestrator.py # 编排器
│   ├── ecosystem_doctor.py       # 健康检查
│   ├── skills/                  # 11 个 Skills
│   │   ├── brainstorming.py
│   │   ├── writing_plans.py
│   │   ├── tdd_skill.py
│   │   ├── code_review_skill.py
│   │   └── ...
│   ├── integrations/              # 54+ 适配器
│   │   ├── intent_adapter.py    # L4
│   │   ├── planning_adapter.py  # L5
│   │   ├── container_adapter.py  # L12
│   │   └── ...
│   ├── memory/                  # 记忆系统
│   └── multi_agent/             # Agent 协调
├── config/
│   └── memory.yaml              # 配置
├── docs/
│   └── 状态矩阵.md              # 状态文档
├── requirements.txt
└── README.md
```

---

**最后更新**: 2026-05-14 v4.0
**项目路径**: `<根据实际挂载点调整>/黑曜石/04_工作/AI开发生态系统/`

---
related::
← [[README.md]]
← [[verification_20260514.md]]
← [[状态矩阵.md]]