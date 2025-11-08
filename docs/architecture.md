# Architecture Overview

This document outlines the high-level architecture for the Telegram trading bot platform. The solution enables users to interact with on-chain liquidity from within Telegram while the backend performs batching, routing, and safety checks to reduce costs and risk.

## Component Diagram

```
Telegram Client → Bot Webhook/API → Command Router → Orchestration Service
                                      ↓                    ↓
                                   API Gateway        Simulation & Safety
                                      ↓                    ↓
                               Order Queue & Ledger ← Bundler Service
                                      ↓
                                 Chain Adapters (EVM/Solana)
                                      ↓
                                  On-Chain Liquidity
```

## Telegram Interface

- **Bot API**: Exposes commands through webhook delivery. Production deployments should host the webhook behind HTTPS (e.g., Cloudflare + Load Balancer) while local development can rely on ngrok.
- **Command Parser & FSM**: Parses slash commands and manages conversational state for multi-step workflows such as `/snipe` and `/auto` strategies.
- **Session Auth**: Derives authentication from Telegram `user_id` combined with short-lived session tokens that are minted after the first interaction.

## API Gateway

- **Responsibilities**: Terminates TLS, enforces per-user/chat rate limits, performs request logging, and generates idempotency keys per command execution.
- **Technology**: A lightweight FastAPI/Express service with Redis-backed rate limiter and PostgreSQL persistence for idempotency tracking.

## Order Orchestration Service

- Converts validated intents into chain-specific `Order` objects with a strict schema.
- Performs pre-trade validations, chain simulations, routing selection, and submits execution requests to the Bundler service.
- Handles post-trade accounting, position updates, and emits events for observability pipelines.

## Chain Adapters

### EVM Adapter

- Built with `viem`/`ethers.js` for RPC interaction.
- Integrates with Uniswap V2/V3, Sushi, and other EVM DEX routers.
- Supports Permit2 approvals and private transaction submission through Flashbots or MEV-Share.

### Solana Adapter

- Uses `@solana/web3.js` for transaction construction.
- Routes trades through Jupiter and Raydium aggregators.
- Supports priority fees and Jito bundles for MEV-safe submission.

## Simulation & Safety Service

- Performs static analysis of token bytecode and ABIs to detect blacklist/whitelist mechanics, honeypots, and ownership controls.
- Runs dynamic simulations via archive nodes or Tenderly/Anvil forks to validate swaps before execution.
- Produces a risk score surfaced by the `/safety` command.

## Bundler Service

- **Intra-user batching**: Aggregates multiple swaps for the same user/token into one on-chain transaction to minimize gas.
- **Inter-user batching**: Coalesces orders targeting the same pool, executes a single on-chain swap, and allocates fills internally via the sub-ledger.
- **Runtime threshold control**: The Python prototype exposes a `/bundler` command to toggle minimum wallet cohorts (5, 10, 15, 20, 25) before triggering execution.
- **MEV-safe submission**: Manages nonces, gas escalation (Replace-By-Fee), and integrates with private relays (Flashbots, MEV-Share, Jito).

## Wallet & Custody

- Supports a non-custodial mode where users connect external wallets and sign transactions.
- Offers "smart-custody" via per-user keys stored in HSM/Vault/KMS or ERC-4337 smart accounts with bundled gas payments.

## Accounting & Ledger

- Maintains a sub-ledger for inter-user batch allocations.
- Tracks per-token positions (average cost basis, realized PnL) and deposit/withdrawal records.

## Storage & Data

- **PostgreSQL**: Persistent storage for orders, positions, and execution history.
- **Redis**: Hot state for mempool monitoring, distributed locks, and rate limiter counters.
- **S3/Blob Storage**: Archive of logs, simulation traces, and artifacts.

## Observability

- Structured logging across services (JSON logs for ingestion into ELK/Datadog).
- Distributed tracing (OpenTelemetry) for end-to-end transaction visibility.
- Metrics and alerting on stuck mempool transactions, revert spikes, and slippage anomalies.

## Deployment Considerations

- Use containerized services (Docker/Kubernetes) with separate autoscaling policies for latency-sensitive components (API, orchestration) and compute-heavy simulation jobs.
- Implement feature flags to gradually roll out new routing strategies or safety checks.
- Secure secrets via Vault/KMS and enforce least privilege across infrastructure.
