# tbot

Telegram-native trading assistant for creating, buying, selling, and managing memecoins with safety and efficiency. The repository now contains a functional prototype bot with order bundling logic tuned for 5/10/15/20/25 wallet cohorts.

## Features

- Slash commands for trading (`/buy`, `/sell`), portfolio inspection, safety checks, and dynamic bundler tuning (`/bundler`).
- Order orchestration service that batches swaps into wallet-count thresholds (5, 10, 15, 20, 25) before execution.
- Mock routing engine to simulate on-chain settlement and ledger updates.
- Wallet manager that provisions custodial wallets for Telegram users.
- Safety scoring helper for quick honeypot/tax checks.

## Project Structure

```
src/tbot/
  models.py                # Shared dataclasses for orders, bundles, wallets
  services/
    bundler.py             # Threshold-aware bundler implementation
    order_service.py       # Order orchestration and mock execution layer
    safety.py              # Token safety scoring helper
    wallets.py             # Wallet lifecycle management
  telegram/
    app.py                 # Telegram application factory
    handlers.py            # Command handlers wired into python-telegram-bot
__main__.py                # Entry point for `python -m tbot`
```

## Requirements

- Python 3.11+
- [python-telegram-bot 21.x](https://docs.python-telegram-bot.org/)

Install dependencies with `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running the bot

1. Create a Telegram bot via [@BotFather](https://t.me/botfather) and obtain the token.
2. Export the token: `export TELEGRAM_BOT_TOKEN=123456:ABCDEF`.
3. Start polling: `python -m tbot`.
4. DM your bot on Telegram and issue `/start`, `/buy <token> <amount>`, `/sell <token> <amount>`, `/portfolio`, `/safety <token>`, `/bundler <wallets>`.

Orders are placed into the bundler until enough unique wallets join. Use `/bundler 5|10|15|20|25` to choose the minimum wallet cohort for execution. When a threshold is reached the batch is executed and all participating wallets receive a simulated fill.

## Tests

```bash
pip install -e .[test]
pytest
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Core User Flows](docs/user_flows.md)

## Roadmap

- Replace mock execution with chain adapters (EVM + Solana).
- Persist wallets, bundles, and trade history in PostgreSQL/Redis.
- Integrate real safety services (decompiled bytecode, simulation, blacklist feeds).
- Support advanced commands like `/snipe`, `/auto`, and `/withdraw` with conversational flows.
