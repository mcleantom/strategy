from __future__ import annotations

from datetime import UTC, datetime

import numpy as np

from strategy.modes.livetrade_mode import LiveTrade, LiveTrader
from tests.mocks import DummyExchange
from tests.strategies import BuyAndHoldStrategy


def _mk_candle(price: float) -> np.ndarray:
    dtype = [
        ("timestamp", "i8"),
        ("open", "f8"),
        ("close", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("volume", "f8"),
    ]
    return np.array([(1, price, price, price, price, 0.0)], dtype=dtype)[0]


async def test_insufficient_balance_does_not_enter() -> None:
    strategy = BuyAndHoldStrategy()
    exchange = DummyExchange(balance=50.0)  # Low balance
    trader = LiveTrader(strategy=strategy, exchange=exchange, symbol="AAPL")

    c1 = _mk_candle(100.0)
    strategy.store.candles.add_candle(c1)
    strategy._has_gone_long = True
    await trader.on_candle()

    # Should not enter due to insufficient balance
    assert trader.position is None
    assert len(exchange.orders) == 0


async def test_exit_position_with_no_order_id() -> None:
    strategy = BuyAndHoldStrategy()
    exchange = DummyExchange(balance=1_000)
    trader = LiveTrader(strategy=strategy, exchange=exchange, symbol="AAPL")

    # Manually set position without order_id
    trader.position = LiveTrade(
        type="long",
        entry_price=100.0,
        quantity=1.0,
        entry_timestamp=datetime.now(tz=UTC),
    )
    trader.order_id = None

    await trader.exit_position({"close": 110.0})
    # Should not crash and should still record trade
    assert trader.position is None
    assert len(trader.trades) == 1  # type: ignore[unreachable]
