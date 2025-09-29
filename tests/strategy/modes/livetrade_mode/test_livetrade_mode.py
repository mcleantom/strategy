from __future__ import annotations

import numpy as np

from strategy.modes.livetrade_mode import LiveTrader
from tests.mocks import DummyExchange
from tests.strategies import DummyStrategy


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


async def test_enter_and_exit_long_flow() -> None:
    strategy = DummyStrategy()
    exchange = DummyExchange(balance=1_000)
    trader = LiveTrader(strategy=strategy, exchange=exchange, symbol="AAPL")

    # set candles and make strategy enter long
    c1 = _mk_candle(100.0)
    strategy.store.candles.add_candle(c1)
    strategy._should_long = True
    await trader.on_candle()

    assert trader.position is not None
    assert trader.order_id == "ORDER-1"
    assert exchange.orders
    assert exchange.orders[0]["side"] == "buy"

    # Exit at higher price
    c2 = _mk_candle(110.0)
    await trader.exit_position({"close": c2["close"]})
    assert trader.position is None
    assert exchange.cancelled  # type: ignore[unreachable]
    assert exchange.cancelled[0] == ("AAPL", "ORDER-1")
    assert trader.pnl > 0


async def test_should_exit_conditions() -> None:
    strategy = DummyStrategy()
    exchange = DummyExchange(balance=1_000)
    trader = LiveTrader(strategy=strategy, exchange=exchange, symbol="AAPL")

    # No position -> should not exit
    assert trader.should_exit_position({"close": 100.0}) is False

    # Enter position and set stops
    c1 = _mk_candle(100.0)
    strategy.store.candles.add_candle(c1)
    strategy._should_long = True
    await trader.on_candle()

    # set stop loss and take profit
    trader.stop_loss = 90.0
    trader.take_profit = 110.0

    # Hit take profit
    assert trader.should_exit_position({"close": 110.0}) is True
    # Hit stop loss
    assert trader.should_exit_position({"close": 90.0}) is True
