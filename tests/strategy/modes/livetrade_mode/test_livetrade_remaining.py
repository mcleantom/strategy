from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import numpy as np

from strategy.modes.livetrade_mode import LiveTrade, LiveTrader
from strategy.strategy import Order, Strategy


class DummyExchange:
    """Mock exchange."""

    def __init__(self, balance: float = 10_000):
        self._balance = balance
        self.orders: list[dict[str, Any]] = []
        self.cancelled: list[tuple[str, str]] = []

    def get_balance(self) -> float:
        return self._balance

    def market_order(
        self,
        symbol: str,
        qty: float,
        current_price: float,
        side: str,
        reduce_only: bool = False,
    ):
        self.orders.append(
            {
                "symbol": symbol,
                "qty": qty,
                "price": current_price,
                "side": side,
                "reduce_only": reduce_only,
            },
        )
        return "ORDER-1"

    def cancel_order(self, symbol: str, order_id: str):
        self.cancelled.append((symbol, order_id))


class DummyStrategy(Strategy):
    """Buy and hold."""

    def __init__(self):
        super().__init__()
        self._should_long = False

    def should_long(self) -> bool:
        return self._should_long

    def go_long(self) -> Order:
        return Order(quantity=1, price=float(self.candles[-1]["close"]))

    def should_short(self) -> bool:
        return False

    def go_short(self):
        return None

    def should_cancel_entry(self) -> bool:
        return False


def _mk_candle(price: float):
    dtype = [
        ("timestamp", "i8"),
        ("open", "f8"),
        ("close", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("volume", "f8"),
    ]
    return np.array([(1, price, price, price, price, 0.0)], dtype=dtype)[0]


def test_insufficient_balance_does_not_enter():
    strategy = DummyStrategy()
    exchange = DummyExchange(balance=50.0)  # Low balance
    trader = LiveTrader(strategy=strategy, exchange=exchange, symbol="AAPL")

    c1 = _mk_candle(100.0)
    strategy.store.candles.add_candle(c1)
    strategy._should_long = True
    trader.on_candle()

    # Should not enter due to insufficient balance
    assert trader.position is None
    assert len(exchange.orders) == 0


def test_exit_position_with_no_order_id():
    strategy = DummyStrategy()
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

    trader.exit_position({"close": 110.0})
    # Should not crash and should still record trade
    assert trader.position is None
    assert len(trader.trades) == 1
