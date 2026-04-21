"""
Telegram bot interface for the work-assistant agent.

Each user message is forwarded to the Agno agent and the response is sent back.
The interface is intentionally thin so that the agent logic stays framework-agnostic
and can be reused by future interfaces (WhatsApp, Teams, …).
"""

import asyncio
import os
from datetime import datetime

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.agent.agent import create_agent
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USERS, IS_LOCAL

import sys

# Only add file logger in local environment (Docker)
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
    """Forward every user message to the agent and reply with its response."""
    user_id = update.effective_user.id
    if TELEGRAM_ALLOWED_USERS and user_id not in TELEGRAM_ALLOWED_USERS:
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        logger.warning(f"[{user_id}] Unauthorized message")
        return

    user_text = update.message.text
    logger.info(f"[{user_id}] User message: {user_text}")

    if "agent" not in context.chat_data:
        context.chat_data["agent"] = await create_agent()
    agent = context.chat_data["agent"]

    await update.message.reply_chat_action("typing")

    try:
        response = await agent.arun(user_text)
        reply = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.exception(f"[{user_id}] Agent error: {exc}")
        reply = "⚠️ An error occurred while processing your request. Please try again."

    logger.info(f"[{user_id}] Agent response: {reply[:500]}")

    try:
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await update.message.reply_text(reply)


def run_bot() -> None:
    """Build and start the Telegram bot (blocking)."""
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
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
        logger.info("Starting Telegram bot in webhook mode…")
    else:
        logger.info("Starting Telegram bot in polling mode…")
        application.run_polling(allowed_updates=Update.ALL_TYPES)