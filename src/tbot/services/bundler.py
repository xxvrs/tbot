from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from decimal import Decimal
from typing import Deque, Dict, Iterable, List, Sequence

from ..models import Bundle, Order, OrderSide, aggregate_amounts


@dataclass(frozen=True)
class BundleThreshold:
    """Represents supported bundle sizes for wallet aggregation."""

    wallet_count: int


DEFAULT_THRESHOLDS: Sequence[BundleThreshold] = tuple(
    BundleThreshold(size) for size in (5, 10, 15, 20, 25)
)


class OrderBundler:
    """Aggregates orders into bundles targeting specific wallet count thresholds."""

    def __init__(
        self,
        thresholds: Sequence[BundleThreshold] | None = None,
        min_wallets: int | None = None,
    ) -> None:
        ordered = sorted(thresholds or list(DEFAULT_THRESHOLDS), key=lambda t: t.wallet_count)
        self._thresholds: List[BundleThreshold] = ordered
        self._threshold_values = {threshold.wallet_count for threshold in ordered}
        if min_wallets is None:
            self._min_wallets = min(self._threshold_values)
        elif min_wallets in self._threshold_values:
            self._min_wallets = min_wallets
        else:
            raise ValueError("min_wallets must match one of the configured thresholds")
        self._queues: Dict[tuple[str, OrderSide], Deque[Order]] = defaultdict(deque)

    def set_min_wallets(self, wallet_count: int) -> None:
        if wallet_count not in self._threshold_values:
            raise ValueError("wallet_count must match one of the configured thresholds")
        self._min_wallets = wallet_count

    def add_order(self, order: Order) -> List[Bundle]:
        key = (order.token_address, order.side)
        queue = self._queues[key]
        queue.append(order)
        return self._drain_threshold_bundles(key)

    def flush(self, force: bool = False) -> List[Bundle]:
        bundles: List[Bundle] = []
        keys = list(self._queues.keys())
        for key in keys:
            bundles.extend(self._drain_threshold_bundles(key))
            if force:
                bundles.extend(self._drain_all(key))
        return bundles

    def _drain_threshold_bundles(self, key: tuple[str, OrderSide]) -> List[Bundle]:
        queue = self._queues[key]
        bundles: List[Bundle] = []
        while queue:
            seen_wallets: set[str] = set()
            threshold_positions: Dict[int, int] = {}
            for idx, order in enumerate(queue):
                seen_wallets.add(order.wallet_id)
                wallet_count = len(seen_wallets)
                if wallet_count in self._threshold_values and wallet_count not in threshold_positions:
                    threshold_positions[wallet_count] = idx + 1
            eligible = {k: v for k, v in threshold_positions.items() if k >= self._min_wallets}
            if not eligible:
                break
            target_wallets = max(eligible.keys())
            order_count = eligible[target_wallets]
            bundles.append(self._pop_bundle(queue, order_count))
        return bundles

    def _drain_all(self, key: tuple[str, OrderSide]) -> List[Bundle]:
        queue = self._queues[key]
        bundles: List[Bundle] = []
        while queue:
            orders = [queue.popleft() for _ in range(len(queue))] or []
            if not orders:
                break
            for order in orders:
                order.mark_bundled()
            bundles.append(self._build_bundle(key, orders))
        return bundles

    def _pop_bundle(self, queue: Deque[Order], order_count: int) -> Bundle:
        orders: List[Order] = []
        for _ in range(order_count):
            orders.append(queue.popleft())
        for order in orders:
            order.mark_bundled()
        return self._build_bundle((orders[0].token_address, orders[0].side), orders)

    def _build_bundle(
        self, key: tuple[str, OrderSide], orders: Iterable[Order]
    ) -> Bundle:
        orders_list = list(orders)
        total = aggregate_amounts(orders_list)
        return Bundle(
            token_address=key[0],
            side=key[1],
            orders=orders_list,
            total_amount=total,
        )

    def queue_depth(self) -> Dict[tuple[str, OrderSide], int]:
        return {key: len(queue) for key, queue in self._queues.items()}

    def pending_wallets(self) -> Dict[tuple[str, OrderSide], int]:
        return {
            key: len({order.wallet_id for order in queue})
            for key, queue in self._queues.items()
        }

    def total_value_locked(self) -> Dict[tuple[str, OrderSide], Decimal]:
        return {
            key: aggregate_amounts(queue)
            for key, queue in self._queues.items()
        }
