"""
Telegram channel.

Thin interface layer: receives Telegram messages, passes them to the agent
via runner.run(), and renders the response. Knows nothing about LangGraph
internals. Uses TelegramHook to emit typing indicators and tool-use feedback.
Inspired by Nanobot's channel/interface separation pattern.
"""

from __future__ import annotations

import os
import time

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.agent.hook import AgentHook, ToolEvent
from src.agent.context import ContextBuilder, load_base_prompt, load_notion_prompt
from src.agent.skills import SkillRegistry
from src.agent import loop, runner
from src.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ALLOWED_USERS,
    IS_LOCAL,
    OLLAMA_MODEL,
    OLLAMA_HOST,
    AGENT_LANGUAGE,
    NOTION_AGENT_INSTRUCTIONS,
)
from src.tools.notion_mcp import get_notion_tools

if IS_LOCAL:
    from langchain_ollama import ChatOllama

if IS_LOCAL:
    logger.add(
        "logs/{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        serialize=True,
    )
else:
    logger.add(
        lambda msg: print(msg.strip(), flush=True),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        colorize=False,
    )


# ---------------------------------------------------------------------------
# Hook — Telegram-specific lifecycle events
# ---------------------------------------------------------------------------

class TelegramHook(AgentHook):
    """Sends typing indicators and tool-use feedback to the Telegram chat."""

    def __init__(self, update: Update) -> None:
        self._update = update

    async def on_iteration_start(self, user_id: str) -> None:
        await self._update.message.reply_chat_action("typing")

    async def on_tool_start(self, user_id: str, event: ToolEvent) -> None:
        logger.debug("[%s] Tool started: %s", user_id, event.name)
        # Keep "typing" indicator alive while a tool runs
        await self._update.message.reply_chat_action("typing")


# ---------------------------------------------------------------------------
# Agent factory (cached per chat session)
# ---------------------------------------------------------------------------

def _build_agent(user_id: int):
    """Initialise the LangGraph agent for a Telegram user."""
    uid_str = str(user_id)

    model = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_HOST, num_ctx=4096)
    logger.info("[%s] Model loaded: %s @ %s", uid_str, OLLAMA_MODEL, OLLAMA_HOST)

    all_tools = get_notion_tools()
    if not all_tools:
        raise RuntimeError("Notion MCP tools unavailable")
    logger.info("[%s] Tools loaded: %d — %s", uid_str, len(all_tools), [t.name for t in all_tools])

    # Build the system prompt with all available skills
    ctx = ContextBuilder(
        base_prompt=load_base_prompt(),
        skills=SkillRegistry(),
        language=AGENT_LANGUAGE,
    )
    system_prompt = ctx.build()
    logger.info("[%s] System prompt: %d chars (~%d tokens)", uid_str, len(system_prompt), len(system_prompt) // 4)

    return loop.create_agent(
        tools=all_tools,
        model=model,
        system_prompt=system_prompt,
        notion_system_prompt=NOTION_AGENT_INSTRUCTIONS or None,
        user_id=uid_str,
    )


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_user.id
    if TELEGRAM_ALLOWED_USERS and user_id not in TELEGRAM_ALLOWED_USERS:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        logger.warning("[%s] Unauthorized /start attempt", user_id)
        return

    await update.message.reply_text(
        "👋 Hello! I'm your work assistant. How can I help you today?"
    )
    logger.info("[%s] User started bot", user_id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward user message to the agent via runner.run()."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name

    if TELEGRAM_ALLOWED_USERS and user_id not in TELEGRAM_ALLOWED_USERS:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        logger.warning("[%s] Unauthorized message from @%s", user_id, username)
        return

    user_text = update.message.text
    logger.info("[%s] (@%s) %d chars: %s", user_id, username, len(user_text), user_text[:80])

    # Initialise agent once per chat session and cache it
    if "agent" not in context.chat_data:
        t_init = time.perf_counter()
        try:
            context.chat_data["agent"] = _build_agent(user_id)
        except RuntimeError as exc:
            logger.error("[%s] Agent init failed: %s", user_id, exc)
            await update.message.reply_text(
                "⚠️ No puedo conectarme a Notion en este momento. "
                "El servidor MCP no está disponible. Inténtalo de nuevo en unos segundos."
            )
            return
        logger.info("[%s] Agent initialised in %.2fs", user_id, time.perf_counter() - t_init)
    else:
        logger.debug("[%s] Reusing cached agent", user_id)

    hook = TelegramHook(update)
    t_invoke = time.perf_counter()

    try:
        reply = await runner.run(
            agent=context.chat_data["agent"],
            message=user_text,
            user_id=str(user_id),
            hook=hook,
        )
    except Exception as exc:
        logger.exception("[%s] Agent error: %s", user_id, exc)
        reply = "⚠️ An error occurred. Please try again."

    logger.info(
        "[%s] Responded in %.2fs (%d chars): %s",
        user_id,
        time.perf_counter() - t_invoke,
        len(reply),
        reply[:300],
    )

    try:
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.warning("[%s] Markdown parse failed, retrying as plain text", user_id)
        await update.message.reply_text(reply)


async def shutdown(application: "Application") -> None:
    logger.info("Bot shutdown")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_bot() -> None:
    """Build and start the Telegram bot."""
    from src.tools.notion_mcp import init_notion_mcp_tools

    init_notion_mcp_tools()

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_shutdown(shutdown)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    webhook_mode = os.environ.get("TELEGRAM_WEBHOOK_URL")
    if webhook_mode:
        webhook_url = f"{webhook_mode}/webhook"
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 10000)),
            url_path="webhook",
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
        logger.info("Starting Telegram bot in webhook mode")
    else:
        logger.info("Starting Telegram bot in polling mode")
        application.run_polling(allowed_updates=Update.ALL_TYPES)