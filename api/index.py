"""
Vercel serverless entry point for the Telegram bot.
Uses FastAPI to handle webhook requests from Telegram.

Note: This file is only used in dev/prod environments (serverless/Vercel).
For local development, use `python -m src.main` which runs in polling mode.
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from loguru import logger
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import TELEGRAM_BOT_TOKEN, IS_LOCAL
from src.interfaces.telegram.bot import start, handle_message

if IS_LOCAL:
    logger.warning(
        "api/index.py is designed for serverless environments. "
        "Use `python -m src.main` for local development."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage bot lifecycle using lifespan context manager."""
    bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    await bot_app.initialize()
    app.state.bot = bot_app
    logger.info("Bot application started")
    yield
    await bot_app.stop()
    await bot_app.shutdown()
    logger.info("Bot application stopped")


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook from Telegram."""
    bot = request.app.state.bot
    data = await request.json()
    update = Update.de_json(data, bot.bot)
    await bot.process_update(update)
    return Response(status_code=200)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "bot": "work-assistant"}


@app.get("/set-webhook")
async def set_webhook():
    """Set webhook URL (call once after deploy)."""
    webhook_url = os.environ.get("TELEGRAM_WEBHOOK_URL")
    if not webhook_url:
        return {"error": "TELEGRAM_WEBHOOK_URL not set"}

    bot = app.state.bot
    await bot.bot.set_webhook(f"{webhook_url}/webhook")
    return {"status": "webhook set", "url": f"{webhook_url}/webhook"}