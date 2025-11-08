from __future__ import annotations

from decimal import Decimal
from typing import Dict, List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..models import OrderSide
from ..services.order_service import OrderOrchestrator, make_order
from ..services.safety import evaluate_token
from ..services.wallets import WalletManager


class BotContext:
    def __init__(self, orchestrator: OrderOrchestrator, wallets: WalletManager) -> None:
        self.orchestrator = orchestrator
        self.wallets = wallets


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_context: BotContext = context.application.bot_data["bot_context"]
    wallet = bot_context.wallets.create_wallet(update.effective_user.id)
    await update.message.reply_text(
        "Welcome to the memecoin trading bot!\n"
        f"A custodial wallet has been created for you on {wallet.chain}.\n"
        f"Wallet ID: {wallet.wallet_id}\nAddress: {wallet.address}"
    )


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot_context: BotContext = context.application.bot_data["bot_context"]
    wallets = bot_context.wallets.list_wallets(update.effective_user.id)
    if not wallets:
        await update.message.reply_text("No wallets found. Use /start to create one.")
        return
    ledger = bot_context.orchestrator.ledger_snapshot()
    summary: Dict[str, Decimal] = {}
    for wallet in wallets:
        wallet_balances = ledger.get(wallet.wallet_id, {})
        for token, amount in wallet_balances.items():
            summary[f"{token}:{wallet.wallet_id}"] = amount
    if not summary:
        await update.message.reply_text("No filled orders yet.")
        return
    lines = ["<b>Your positions</b>"]
    for key, amount in summary.items():
        token, wallet_id = key.split(":")
        lines.append(f"Token <code>{token}</code> in wallet <code>{wallet_id}</code>: {amount}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_trade(update, context, OrderSide.BUY)


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_trade(update, context, OrderSide.SELL)


async def safety(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /safety <token_address>")
        return
    token_address = context.args[0]
    report = evaluate_token(token_address)
    issues = "\n".join(f"- {issue}" for issue in report.issues) or "No major issues detected"
    await update.message.reply_text(
        f"Safety score for <code>{token_address}</code>: <b>{report.score}</b>\n{issues}",
        parse_mode=ParseMode.HTML,
    )

async def configure_bundler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /bundler <wallet_count>")
        return
    try:
        wallet_count = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Wallet count must be an integer.")
        return
    bot_context: BotContext = context.application.bot_data["bot_context"]
    try:
        bot_context.orchestrator.set_min_wallets(wallet_count)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return
    await update.message.reply_text(
        f"Bundler threshold set to {wallet_count} unique wallets."
    )


async def _handle_trade(update: Update, context: ContextTypes.DEFAULT_TYPE, side: OrderSide) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /buy <token_address> <amount>")
        return
    token_address = context.args[0]
    amount = context.args[1]
    bot_context: BotContext = context.application.bot_data["bot_context"]
    wallets = bot_context.wallets.list_wallets(update.effective_user.id)
    if not wallets:
        await update.message.reply_text("No wallets found. Use /start first.")
        return
    wallet = wallets[0]
    order = make_order(
        user_id=update.effective_user.id,
        wallet_id=wallet.wallet_id,
        token_address=token_address,
        side=side,
        amount=amount,
    )
    results = bot_context.orchestrator.submit_order(order)
    if not results:
        await update.message.reply_text(
            "Order queued for bundling. We'll execute once enough wallets join (5/10/15/20/25)."
        )
        return
    messages: List[str] = []
    for result in results:
        messages.append(
            f"Executed bundle {result.bundle.bundle_id[:8]} for {result.bundle.total_amount} tokens\n"
            f"Wallets involved: {result.bundle.wallet_count()} | Users: {result.bundle.user_count()}\n"
            f"Tx hash: {result.tx_hash}"
        )
    await update.message.reply_text("\n\n".join(messages))
