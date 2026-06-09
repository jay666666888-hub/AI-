# sightflow-agent AI 自动回复实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为 sightflow-agent 的 VisionAgent 实现 AI 回复功能，支持 MiniMax API、联系人独立角色配置、SQLite 历史存储。

**架构：** fork 后扩展，在 agent.py 中修改 `_ai_reply` 方法，新增 ai_integration.py 调用 MiniMax、storage/history_store.py 管理 SQLite 历史、config/ 目录存放 JSON 配置。

**技术栈：** Python + SQLite + MiniMax API + 环境变量配置

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `src/sightflow_agent/agent.py` | 修改 `_ai_reply` 方法，新增配置加载、历史存储调用 |
| `src/sightflow_agent/ai_integration.py` | MiniMax API 调用（两次分离：解析 + 回复） |
| `src/sightflow_agent/storage/history_store.py` | SQLite 对话历史读写 |
| `src/sightflow_agent/config/contacts.json` | 联系人角色配置 |
| `src/sightflow_agent/config/roles.json` | 角色默认配置 |
| `src/sightflow_agent/config/__init__.py` | 配置加载器 |
| `src/sightflow_agent/storage/__init__.py` | 存储模块导出 |
| `.env` | API Key 和模型配置 |
| `config.example.env` | 环境变量模板 |
| `requirements.txt` | 依赖：python-dotenv |

---

### 任务 1：fork 并初始化环境

**文件：**
- 创建：`src/sightflow_agent/storage/__init__.py`
- 创建：`src/sightflow_agent/config/__init__.py`

- [ ] **步骤 1：创建 storage/__init__.py**

```python
from .history_store import HistoryStore

__all__ = ["HistoryStore"]
```

- [ ] **步骤 2：创建 config/__init__.py**

```python
import json
import os
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path(__file__).parent
CONTACTS_FILE = CONFIG_DIR / "contacts.json"
ROLES_FILE = CONFIG_DIR / "roles.json"

def load_contacts() -> dict:
    if not CONTACTS_FILE.exists():
        return {}
    with open(CONTACTS_FILE) as f:
        return json.load(f).get("contacts", {})

def load_roles() -> dict:
    if not ROLES_FILE.exists():
        return {}
    with open(ROLES_FILE) as f:
        return json.load(f).get("roles", {})

__all__ = ["load_contacts", "load_roles", "CONTACTS_FILE", "ROLES_FILE"]
```

- [ ] **步骤 3：Commit**

```bash
git add src/sightflow_agent/storage/__init__.py src/sightflow_agent/config/__init__.py
git commit -m "feat: init storage and config modules"
```

---

### 任务 2：SQLite 历史存储（history_store.py）

**文件：**
- 创建：`src/sightflow_agent/storage/history_store.py`
- 测试：`tests/test_history_store.py`

- [ ] **步骤 1：编写失败的测试**

```python
import pytest
import tempfile
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent)
from src.sightflow_agent.storage.history_store import HistoryStore

@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        path = f.name
    yield path
    os.unlink(path)

def test_add_and_get_history(db_path):
    store = HistoryStore(db_path)
    store.add_message("张三", "user", "你好")
    store.add_message("张三", "assistant", "你好呀")

    history = store.get_history("张三")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

def test_ocr_hash_save_and_get(db_path):
    store = HistoryStore(db_path)
    store.save_ocr_hash("张三", "abc123")

    assert store.get_ocr_hash("张三") == "abc123"

def test_ocr_hash_update(db_path):
    store = HistoryStore(db_path)
    store.save_ocr_hash("张三", "abc123")
    store.save_ocr_hash("张三", "def456")
    assert store.get_ocr_hash("张三") == "def456"

def test_get_history_respects_limit(db_path):
    store = HistoryStore(db_path)
    for i in range(30):
        store.add_message("张三", "user", f"msg{i}")
    history = store.get_history("张三", limit=10)
    assert len(history) == 10
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_history_store.py -v`
预期：FAIL，报错 "No module named 'src'"

- [ ] **步骤 3：编写 history_store.py**

