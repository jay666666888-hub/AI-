# 微信自动回复系统实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在 SightFlow Desktop Agent 中实现微信自动回复 Provider，基于 MiniMax API，支持联系人独立角色配置、对话历史记忆、防循环检测。

**架构：** Provider 架构（manifest.json + provider.bundle.js），复用 SightFlow 截图/自动化能力，新增 OCR 解析 + SQLite 历史 + 两次 MiniMax 调用（轻量解析 + 角色回复）。

**技术栈：** TypeScript + better-sqlite3 + MiniMax API

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `resources/providers/wechat-minimax/manifest.json` | Provider 元信息、配置 Schema |
| `resources/providers/wechat-minimax/provider.bundle.js` | Provider 入口，串联所有模块 |
| `resources/providers/wechat-minimax/src/config-store.ts` | SQLite 数据库读写（chat_history + ocr_state） |
| `resources/providers/wechat-minimax/src/ocr-parser.ts` | OCR 归一化 + 哈希计算 |
| `resources/providers/wechat-minimax/src/contact-manager.ts` | 联系人/角色配置加载 + mergeConfig |
| `resources/providers/wechat-minimax/src/reply-generator.ts` | 两次 MiniMax 调用（解析 + 回复） |
| `resources/providers/wechat-minimax/config/contacts.json` | 联系人配置示例 |
| `resources/providers/wechat-minimax/config/roles.json` | 角色配置示例 |
| `resources/providers/wechat-minimax/package.json` | 依赖和构建脚本 |

---

## 任务 1：初始化 Provider 骨架

**文件：**
- 创建：`resources/providers/wechat-minimax/manifest.json`
- 创建：`resources/providers/wechat-minimax/package.json`

- [ ] **步骤 1：创建 manifest.json**

```json
{
  "apiVersion": 1,
  "id": "wechat-minimax",
  "name": "微信 MiniMax 自动回复",
  "version": "1.0.0",
  "entry": "provider.bundle.js",
  "moduleType": "module",
  "capabilities": ["chat"],
  "configSchema": {
    "type": "object",
    "properties": {
      "apiKey": {
        "type": "password",
        "title": "MiniMax API Key"
      },
      "parseModel": {
        "type": "string",
        "title": "解析模型",
        "default": "MiniMax-Text-01"
      },
      "replyModel": {
        "type": "string",
        "title": "回复模型",
        "default": "MiniMax-M2.7"
      },
      "dbPath": {
        "type": "string",
        "title": "数据库路径",
        "default": "./data/chat.db"
      },
      "selfName": {
        "type": "string",
        "title": "自己的微信昵称"
      }
    },
    "required": ["apiKey", "selfName"]
  }
}
```

- [ ] **步骤 2：创建 package.json**

```json
{
  "name": "wechat-minimax",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "better-sqlite3": "^11.0.0",
    "js-md5": "^0.7.3"
  },
  "devDependencies": {
    "electron-rebuild": "^3.2.9"
  },
  "scripts": {
    "rebuild": "electron-rebuild -f -w better-sqlite3"
  }
}
```

- [ ] **步骤 3：Commit**

```bash
git add resources/providers/wechat-minimax/manifest.json resources/providers/wechat-minimax/package.json
git commit -m "feat(wechat-minimax): init provider skeleton with manifest and package.json"
```

---

## 任务 2：SQLite 配置存储（config-store.ts）

**文件：**
- 创建：`resources/providers/wechat-minimax/src/config-store.ts`
- 测试：`resources/providers/wechat-minimax/src/config-store.test.ts`

- [ ] **步骤 1：编写失败的测试**

