from decimal import Decimal

from tbot.models import OrderSide
from tbot.services.bundler import OrderBundler
from tbot.services.order_service import make_order


def _make_orders(count: int, token: str = "0xabc", side: OrderSide = OrderSide.BUY):
    for idx in range(count):
        yield make_order(
            user_id=idx,
            wallet_id=f"wallet-{idx}",
            token_address=token,
            side=side,
            amount=Decimal("1.0"),
        )


def test_bundler_respects_min_wallets_setting():
    bundler = OrderBundler(min_wallets=10)
    results = []
    for order in _make_orders(10):
        results.extend(bundler.add_order(order))
    assert len(results) == 1
    bundle = results[0]
    assert bundle.wallet_count() == 10
    assert bundle.total_amount == Decimal("10.0")


def test_bundler_handles_highest_threshold():
    bundler = OrderBundler(min_wallets=25)
    results = []
    for order in _make_orders(25):
        results.extend(bundler.add_order(order))
    assert len(results) == 1
    assert results[0].wallet_count() == 25


def test_force_flush_releases_remaining_orders():
    bundler = OrderBundler(min_wallets=5)
    for order in _make_orders(7):
        bundler.add_order(order)
    bundles = bundler.flush(force=True)
    assert len(bundles) == 1
    assert bundles[0].wallet_count() == 2
