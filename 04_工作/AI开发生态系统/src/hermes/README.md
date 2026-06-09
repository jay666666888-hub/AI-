# Hermes Integration Layer

> 连接 CrewAI 多AI协调系统与 Hermes Hook 系统

---

## 功能

- Hook 管理器：注册和管理 Hermes hooks
- Skill 加载器：动态加载 Claude Code skills
- 事件总线：Agent 间通信
- 状态同步：跨会话状态管理

---

## 使用

```python
from src.hermes import HookManager, SkillLoader

hooks = HookManager()
hooks.register("pre_agent", my_pre_hook)

skills = SkillLoader()
skills.load_from_path("/path/to/skills")
```

---

*最后更新: 2026-05-14*

---
related::
← [[2026-05-14.md]]
← [[决策库.md]]
← [[运行规则.md]]
← [[README.md]]