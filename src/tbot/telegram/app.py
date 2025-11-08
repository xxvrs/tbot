from __future__ import annotations

import logging
import os

from telegram.ext import Application, ApplicationBuilder, CommandHandler

from ..services.order_service import OrderOrchestrator
from ..services.wallets import WalletManager
from .handlers import BotContext, buy, configure_bundler, portfolio, safety, sell, start

logger = logging.getLogger(__name__)


def build_application(token: str | None = None) -> Application:
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN must be configured")

    orchestrator = OrderOrchestrator()
    wallets = WalletManager()

    application: Application = ApplicationBuilder().token(token).build()
    application.bot_data["orchestrator"] = orchestrator
    application.bot_data["wallets"] = wallets
    application.bot_data["bot_context"] = BotContext(orchestrator, wallets)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("portfolio", portfolio))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("sell", sell))
    application.add_handler(CommandHandler("bundler", configure_bundler))
    application.add_handler(CommandHandler("safety", safety))

    logger.info("Telegram application initialized with bundler thresholds 5/10/15/20/25")
    return application


def run_polling(token: str | None = None) -> None:
    application = build_application(token)
    application.run_polling()
