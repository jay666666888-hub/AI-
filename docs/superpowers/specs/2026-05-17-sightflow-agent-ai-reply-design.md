# sightflow-agent AI 自动回复扩展设计

**日期**: 2026-05-17
**项目**: deepdadou/sightflow-agent AI 扩展
**技术栈**: Python + SQLite + MiniMax API

---

## 1. 架构

```
sightflow-agent/ (forked + extended)
├── src/sightflow_agent/
│   ├── agent.py              # 修改 _ai_reply 方法
│   ├── ai_integration.py      # MiniMax API 调用（新增）
│   ├── storage/
│   │   ├── history_store.py   # SQLite 历史读写（新增）
│   │   └── __init__.py
│   └── config/
│       ├── contacts.json      # 联系人配置（新增）
│       ├── roles.json        # 角色配置（新增）
│       └── __init__.py
├── .env                     # API Key（不提交 git）
├── config.example.env          # 环境变量模板
└── requirements.txt           # 依赖
```

---

## 2. 核心流程

```
auto_reply 检测未读
    ↓
read_chat 读取消息 + OCR
    ↓
_generate_reply 模式判断
    ↓
_ai_reply (VisionAgent._ai_reply)
    ├─ 检查联系人配置（是否启用、角色）
    ├─ 检查 OCR 哈希防循环
    ├─ 加载对话历史（SQLite）
    ├─ 轻量模型解析最新消息
    ├─ 角色模型生成回复
    ├─ 保存历史到 SQLite
    ├─ 模拟人类延迟
    └─ 返回回复内容
    ↓
send_message 发送
```

---

## 3. 防循环机制

微信截图时间戳每分钟变化，直接哈希会导致哈希失效。

```python
import re
import hashlib

def normalize_text(text: str) -> str:
    """去掉时间戳等不稳定的部分"""
    return re.sub(r'\d{1,2}:\d{2}', '', text).strip()

def ocr_fingerprint(text: str) -> str:
    """OCR 文本归一化后的哈希"""
    return hashlib.md5(normalize_text(text).encode()).hexdigest()
```

```sql
CREATE TABLE ocr_state (
    contact TEXT PRIMARY KEY,
    hash TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);
```

---

## 4. 历史消息顺序

```python
# 正确：时间顺序交替，系统在最前
messages = [
    {"role": "system", "content": role_prompt},
    *history,  # ASC 排序
    {"role": "user", "content": latest_message}
]
```

---

## 5. 两次调用分离

```python
# 第一次：轻量解析模型
parsed = call_minimax(
    model="MiniMax-Text-01",
    messages=[{"role": "user", "content": f"提取最新一条对方消息，只返回内容：\n{ocr_text}"}],
    max_tokens=200
)

# 第二次：角色模型回复
reply = call_minimax(
    model="MiniMax-M2.7",
    messages=[
        {"role": "system", "content": system_prompt},
        *history,  # 已按时间排序
        {"role": "user", "content": parsed}
    ]
)
```

---

## 6. SQLite 表结构

```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp INTEGER NOT NULL
);
CREATE INDEX idx_contact_time ON chat_history(contact, timestamp DESC);

CREATE TABLE ocr_state (
    contact TEXT PRIMARY KEY,
    hash TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);
```

---

## 7. 配置合并规则

联系人配置覆盖角色默认值。

```python
def merge_config(role: dict, contact: dict) -> dict:
    return {
        "name": contact.get("name", role["name"]),
        "system_prompt": contact.get("system_prompt", role["system_prompt"]),
        "temperature": contact.get("temperature", role["temperature"]),
        "min_delay": contact.get("min_delay", role["min_delay"]),
        "max_delay": contact.get("max_delay", role["max_delay"]),
    }
```

---

## 8. 联系人/角色配置

**contacts.json**：
```json
{
    "contacts": {
        "张三": { "role": "friend", "enabled": true },
        "工作群": { "role": "work_group", "enabled": true }
    }
}
```

**roles.json**：
```json
{
    "roles": {
        "friend": {
            "name": "朋友",
            "system_prompt": "你是一个热情开朗的朋友...",
            "temperature": 0.8,
            "min_delay": 1.5,
            "max_delay": 4.0
        },
        "work_group": {
            "name": "工作助手",
            "system_prompt": "你是一个专业的工作助手...",
            "temperature": 0.6,
            "min_delay": 2.0,
            "max_delay": 5.0
        }
    }
}
```

---

## 9. .env 配置

```
MINIMAX_API_KEY=your-api-key-here
MINIMAX_API_BASE=https://api.minimax.chat/v1
MINIMAX_PARSE_MODEL=MiniMax-Text-01
MINIMAX_REPLY_MODEL=MiniMax-M2.7
```
