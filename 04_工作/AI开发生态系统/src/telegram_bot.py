#!/usr/bin/env python3
"""
Telegram Bot - Ralph Ecosystem 入口
两阶段模式: 需求收集 → 自主执行

阶段1: 调用 Claude API 扮演需求分析师，每次问1个关键问题
阶段2: 调用 orchestrator.run_workflow() 自主执行
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Optional

# 环境变量检查
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN 环境变量未设置")

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not CLAUDE_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY 环境变量未设置")

# 导入 Telegram
try:
    import telegram
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        ContextTypes, ConversationHandler, filters
    )
except ImportError:
    raise RuntimeError("python-telegram-bot 未安装. 运行: pip install python-telegram-bot>=22.0")

# 导入生态系统
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecosystem_orchestrator import EcosystemOrchestrator

# ============================================================
# 配置
# ============================================================

# 用户状态
USER_STATES: Dict[int, Dict] = {}  # user_id -> {state, conversation, task_summary, detail}

# 状态定义
STATE_GATHERING = "gathering"  # 阶段1: 需求收集
STATE_EXECUTING = "executing"  # 阶段2: 自主执行

# Claude API 配置
CLAUDE_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")

# ============================================================
# 阶段1: 需求分析师 (Claude API)
# ============================================================

ANALYST_SYSTEM_PROMPT = """你是需求分析师。每次只问1个最关键的问题，不超过2轮。
用户回复后判断：信息足够时输出：---READY---\n{task_summary}

判断任务是否足够清晰的标准：
- 任务目标明确 (做什么)
- 涉及范围清晰 (做到什么程度)
- 没有重大歧义

问问题时的风格：简洁明了，聚焦最重要的一点，避免引导性提问。"""

ANALYST_MAX_TURNS = 2  # 最多追问2轮


def call_claude_api(messages: list) -> str:
    """调用 Claude API 获取响应"""
    import httpx

    headers = {
        "Authorization": f"Bearer {CLAUDE_API_KEY}",
        "Content-Type": "application/json",
        "x-api-key": CLAUDE_API_KEY
    }

    payload = {
        "model": "MiniMax-M2",
        "messages": messages,
        "max_tokens": 800,
        "temperature": 0.7
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{CLAUDE_BASE_URL}/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    except Exception as e:
        return f"API调用失败: {str(e)}"


def analyze_requirement(conversation_history: list, user_message: str) -> tuple[str, bool, str]:
    """
    分析用户需求

    Returns:
        (response_to_user, is_ready, task_summary)
        - response_to_user: 要回复用户的话
        - is_ready: True 表示可以开始执行
        - task_summary: 任务摘要（如果 is_ready=True）
    """
    messages = [
        {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
        *conversation_history,
        {"role": "user", "content": user_message}
    ]

    response = call_claude_api(messages)

    # 检查是否包含 ---READY---
    if "---READY---" in response:
        parts = response.split("---READY---")
        task_summary = parts[1].strip() if len(parts) > 1 else parts[0].strip()
        return response, True, task_summary
    else:
        return response, False, ""


# ============================================================
# 阶段2: 自主执行
# ============================================================

class ProgressCapture:
    """捕获 orchestrator 输出并实时推送"""

    def __init__(self, bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self.last_msg_id = None

    def send(self, text: str):
        """发送进度消息"""
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._send_async(text))

    async def _send_async(self, text: str):
        msg = await self.bot.send_message(
            chat_id=self.chat_id,
            text=f"🔄 {text}"
        )
        self.last_msg_id = msg.message_id

    def update(self, text: str):
        """更新最后一条消息"""
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._update_async(text))

    async def _update_async(self, text: str):
        if self.last_msg_id:
            try:
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.last_msg_id,
                    text=f"✅ {text}"
                )
            except:
                pass


async def execute_task(task_summary: str, user_id: int, app: Application) -> str:
    """执行任务并推送进度"""
    project_path = "/mnt/e/黑曜石/04_工作/AI开发生态系统"
    orch = EcosystemOrchestrator(project_path)
    orch.load_adapters()

    progress = ProgressCapture(app.bot, user_id)

    # 发送开始消息
    await app.bot.send_message(
        chat_id=user_id,
        text=f"🔄 开始执行任务...\n\n📋 {task_summary}"
    )

    try:
        # 执行工作流 - 捕获输出
        import io
        from contextlib import redirect_stdout

        output_buffer = io.StringIO()

        def progress_callback(stage_name: str, status: str, detail: str = ""):
            """进度回调"""
            msg = f"{stage_name}"
            if detail:
                msg += f": {detail}"
            app.bot.send_message(chat_id=user_id, text=f"🔄 {msg}")

        # 直接调用并捕获
        result = orch.run_workflow(task_summary, mode="auto")

        # 构建报告
        success_count = result.get("success_count", 0)
        total_stages = result.get("stages_completed", 0)
        quality_score = result.get("quality_score", 0)
        ece = result.get("ece", 0)

        route = result.get("route", {})
        report = f"""
✅ 任务执行完成

📊 执行摘要:
   • 完成阶段: {success_count}/{total_stages}
   • 质量分数: {quality_score:.2f}
   • ECE校准: {ece:.3f}

📋 路由结果:
   • 类型: {route.get('task_type', 'unknown')}
   • Skills: {route.get('recommended_skills', [])}
   • Layers: {route.get('recommended_layers', [])}
