from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Iterable, List, Optional
import uuid


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"
    SNIPE = "snipe"


class OrderStatus(str, Enum):
    PENDING = "pending"
    BUNDLED = "bundled"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass(slots=True)
class Order:
    """Represents a normalized order from the Telegram interface."""

    user_id: int
    wallet_id: str
    token_address: str
    side: OrderSide
    amount: Decimal
    order_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    options: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: OrderStatus = OrderStatus.PENDING

    def mark_bundled(self) -> None:
        self.status = OrderStatus.BUNDLED

    def mark_executed(self) -> None:
        self.status = OrderStatus.EXECUTED

    def mark_failed(self) -> None:
        self.status = OrderStatus.FAILED


@dataclass(slots=True)
class Bundle:
    """Represents a batch of orders to be sent as a single on-chain swap."""

    token_address: str
    side: OrderSide
    orders: List[Order]
    total_amount: Decimal
    bundle_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def user_count(self) -> int:
        return len({order.user_id for order in self.orders})

    def wallet_count(self) -> int:
        return len({order.wallet_id for order in self.orders})


@dataclass(slots=True)
class ExecutionResult:
    bundle: Bundle
    tx_hash: Optional[str] = None
    executed_at: Optional[datetime] = None
    notes: Optional[str] = None


@dataclass(slots=True)
class PortfolioPosition:
    token_address: str
    balance: Decimal
    average_cost: Decimal
    realized_pnl: Decimal = Decimal("0")


@dataclass(slots=True)
class Wallet:
    wallet_id: str
    owner_id: int
    chain: str
    address: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_custodial: bool = False


@dataclass(slots=True)
class SafetyReport:
    token_address: str
    score: int
    issues: List[str] = field(default_factory=list)


@dataclass(slots=True)
class DepositAddress:
    wallet_id: str
    chain: str
    address: str


@dataclass(slots=True)
class WithdrawalRequest:
    wallet_id: str
    destination: str
    amount: Decimal
    token_address: str


def aggregate_amounts(orders: Iterable[Order]) -> Decimal:
    total = Decimal("0")
    for order in orders:
        total += order.amount
    return total
