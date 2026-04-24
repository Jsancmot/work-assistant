"""
Telegram bot interface using LangGraph agent.
"""

import os
import time

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ALLOWED_USERS,
    IS_LOCAL,
    OLLAMA_MODEL,
    OLLAMA_HOST,
    AGENT_INSTRUCTIONS,
)
from src.tools.notion_mcp import get_notion_tools
from src.agent.langgraph_agent import create_langgraph_agent, run_agent

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_user.id
    if TELEGRAM_ALLOWED_USERS and user_id not in TELEGRAM_ALLOWED_USERS:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        logger.warning(f"[{user_id}] Unauthorized /start attempt")
        return

    await update.message.reply_text(
        "👋 Hello! I'm your work assistant. How can I help you today?"
    )
    logger.info(f"[{user_id}] User started bot")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward user message to LangGraph agent."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name
    if TELEGRAM_ALLOWED_USERS and user_id not in TELEGRAM_ALLOWED_USERS:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        logger.warning(f"[{user_id}] Unauthorized message from @{username}")
        return

    user_text = update.message.text
    logger.info(f"[{user_id}] (@{username}) User message ({len(user_text)} chars): {user_text}")

    if "agent" not in context.chat_data:
        logger.info(f"[{user_id}] No cached agent found — initializing new agent")
        t_init = time.perf_counter()

        logger.info(f"[{user_id}] Loading model: {OLLAMA_MODEL} @ {OLLAMA_HOST} (num_ctx=8192)")
        model = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_HOST, num_ctx=4096)

        all_tools = get_notion_tools()
        if not all_tools:
            logger.error(f"[{user_id}] No Notion tools available — Notion MCP may be unreachable")
            await update.message.reply_text(
                "⚠️ No puedo conectarme a Notion en este momento. "
                "El servidor MCP no está disponible. Inténtalo de nuevo en unos segundos."
            )
            return
        loaded_names = [t.name for t in all_tools]
        logger.info(f"[{user_id}] Tools loaded: {len(all_tools)} — {loaded_names}")

        prompt_chars = len(AGENT_INSTRUCTIONS)
        logger.info(f"[{user_id}] System prompt size: {prompt_chars} chars (~{prompt_chars // 4} tokens)")

        agent = create_langgraph_agent(
            tools=all_tools,
            model=model,
            system_prompt=AGENT_INSTRUCTIONS,
            user_id=user_id,
        )

        context.chat_data["agent"] = agent
        elapsed_init = time.perf_counter() - t_init
        logger.info(f"[{user_id}] Agent initialized in {elapsed_init:.2f}s")
    else:
        logger.debug(f"[{user_id}] Reusing cached agent")

    agent = context.chat_data["agent"]

    await update.message.reply_chat_action("typing")

    t_invoke = time.perf_counter()
    logger.info(f"[{user_id}] Invoking agent...")
    try:
        reply = await run_agent(agent, user_text, user_id)
    except Exception as exc:
        logger.exception(f"[{user_id}] Agent error: {exc}")
        reply = "⚠️ An error occurred. Please try again."

    elapsed_invoke = time.perf_counter() - t_invoke
    logger.info(
        f"[{user_id}] Agent responded in {elapsed_invoke:.2f}s "
        f"({len(reply)} chars): {reply[:300]}"
    )

    try:
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.warning(f"[{user_id}] Markdown parse failed, retrying as plain text")
        await update.message.reply_text(reply)


async def shutdown(application: "Application") -> None:
    logger.info("Bot shutdown")


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
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

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