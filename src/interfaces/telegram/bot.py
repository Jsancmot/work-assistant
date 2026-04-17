"""
Telegram bot interface for the work-assistant agent.

Each user message is forwarded to the Agno agent and the response is sent back.
The interface is intentionally thin so that the agent logic stays framework-agnostic
and can be reused by future interfaces (WhatsApp, Teams, …).
"""

import asyncio
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.agent.agent import create_agent
from src.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    await update.message.reply_text(
        "👋 Hello! I'm your work assistant. How can I help you today?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward every user message to the agent and reply with its response."""
    user_text = update.message.text
    logger.info("Received message from user %s", update.effective_user.id)

    # Retrieve or create a per-chat agent instance stored in chat_data
    if "agent" not in context.chat_data:
        context.chat_data["agent"] = create_agent()
    agent = context.chat_data["agent"]

    await update.message.reply_chat_action("typing")

    try:
        # Run the synchronous agent call in a thread to avoid blocking the event loop
        response = await asyncio.to_thread(agent.run, user_text)
        reply = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.exception("Agent error: %s", exc)
        reply = "⚠️ An error occurred while processing your request. Please try again."

    # Try Markdown first; fall back to plain text if parsing fails
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

    logger.info("Starting Telegram bot…")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