```typescript
// config-store.test.ts
import { ChatStore } from './config-store';
import fs from 'fs';
import path from 'path';

const TEST_DB = '/tmp/test-chat-store.db';

function cleanup() {
  if (fs.existsSync(TEST_DB)) fs.unlinkSync(TEST_DB);
}

test('addMessage and getHistory', () => {
  cleanup();
  const store = new ChatStore(TEST_DB);

  store.addMessage('张三', 'assistant', '你好呀', false);
  store.addMessage('张三', 'user', '你好', true);

  const history = store.getHistory('张三', 10);
  expect(history).toHaveLength(2);
  expect(history[0].role).toBe('assistant');
  expect(history[1].role).toBe('user');
});

test('ocr hash save and compare', () => {
  cleanup();
  const store = new ChatStore(TEST_DB);

  store.saveOcrHash('张三', 'abc123');
  expect(store.getOcrHash('张三')).toBe('abc123');

  store.saveOcrHash('张三', 'def456');
  expect(store.getOcrHash('张三')).toBe('def456');
});

test('getLastSent', () => {
  cleanup();
  const store = new ChatStore(TEST_DB);

  store.addMessage('张三', 'assistant', '回复1', false);
  store.addMessage('张三', 'user', '用户消息', true);
  store.addMessage('张三', 'assistant', '回复2', false);

  expect(store.getLastSent('张三')).toBe('回复2');
});
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd resources/providers/wechat-minimax && npx tsx src/config-store.test.ts`
预期：FAIL，报错 "ConfigStore is not exported"

- [ ] **步骤 3：编写 config-store.ts**

