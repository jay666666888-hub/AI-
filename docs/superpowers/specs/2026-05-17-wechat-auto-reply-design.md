# 微信自动回复系统设计

**日期**: 2026-05-17
**项目**: wechat-auto-reply
**技术栈**: SightFlow Desktop Agent + MiniMax API + better-sqlite3

---

## 1. 架构

```
wechat-auto-reply/
├── providers/
│   └── wechat-minimax/        # Provider 包
│       ├── manifest.json
│       ├── provider.bundle.js
│       └── config/
│           ├── contacts.json   # 联系人配置
│           └── roles.json      # 角色配置
├── src/
│   ├── ocr-parser.ts          # OCR 文本解析
│   ├── contact-manager.ts      # 联系人/角色管理
│   ├── chat-store.ts          # SQLite 对话历史
│   └── reply-generator.ts      # MiniMax 调用
├── data/
│   └── chat.db                # SQLite 数据库
└── package.json
```

---

## 2. 核心流程

```
1. 截图 + OCR → 原始文本
2. OCR 归一化 → md5 hash → 防循环判断
3. 轻量模型解析 → 提取最新对方消息
4. 加载历史 + 角色配置 → 构建消息
5. 角色模型生成回复
6. 模拟人类延迟
7. 发送回复 → 保存历史
```

---

## 3. 防循环机制

微信截图每分钟时间戳变化，直接 md5 会导致哈希失效。

```typescript
function normalizeOcr(text: string): string {
  return text
    .replace(/\d{1,2}:\d{2}/g, '')  // 去掉时间
    .replace(/\s+/g, ' ')
    .trim();
}

const currentOcrHash = md5(normalizeOcr(ocrText));
```

对比哈希判断是否有新消息触发。

---

## 4. 历史消息顺序

```typescript
// 正确：时间顺序交替，系统在最前
const messages = [
  { role: 'system', content: role.systemPrompt },
  ...history,  // 已按时间 ASC 排序
  { role: 'user', content: latestForeignMessage }
];
```

---

## 5. 两次调用分离

单聊 OCR 无法区分左右气泡，用两次调用分离职责：

```typescript
// 第一次：轻量解析模型
const parsed = await callMiniMax({
  model: 'MiniMax-Text-01',
  messages: [{
    role: 'user',
    content: `提取最新一条对方消息，只返回内容：\n${ocrText}`
  }],
  max_tokens: 200
});

// 第二次：角色模型回复
const reply = await callMiniMax({
  model: 'MiniMax-M2.7',
  messages: [
    { role: 'system', content: role.systemPrompt },
    ...history,
    { role: 'user', content: parsed }
  ]
});
```

---

## 6. 配置合并规则

联系人配置覆盖角色默认值。

```typescript
function mergeConfig(role: RoleConfig, contact: ContactConfig): RoleConfig {
  return {
    name: contact.role,
    systemPrompt: contact.systemPrompt ?? role.systemPrompt,
    temperature: contact.temperature ?? role.temperature,
    minDelay: contact.minDelay ?? role.minDelay,
    maxDelay: contact.maxDelay ?? role.maxDelay,
  };
}
```

---

## 7. SQLite 表结构

```sql
CREATE TABLE chat_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  contact_name TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  timestamp INTEGER NOT NULL,
  is_self INTEGER DEFAULT 0
);
CREATE INDEX idx_contact_time ON chat_history(contact_name, timestamp DESC);

CREATE TABLE ocr_state (
  contact_name TEXT PRIMARY KEY,
  ocr_hash TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);
```

---

## 8. 构建依赖

```json
{
  "scripts": {
    "rebuild": "electron-rebuild -f -w better-sqlite3"
  },
  "devDependencies": {
    "better-sqlite3": "^11.0.0",
    "electron-rebuild": "^3.2.9"
  }
}
```