"""

        # 获取 Reality Alignment 状态
        ra_status = orch.get_reality_alignment_status()
        cal = ra_status.get("calibration", {})
        delayed = ra_status.get("delayed_outcomes", {})

        if cal.get("ece_by_task_type"):
            report += "\n📈 ECE校准:"
            for tt, ece_val in cal["ece_by_task_type"].items():
                report += f"\n   • {tt}: {ece_val:.3f}"

        if delayed:
            report += f"\n⏱️ 延迟跟踪:"
            report += f"\n   • 待处理: {delayed.get('pending_checks', 0)}"
            report += f"\n   • 追踪任务: {delayed.get('total_tracked', 0)}"
            report += f"\n   • 延迟失败率: {delayed.get('delayed_failure_rate', 0):.1%}"

        return report

    except Exception as e:
        return f"❌ 执行失败:\n{str(e)}"


# ============================================================
# Telegram Handlers
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """欢迎消息"""
    user_id = update.message.chat_id

    USER_STATES[user_id] = {
        "state": STATE_GATHERING,
        "conversation": [],
        "task_summary": None,
        "turns": 0
    }

    welcome = """
👋 欢迎使用 Ralph Ecosystem Bot

我是你的 AI 开发助手，采用两阶段工作模式：

📌 阶段1 - 需求收集
   我会问你问题，直到任务足够清晰
   这个阶段我不会执行任何操作

📌 阶段2 - 自主执行
   确认任务后，我会自动执行
   每个步骤完成会通知你

请描述你的任务或需求。
"""

    await update.message.reply_text(welcome)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息"""
    user_id = update.message.chat_id
    text = update.message.text.strip()

    if not text:
        return

    # 初始化用户状态 (如果不存在)
    if user_id not in USER_STATES:
        USER_STATES[user_id] = {
            "state": STATE_GATHERING,
            "conversation": [],
            "task_summary": None,
            "turns": 0
        }

    user_state = USER_STATES[user_id]

    # 阶段1: 需求收集
    if user_state["state"] == STATE_GATHERING:
        # 添加用户消息到历史
        user_state["conversation"].append({"role": "user", "content": text})
        user_state["turns"] += 1

        # 调用需求分析
        response, is_ready, task_summary = analyze_requirement(
            user_state["conversation"][:-1],
            text
        )

        # 添加助手回复到历史
        user_state["conversation"].append({"role": "assistant", "content": response})

        if is_ready:
            # 信息足够，进入阶段2
            user_state["task_summary"] = task_summary
            user_state["state"] = STATE_EXECUTING

            confirm_msg = f"""
📋 任务摘要:

{task_summary}

🔧 进入阶段2 - 自主执行?

回复 "确认" 开始执行，或继续补充信息。
"""
            await update.message.reply_text(confirm_msg)

        elif user_state["turns"] >= ANALYST_MAX_TURNS:
            # 超过最大追问轮次，直接进入执行
            user_state["task_summary"] = text
            user_state["state"] = STATE_EXECUTING
            await update.message.reply_text(
                f"📌 信息收集完成，直接进入执行阶段。\n\n🔄 开始执行: {text}"
            )
            result = await execute_task(text, user_id, context.bot)
            await update.message.reply_text(result)

            # 重置状态
            user_state["state"] = STATE_GATHERING
            user_state["conversation"] = []
            user_state["turns"] = 0

        else:
            # 继续问问题
            await update.message.reply_text(response)

    # 阶段2: 等待确认
    elif user_state["state"] == STATE_EXECUTING:
        if "确认" in text:
            task_summary = user_state.get("task_summary") or text
            result = await execute_task(task_summary, user_id, context.bot)
            await update.message.reply_text(result)

            # 重置状态
            user_state["state"] = STATE_GATHERING
            user_state["conversation"] = []
            user_state["task_summary"] = None
            user_state["turns"] = 0
        else:
            # 取消，回到阶段1
            user_state["state"] = STATE_GATHERING
            user_state["conversation"] = []
            user_state["turns"] = 0
            await update.message.reply_text("📌 已取消执行。继续补充信息。")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """取消当前任务"""
    user_id = update.message.chat_id

    if user_id in USER_STATES:
        USER_STATES[user_id] = {
            "state": STATE_GATHERING,
            "conversation": [],
            "task_summary": None,
            "turns": 0
        }

    await update.message.reply_text("❌ 已取消当前任务。\n\n可以描述新任务。")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看当前状态"""
    user_id = update.message.chat_id

    if user_id not in USER_STATES:
        await update.message.reply_text("📌 无进行中的任务。")
        return

    user_state = USER_STATES[user_id]
    state = user_state.get("state", STATE_GATHERING)
    turns = user_state.get("turns", 0)
    summary = user_state.get("task_summary", "未设置")

    state_text = {
        STATE_GATHERING: "📌 阶段1 - 需求收集",
        STATE_EXECUTING: "🔄 阶段2 - 等待确认"
    }.get(state, "未知")

    status = f"""
📊 当前状态:

{state_text}
对话轮数: {turns}/{ANALYST_MAX_TURNS}
任务摘要: {summary if summary else "(未设置)"}
"""
    await update.message.reply_text(status)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """帮助信息"""
    help_text = """
📖 Ralph Ecosystem Bot 帮助

命令:
/start - 开始新任务
/status - 查看当前状态
/cancel - 取消当前任务
/help - 显示此帮助

工作模式:
1. 描述你的任务或需求
2. 我会问一些问题来明确目标（最多2轮）
3. 确认后自动执行
4. 执行期间实时通知进度

示例任务:
• "部署一个 Python Web 服务"
• "分析六肖预测系统的表现"
• "构建一个 REST API"
"""
    await update.message.reply_text(help_text)


# ============================================================
# 主程序
# ============================================================

def main():
    """启动 Bot"""
    print("=" * 50)
    print("  Ralph Ecosystem Telegram Bot")
    print("=" * 50)
    print(f"Bot Token: {BOT_TOKEN[:10]}...")
    print("=" * 50)

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("✅ Bot 启动成功!")
    print("📱 发送 /start 开始使用")
    print("=" * 50)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