```python
import sqlite3
import hashlib
import re
from pathlib import Path
from typing import Optional, List, Dict

def normalize_text(text: str) -> str:
    """去掉时间戳等不稳定字符"""
    return re.sub(r'\d{1,2}:\d{2}', '', text).strip()

def ocr_fingerprint(text: str) -> str:
    """归一化后的 md5 哈希"""
    return hashlib.md5(normalize_text(text).encode()).hexdigest()

class HistoryStore:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_contact_time ON chat_history(contact, timestamp DESC);

            CREATE TABLE IF NOT EXISTS ocr_state (
                contact TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            );
        """)

    def add_message(self, contact: str, role: str, content: str) -> None:
        self.db.execute(
            "INSERT INTO chat_history (contact, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (contact, role, content, __import__('time').time_ns() // 1_000_000)
        )
        self.db.commit()

    def get_history(self, contact: str, limit: int = 20) -> List[Dict]:
        cur = self.db.execute(
            "SELECT role, content FROM chat_history WHERE contact = ? ORDER BY timestamp ASC LIMIT ?",
            (contact, limit)
        )
        return [{"role": r[0], "content": r[1]} for r in cur.fetchall()]

    def save_ocr_hash(self, contact: str, hash: str) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO ocr_state (contact, hash, updated_at) VALUES (?, ?, ?)",
            (contact, hash, __import__('time').time_ns() // 1_000_000)
        )
        self.db.commit()

    def get_ocr_hash(self, contact: str) -> Optional[str]:
        cur = self.db.execute("SELECT hash FROM ocr_state WHERE contact = ?", (contact,))
        row = cur.fetchone()
        return row[0] if row else None
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_history_store.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add src/sightflow_agent/storage/history_store.py tests/test_history_store.py
git commit -m "feat: add SQLite history store with ocr hash tracking"
```

---

### 任务 3：MiniMax API 集成（ai_integration.py）

**文件：**
- 创建：`src/sightflow_agent/ai_integration.py`
- 测试：`tests/test_ai_integration.py`

- [ ] **步骤 1：编写失败的测试**

```python
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent)
import os
os.environ["MINIMAX_API_KEY"] = "test-key"
os.environ["MINIMAX_API_BASE"] = "https://api.minimax.chat/v1"

from src.sightflow_agent.ai_integration import MiniMaxClient

def test_two_phase_call_sequence():
    client = MiniMaxClient()
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs)
        import json
        return type("Response", (), {"ok": True, "json": lambda: {"choices": [{"message": {"content": "parsed"}}]})()

    client._post = fake_post
    result = client.two_phase_reply(
        ocr_text="test ocr",
        system_prompt="你是一个朋友",
        history=[{"role": "user", "content": "历史消息"}],
        parse_model="MiniMax-Text-01",
        reply_model="MiniMax-M2.7"
    )

    assert len(calls) == 2
    # 第一次调用是解析
    assert calls[0]["json"]["model"] == "MiniMax-Text-01"
    # 第二次调用是回复
    assert calls[1]["json"]["model"] == "MiniMax-M2.7"
    assert len(calls[1]["json"]["messages"]) == 3  # system + history + user
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_ai_integration.py -v`
预期：FAIL

- [ ] **步骤 3：编写 ai_integration.py**

```python
import os
import requests
from typing import List, Dict, Optional
import time

class MiniMaxClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        parse_model: str = "MiniMax-Text-01",
        reply_model: str = "MiniMax-M2.7"
    ):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.base_url = base_url or os.getenv("MINIMAX_API_BASE", "https://api.minimax.chat/v1")
        self.parse_model = parse_model
        self.reply_model = reply_model

    def _post(self, url: str, **kwargs):
        return requests.post(url, **kwargs)

    def two_phase_reply(
        self,
        ocr_text: str,
        system_prompt: str,
        history: List[Dict],
        parse_model: Optional[str] = None,
        reply_model: Optional[str] = None
    ) -> str:
        # 第一次：轻量解析
        parse_result = self._call(
            model=parse_model or self.parse_model,
            messages=[{"role": "user", "content": f"提取最新一条对方消息，只返回内容：\n{ocr_text}"}],
            max_tokens=200
        )

        # 第二次：角色回复
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": parse_result})

        return self._call(
            model=reply_model or self.reply_model,
            messages=messages
        )

    def _call(self, model: str, messages: List[Dict], max_tokens: int = 1024) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
        resp = self._post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

__all__ = ["MiniMaxClient"]
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_ai_integration.py -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add src/sightflow_agent/ai_integration.py tests/test_ai_integration.py
git commit -m "feat: add MiniMax client with two-phase reply"
```

---

### 任务 4：配置加载器

**文件：**
- 创建：`src/sightflow_agent/config_loader.py`

- [ ] **步骤 1：编写 merge_config 函数**

