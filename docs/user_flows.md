# Core User Flows

This document summarizes the expected Telegram bot commands and the backend steps that power each action.

## `/start`
1. Prompt the user to create a managed wallet or connect an external wallet.
2. Allow the user to choose default chains (EVM, Solana) and set security preferences.
3. Issue a session token tied to the Telegram `user_id` for subsequent authenticated calls.

## `/create`
1. Collect token metadata (name, symbol, supply, liquidity settings).
2. For EVM, deploy ERC-20 or ERC-404 contracts with guardrails (ownership renounce, liquidity locks).
3. Seed liquidity via integrated DEX routers and record the token in the catalog.

## `/buy <CA> <amount>`
1. Validate contract address and perform safety checks (honeypot/tax/blacklist).
2. Simulate swap route using DEX aggregators (Uniswap, Jupiter, etc.).
3. Queue the order for bundling; once executed, update portfolio and notify the user.

## `/sell <CA> <%|amount>`
1. Verify holdings and determine exact sell quantity.
2. Run slippage and tax checks; simulate route.
3. Submit to bundler and settle proceeds back to the user wallet or internal balance.

## `/snipe <CA> [options]`
1. Collect advanced parameters (liquidity thresholds, anti-MEV preferences, gas caps, slippage).
2. Monitor pool events or liquidity additions that match criteria.
3. Auto-submit swap when triggers fire, using private relays when possible.

## `/bundler <wallets>`
1. Accept a target wallet cohort (5, 10, 15, 20, or 25).
2. Update the bundler service to defer execution until the chosen threshold is met.
3. Confirm the new threshold back to the user.

## `/auto`
1. Configure automation strategies (trailing stops, DCA schedules, take-profit ladders).
2. Persist strategy definitions and evaluate triggers continuously.
3. Execute resulting buy/sell orders via the orchestration and bundler pipeline.

## `/approve <CA>`
1. Request token approval for the router if not using Permit2.
2. Generate and submit approval transaction (on-chain or via permit signature).
3. Update internal state to reflect allowance status.

## `/portfolio`
1. Aggregate balances across chains, including unrealized and realized PnL.
2. Display average cost basis, ROI, and recent trade history.
3. Provide export options for tax/accounting.

## `/settings`
1. Allow users to adjust slippage tolerance, gas strategy, privacy mode, and default wallet.
2. Persist settings per user and apply defaults to subsequent orders.

## `/safety <CA>`
1. Run static/dynamic analysis to produce a risk score (honeypot detection, taxes, owner perms).
2. Present findings to the user before they trade.

## `/withdraw`
1. Authenticate and gather destination address.
2. Validate withdrawal against risk rules (AML, velocity limits).
3. Initiate transfer from custody wallet or generate unsigned transaction for user confirmation.

## `/deposit`
1. Provide a per-user deposit address or QR code for supported chains.
2. Monitor inbound transfers and credit internal balances once confirmed.
3. Trigger optional notifications and ledger entries.
