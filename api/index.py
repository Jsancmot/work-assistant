"""
Vercel serverless entry point for the Telegram bot.
Uses FastAPI to handle webhook requests from Telegram.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Request, Response
from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.config import TELEGRAM_BOT_TOKEN
from src.interfaces.telegram.bot import start, handle_message

app = FastAPI()

# Store application instance globally
_bot_app: Application = None


@app.on_event("startup")
async def startup():
    """Initialize the bot application."""
    global _bot_app

    _bot_app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    _bot_app.add_handler(CommandHandler("start", start))
    _bot_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    await _bot_app.initialize()
    await _bot_app.start()
    logger.info("Bot application started")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown the bot application."""
    global _bot_app
    if _bot_app:
        await _bot_app.stop()
        await _bot_app.shutdown()
        logger.info("Bot application stopped")


@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook from Telegram."""
    global _bot_app

    data = await request.json()
    update = Update.de_json(data, _bot_app.bot)

    await _bot_app.process_update(update)
    return Response(status_code=200)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "bot": "work-assistant"}


@app.get("/set-webhook")
async def set_webhook():
    """Set webhook URL (call once after deploy)."""
    global _bot_app

    webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")
    if not webhook_url:
        return {"error": "TELEGRAM_WEBHOOK_URL not set"}

    await _bot_app.bot.set_webhook(f"{webhook_url}/webhook")
    return {"status": "webhook set", "url": f"{webhook_url}/webhook"}