```python
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)
from src.sightflow_agent.config import load_contacts, load_roles
from src.sightflow_agent.storage.history_store import normalize_text, ocr_fingerprint
import hashlib

def merge_config(contact_name: str) -> Optional[dict]:
    contacts = load_contacts()
    roles = load_roles()

    contact = contacts.get(contact_name)
    if not contact or not contact.get("enabled"):
        return None

    role_name = contact.get("role")
    role = roles.get(role_name, {})
    if not role:
        return None

    return {
        "name": role.get("name", contact_name),
        "system_prompt": contact.get("system_prompt") or role.get("system_prompt", ""),
        "temperature": contact.get("temperature") or role.get("temperature", 0.7),
        "min_delay": contact.get("min_delay", role.get("min_delay", 1.0)),
        "max_delay": contact.get("max_delay") or role.get("max_delay", 5.0)),
    }

def should_skip(contact_name: str, ocr_text: str, store) -> bool:
    current_hash = ocr_fingerprint(ocr_text)
    last_hash = store.get_ocr_hash(contact_name)
    if current_hash == last_hash:
        return True
    store.save_ocr_hash(contact_name, current_hash)
    return False
```

- [ ] **步骤 2：Commit**

```bash
git add src/sightflow_agent/config_loader.py
git commit -m "feat: add config loader with merge_config and skip logic"
```

---

### 任务 5：修改 agent.py _ai_reply

**文件：**
- 修改：`src/sightflow_agent/agent.py`

- [ ] **步骤 1：读取现有 _ai_reply 代码位置**

在 `_ai_reply` 方法处替换为完整实现。

- [ ] **步骤 2：编写新的 _ai_reply**

```python
def _ai_reply(self, messages: List[Message]) -> Optional[str]:
    """AI 生成回复"""
    if not messages:
        return None

    contact = messages[0].sender  # 第一个消息的发送者作为联系人名
    ocr_text = "\n".join(m.messages for m in messages)

    # 加载配置
    from .config_loader import merge_config, should_skip
    from .storage.history_store import HistoryStore
    from .ai_integration import MiniMaxClient
    import os

    config = merge_config(contact)
    if not config:
        return None

    # 防循环检查
    db_path = os.getenv("HISTORY_DB", "data/chat_history.db")
    store = HistoryStore(db_path)
    if should_skip(contact, ocr_text, store):
        logger.info(f"[VisionAgent] OCR 未变，跳过 {contact}")
        return None

    # 加载历史
    history = store.get_history(contact)

    # 两次调用
    client = MiniMaxClient()
    reply = client.two_phase_reply(
        ocr_text=ocr_text,
        system_prompt=config["system_prompt"],
        history=history
    )

    # 保存回复
    store.add_message(contact, "assistant", reply)

    # 人类延迟
    import random, asyncio
    delay = random.uniform(config["min_delay"], config["max_delay"])
    asyncio.sleep(delay)

    return reply
```

- [ ] **步骤 3：Commit**

```bash
git add src/sightflow_agent/agent.py
git commit -m "feat: implement _ai_reply with MiniMax two-phase call"
```

---

### 任务 6：配置文件

**文件：**
- 创建：`src/sightflow_agent/config/contacts.json`
- 创建：`src/sightflow_agent/config/roles.json`
- 创建：`.env.example`

- [ ] **步骤 1：创建 contacts.json**

```json
{
    "contacts": {
        "张三": {
            "role": "friend",
            "enabled": true
        }
    }
}
```

- [ ] **步骤 2：创建 roles.json**

```json
{
    "roles": {
        "friend": {
            "name": "朋友",
            "system_prompt": "你是一个热情开朗的朋友，说话轻松活泼...",
            "temperature": 0.8,
            "min_delay": 1.5,
            "max_delay": 4.0
        }
    }
}
```

- [ ] **步骤 3：创建 .env.example**

```
MINIMAX_API_KEY=your-api-key-here
MINIMAX_API_BASE=https://api.minimax.chat/v1
MINIMAX_PARSE_MODEL=MiniMax-Text-01
MINIMAX_REPLY_MODEL=MiniMax-M2.7
HISTORY_DB=data/chat_history.db
```

- [ ] **步骤 4：Commit**

```bash
git add src/sightflow_agent/config/contacts.json src/sightflow_agent/config/roles.json .env.example
git commit -m "feat: add default contacts and roles config"
```

---

## 自检清单

**规格覆盖度：**
- [x] 防循环机制（normalize + md5 hash）
- [x] 历史消息顺序（ASC + system 在前）
- [x] 两次调用分离（轻量解析 + 角色回复）
- [x] 配置合并（contact 覆盖 role 默认值）
- [x] SQLite 表结构（chat_history + ocr_state）
- [x] 人类延迟模拟
- [x] .env 敏感信息分离

**占位符扫描：**
- 无 "待定"、"TODO"、"后续实现"

**类型一致性：**
- `HistoryStore` 方法贯穿：`add_message` / `get_history` / `save_ocr_hash` / `get_ocr_hash`
- `MiniMaxClient.two_phase_reply` 参数：`ocr_text` / `system_prompt` / `history` / `parse_model` / `reply_model`
