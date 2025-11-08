from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

from ..models import Bundle, ExecutionResult, Order, OrderSide
from .bundler import OrderBundler


@dataclass
class RoutingDecision:
    """Represents routing metadata for a bundle."""

    route: str
    estimated_gas: Decimal
    price_impact_bps: int


class PositionLedger:
    """Tracks per-wallet token balances for filled orders."""

    def __init__(self) -> None:
        self._balances: Dict[str, Dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

    def apply_execution(self, result: ExecutionResult) -> None:
        sign = Decimal("1") if result.bundle.side is OrderSide.BUY else Decimal("-1")
        for order in result.bundle.orders:
            wallet_balances = self._balances[order.wallet_id]
            current = wallet_balances.get(result.bundle.token_address, Decimal("0"))
            wallet_balances[result.bundle.token_address] = current + (sign * order.amount)

    def balance(self, wallet_id: str, token_address: str) -> Decimal:
        return self._balances[wallet_id].get(token_address, Decimal("0"))

    def snapshot(self) -> Dict[str, Dict[str, Decimal]]:
        return {
            wallet_id: dict(tokens)
            for wallet_id, tokens in self._balances.items()
        }


class OrderOrchestrator:
    """High level service that normalizes and routes orders via the bundler."""

    def __init__(self, bundler: OrderBundler | None = None) -> None:
        self._bundler = bundler or OrderBundler()
        self._executed_bundles: List[ExecutionResult] = []
        self._ledger = PositionLedger()

    def submit_order(self, order: Order) -> List[ExecutionResult]:
        bundles = self._bundler.add_order(order)
        results: List[ExecutionResult] = []
        for bundle in bundles:
            decision = self._choose_route(bundle)
            result = self._execute_bundle(bundle, decision)
            results.append(result)
            self._executed_bundles.append(result)
            self._ledger.apply_execution(result)
        return results

    def flush(self, force: bool = False) -> List[ExecutionResult]:
        bundles = self._bundler.flush(force=force)
        results: List[ExecutionResult] = []
        for bundle in bundles:
            decision = self._choose_route(bundle)
            result = self._execute_bundle(bundle, decision)
            results.append(result)
            self._executed_bundles.append(result)
            self._ledger.apply_execution(result)
        return results

    def history(self) -> List[ExecutionResult]:
        return list(self._executed_bundles)

    def set_min_wallets(self, wallet_count: int) -> None:
        self._bundler.set_min_wallets(wallet_count)


    def ledger_snapshot(self) -> Dict[str, Dict[str, Decimal]]:
        return self._ledger.snapshot()

    def _choose_route(self, bundle: Bundle) -> RoutingDecision:
        """Dummy router that selects a route based on the order side."""
        if bundle.side is OrderSide.BUY:
            route = "uniswap_v3"
            price_impact_bps = 35
        elif bundle.side is OrderSide.SELL:
            route = "sushiswap"
            price_impact_bps = 42
        else:
            route = "jupiter"
            price_impact_bps = 50
        estimated_gas = Decimal("0.005") * Decimal(bundle.user_count() or 1)
        return RoutingDecision(route=route, estimated_gas=estimated_gas, price_impact_bps=price_impact_bps)

    def _execute_bundle(self, bundle: Bundle, decision: RoutingDecision) -> ExecutionResult:
        """Mock execution layer. In production this would submit on-chain tx."""
        for order in bundle.orders:
            order.mark_executed()
        tx_hash = f"0x{bundle.bundle_id[:16]}"
        notes = (
            f"Executed via {decision.route} with est. gas {decision.estimated_gas}"
            f" and price impact {decision.price_impact_bps}bps"
        )
        return ExecutionResult(bundle=bundle, tx_hash=tx_hash, notes=notes)


def normalize_amount(amount: str | float | Decimal) -> Decimal:
    if isinstance(amount, Decimal):
        return amount
    if isinstance(amount, (int, float)):
        return Decimal(str(amount))
    return Decimal(amount)


def make_order(
    user_id: int,
    wallet_id: str,
    token_address: str,
    side: OrderSide,
    amount: str | float | Decimal,
    options: Optional[Dict[str, str]] = None,
) -> Order:
    order = Order(
        user_id=user_id,
        wallet_id=wallet_id,
        token_address=token_address,
        side=side,
        amount=normalize_amount(amount),
        options=options or {},
    )
    return order