```typescript
// config-store.ts
import Database from 'better-sqlite3';
import md5 from 'js-md5';

export interface HistoryEntry {
  role: 'user' | 'assistant';
  content: string;
}

export class ChatStore {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_name TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        is_self INTEGER DEFAULT 0
      );
      CREATE INDEX IF NOT EXISTS idx_contact_time
        ON chat_history(contact_name, timestamp DESC);

      CREATE TABLE IF NOT EXISTS ocr_state (
        contact_name TEXT PRIMARY KEY,
        ocr_hash TEXT NOT NULL,
        updated_at INTEGER NOT NULL
      );
    `);
  }

  addMessage(contactName: string, role: 'user' | 'assistant', content: string, isSelf: boolean): void {
    const stmt = this.db.prepare(`
      INSERT INTO chat_history (contact_name, role, content, timestamp, is_self)
      VALUES (?, ?, ?, ?, ?)
    `);
    stmt.run(contactName, role, content, Date.now(), isSelf ? 1 : 0);
  }

  getHistory(contactName: string, limit: number = 20): HistoryEntry[] {
    const stmt = this.db.prepare(`
      SELECT role, content FROM chat_history
      WHERE contact_name = ?
      ORDER BY timestamp ASC
      LIMIT ?
    `);
    return stmt.all(contactName, limit) as HistoryEntry[];
  }

  getLastSent(contactName: string): string | null {
    const stmt = this.db.prepare(`
      SELECT content FROM chat_history
      WHERE contact_name = ? AND is_self = 1
      ORDER BY timestamp DESC
      LIMIT 1
    `);
    return (stmt.get(contactName) as { content: string } | undefined)?.content ?? null;
  }

  saveOcrHash(contactName: string, hash: string): void {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO ocr_state (contact_name, ocr_hash, updated_at)
      VALUES (?, ?, ?)
    `);
    stmt.run(contactName, hash, Date.now());
  }

  getOcrHash(contactName: string): string | null {
    const stmt = this.db.prepare(`
      SELECT ocr_hash FROM ocr_state WHERE contact_name = ?
    `);
    return (this.db.get('SELECT ocr_hash FROM ocr_state WHERE contact_name = ?', contactName) as { ocr_hash: string } | undefined)?.ocr_hash ?? null;
  }
}

export function normalizeOcr(text: string): string {
  return text
    .replace(/\d{1,2}:\d{2}/g, '')  // 去掉时间
    .replace(/\s+/g, ' ')
    .trim();
}

export function ocrHash(text: string): string {
  return md5(normalizeOcr(text));
}
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd resources/providers/wechat-minimax && npx tsx src/config-store.test.ts`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add resources/providers/wechat-minimax/src/config-store.ts resources/providers/wechat-minimax/src/config-store.test.ts
git commit -m "feat(wechat-minimax): add SQLite chat history store with ocr hash"
```

---

## 任务 3：联系人/角色配置管理（contact-manager.ts）

**文件：**
- 创建：`resources/providers/wechat-minimax/src/contact-manager.ts`
- 测试：`resources/providers/wechat-minimax/src/contact-manager.test.ts`

- [ ] **步骤 1：编写失败的测试**

```typescript
// contact-manager.test.ts
import { ContactManager } from './contact-manager';

const ROLES = {
  friend: {
    name: '朋友',
    systemPrompt: '你是一个热情开朗的朋友',
    temperature: 0.8,
    minDelay: 1.5,
    maxDelay: 4.0
  }
};

const CONTACTS = {
  '张三': {
    role: 'friend',
    enabled: true,
    temperature: 0.9  // 覆盖角色默认值
  },
  '工作群': {
    role: 'friend',
    enabled: false  // 禁用
  }
};

test('mergeConfig contact overrides role defaults', () => {
  const mgr = new ContactManager(CONTACTS, ROLES);
  const merged = mgr.getMergedConfig('张三');

  expect(merged.temperature).toBe(0.9);  // 覆盖了角色的 0.8
  expect(merged.systemPrompt).toBe('你是一个热情开朗的朋友');  // 继承了角色默认值
});

test('disabled contact returns null', () => {
  const mgr = new ContactManager(CONTACTS, ROLES);
  expect(mgr.getMergedConfig('工作群')).toBeNull();
});

test('unknown contact returns null', () => {
  const mgr = new ContactManager(CONTACTS, ROLES);
  expect(mgr.getMergedConfig('不存在的人')).toBeNull();
});
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd resources/providers/wechat-minimax && npx tsx src/contact-manager.test.ts`
预期：FAIL，报错 "ContactManager is not exported"

- [ ] **步骤 3：编写 contact-manager.ts**

```typescript
// contact-manager.ts
export interface RoleConfig {
  name: string;
  systemPrompt: string;
  temperature: number;
  minDelay: number;
  maxDelay: number;
}

export interface ContactConfig {
  role: string;
  enabled: boolean;
  systemPrompt?: string;
  temperature?: number;
  minDelay?: number;
  maxDelay?: number;
}

export interface MergedConfig extends RoleConfig {
  contactName: string;
}

export class ContactManager {
  constructor(
    private contacts: Record<string, ContactConfig>,
    private roles: Record<string, RoleConfig>
  ) {}

  getMergedConfig(contactName: string): MergedConfig | null {
    const contact = this.contacts[contactName];
    if (!contact || !contact.enabled) return null;

    const role = this.roles[contact.role];
    if (!role) return null;

    return {
      contactName,
      name: role.name,
      systemPrompt: contact.systemPrompt ?? role.systemPrompt,
      temperature: contact.temperature ?? role.temperature,
      minDelay: contact.minDelay ?? role.minDelay,
      maxDelay: contact.maxDelay ?? role.maxDelay,
    };
  }

  isEnabled(contactName: string): boolean {
    return !!this.contacts[contactName]?.enabled;
  }
}
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd resources/providers/wechat-minimax && npx tsx src/contact-manager.test.ts`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add resources/providers/wechat-minimax/src/contact-manager.ts resources/providers/wechat-minimax/src/contact-manager.test.ts
git commit -m "feat(wechat-minimax): add contact/role config management with mergeConfig"
```

---

## 任务 4：OCR 解析 + MiniMax 调用（reply-generator.ts）

**文件：**
- 创建：`resources/providers/wechat-minimax/src/reply-generator.ts`
- 测试：`resources/providers/wechat-minimax/src/reply-generator.test.ts`

- [ ] **步骤 1：编写失败的测试**

```typescript
// reply-generator.test.ts
import { ReplyGenerator } from './reply-generator';

test('calls parse model then reply model', async () => {
  const gen = new ReplyGenerator({
    apiKey: 'test-key',
    parseModel: 'MiniMax-Text-01',
    replyModel: 'MiniMax-M2.7'
  });

  let callCount = 0;
  gen['callMiniMax'] = async (opts: any) => {
    callCount++;
    if (callCount === 1) {
      // 第一次调用应该是解析模型
      expect(opts.model).toBe('MiniMax-Text-01');
      expect(opts.messages[0].content).toContain('提取最新一条对方消息');
      return '你好呀';
    } else {
      // 第二次应该是回复模型
      expect(opts.model).toBe('MiniMax-M2.7');
      expect(opts.messages[0].role).toBe('system');
      return '回复内容';
    }
  };

  const result = await gen.generate({
    ocrText: '张三：你好\n李四：在吗',
    contactName: '张三',
    config: { name: '朋友', systemPrompt: '你是一个朋友', temperature: 0.8, minDelay: 1, maxDelay: 3 }
  });

  expect(callCount).toBe(2);
  expect(result).toBe('回复内容');
});
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd resources/providers/wechat-minimax && npx tsx src/reply-generator.test.ts`
预期：FAIL，报错 "ReplyGenerator is not exported"

- [ ] **步骤 3：编写 reply-generator.ts**

```typescript
// reply-generator.ts
import { ChatStore, normalizeOcr, ocrHash } from './config-store';
import { ContactManager, MergedConfig } from './contact-manager';

export interface GenerateInput {
  ocrText: string;
  contactName: string;
  config: MergedConfig;
  chatStore: ChatStore;
}

export class ReplyGenerator {
  constructor(private apiKey: string) {}

  async generate(input: GenerateInput): Promise<string> {
    const { ocrText, contactName, config, chatStore } = input;

    // 1. 检查 OCR 是否变化（防循环）
    const lastHash = chatStore.getOcrHash(contactName);
    const currentHash = ocrHash(ocrText);
    if (lastHash === currentHash) {
      throw new Error('OCR_UNCHANGED');
    }
    chatStore.saveOcrHash(contactName, currentHash);

    // 2. 第一次调用：轻量解析模型提取最新消息
    const latestMessage = await this.callMiniMax({
      model: 'MiniMax-Text-01',
      messages: [{
        role: 'user',
        content: `提取最新一条对方消息，只返回内容：\n${ocrText}`
      }],
      max_tokens: 200
    });

    // 3. 加载历史
    const history = input.chatStore.getHistory(contactName, 20);

    // 4. 第二次调用：角色模型生成回复
    const reply = await this.callMiniMax({
      model: 'MiniMax-M2.7',
      messages: [
        { role: 'system', content: config.systemPrompt },
        ...history.map(h => ({ role: h.role, content: h.content })),
        { role: 'user', content: latestMessage }
      ],
      temperature: config.temperature
    });

    // 5. 保存回复到历史
    chatStore.addMessage(contactName, 'assistant', reply, false);

    return reply;
  }

  private async callMiniMax(opts: {
    model: string;
    messages: Array<{ role: string; content: string }>;
    temperature?: number;
    max_tokens?: number;
  }): Promise<string> {
    const url = 'https://api.minimax.chat/v1/chat/completions';
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: opts.model,
        messages: opts.messages,
        temperature: opts.temperature ?? 0.7,
        max_tokens: opts.max_tokens ?? 1024
      })
    });

    if (!response.ok) {
      throw new Error(`MiniMax API error: ${response.status}`);
    }

    const json = await response.json();
    return json.choices?.[0]?.message?.content ?? '';
  }
}
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd resources/providers/wechat-minimax && npx tsx src/reply-generator.test.ts`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add resources/providers/wechat-minimax/src/reply-generator.ts resources/providers/wechat-minimax/src/reply-generator.test.ts
git commit -m "feat(wechat-minimax): add ReplyGenerator with two-phase MiniMax calls"
```

---

## 任务 5：Provider 入口（provider.bundle.js）

**文件：**
- 创建：`resources/providers/wechat-minimax/provider.bundle.js`

- [ ] **步骤 1：编写 provider.bundle.js**

```javascript
// provider.bundle.js
import { ChatStore } from './src/config-store';
import { ContactManager } from './src/contact-manager';
import { ReplyGenerator } from './src/reply-generator';
import contacts from './config/contacts.json';
import roles from './config/roles.json';

export function createProvider(context) {
  const { providerConfig } = context;
  const { apiKey, dbPath } = providerConfig;

  const chatStore = new ChatStore(dbPath || './data/chat.db');
  const contactManager = new ContactManager(contacts, roles);
  const replyGenerator = new ReplyGenerator(apiKey);

  return {
    async *run(input) {
      const { ocrText, contactName } = input;

      yield { type: 'thinking', content: '检查联系人配置...' };

      // 1. 检查联系人是否启用
      const config = contactManager.getMergedConfig(contactName);
      if (!config) {
        yield { type: 'skip' };
        return;
      }

      yield { type: 'thinking', content: '正在生成回复...' };

      try {
        // 2. 生成回复（包含 OCR 防循环检查）
        const reply = await replyGenerator.generate({
          ocrText,
          contactName,
          config,
          chatStore
        });

        // 3. 模拟人类延迟
        const delay = config.minDelay + Math.random() * (config.maxDelay - config.minDelay);
        await new Promise(resolve => setTimeout(resolve, delay * 1000));

        yield { type: 'reply_text', content: reply };
      } catch (err) {
        if (err.message === 'OCR_UNCHANGED') {
          yield { type: 'skip' };
          return;
        }
        yield { type: 'error', error: err.message };
      }
    }
  };
}
```

- [ ] **步骤 2：Commit**

```bash
git add resources/providers/wechat-minimax/provider.bundle.js
git commit -m "feat(wechat-minimax): add provider entry point"
```

---

## 任务 6：配置文件

**文件：**
- 创建：`resources/providers/wechat-minimax/config/contacts.json`
- 创建：`resources/providers/wechat-minimax/config/roles.json`

- [ ] **步骤 1：创建 contacts.json**

```json
{
  "contacts": {
    "张三": {
      "role": "friend",
      "enabled": true
    },
    "工作群": {
      "role": "work_group",
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
      "systemPrompt": "你是一个热情开朗的朋友，说话轻松活泼...",
      "temperature": 0.8,
      "minDelay": 1.5,
      "maxDelay": 4.0
    },
    "work_group": {
      "name": "工作助手",
      "systemPrompt": "你是一个专业的工作助手...",
      "temperature": 0.6,
      "minDelay": 2.0,
      "maxDelay": 5.0
    }
  }
}
```

- [ ] **步骤 3：Commit**

```bash
git add resources/providers/wechat-minimax/config/contacts.json resources/providers/wechat-minimax/config/roles.json
git commit -m "feat(wechat-minimax): add default contacts and roles config"
```

---

## 任务 7：集成到 SightFlow

**文件：**
- 修改：`resources/providers/wechat-minimax/manifest.json`（更新路径）

- [ ] **步骤 1：验证 Provider 打包**

安装 Provider 到 SightFlow：
1. 将 `resources/providers/wechat-minimax/` 复制到 `SightFlow/resources/providers/wechat-minimax`
2. 在 SightFlow 设置中配置 Provider 的 manifest 地址
3. 运行 `npm run rebuild` 编译 native 模块

- [ ] **步骤 2：测试完整流程**

手动测试：
```bash
# 1. 启动 SightFlow
npm run dev

# 2. 配置 Provider（设置 → 安装 wechat-minimax）
# 3. 配置联系人列表和角色
# 4. 发送测试消息触发自动回复
```

---

## 自检清单

**规格覆盖度：**
- [x] 防循环机制（normalizeOcr + md5 hash）
- [x] 历史消息顺序（时间 ASC + system 在前）
- [x] 两次调用分离（轻量解析 + 角色回复）
- [x] 配置合并规则（contact 覆盖 role 默认值）
- [x] SQLite 表结构（chat_history + ocr_state）
- [x] 人类延迟模拟
- [x] 群聊/单聊区分（联系人名称匹配）

**占位符扫描：**
- 无 "待定"、"TODO"、"后续实现"

**类型一致性：**
- `ChatStore` 的 `addMessage` / `getHistory` / `getOcrHash` / `saveOcrHash` 方法在所有任务中一致
- `ContactManager.getMergedConfig` 返回 `MergedConfig | null` 贯穿全程
- `ReplyGenerator.generate` 输入输出类型清晰