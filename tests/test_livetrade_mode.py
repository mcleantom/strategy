from typing import Any

import numpy as np

from strategy.modes.livetrade_mode import LiveTrader
from strategy.strategy import Order, Strategy


class DummyExchange:
    def __init__(self, balance: float = 10_000):
        self._balance = balance
        self.orders: list[dict[str, Any]] = []
        self.cancelled: list[tuple[str, str]] = []

    def get_balance(self) -> float:
        return self._balance

    def market_order(self, symbol: str, qty: float, current_price: float, side: str, reduce_only: bool = False):
        self.orders.append(
            {"symbol": symbol, "qty": qty, "price": current_price, "side": side, "reduce_only": reduce_only}
        )
        return "ORDER-1"

    def cancel_order(self, symbol: str, order_id: str):
        self.cancelled.append((symbol, order_id))


class DummyStrategy(Strategy):
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
    dtype = [("timestamp", "i8"), ("open", "f8"), ("close", "f8"), ("high", "f8"), ("low", "f8"), ("volume", "f8")]
    return np.array([(1, price, price, price, price, 0.0)], dtype=dtype)[0]


def test_enter_and_exit_long_flow():
    strategy = DummyStrategy()
    exchange = DummyExchange(balance=1_000)
    trader = LiveTrader(strategy=strategy, exchange=exchange, symbol="AAPL")

    # set candles and make strategy enter long
    c1 = _mk_candle(100.0)
    strategy.store.candles.add_candle(c1)
    strategy._should_long = True
    trader.on_candle()

    assert trader.position is not None
    assert trader.order_id == "ORDER-1"
    assert exchange.orders and exchange.orders[0]["side"] == "buy"

    # Exit at higher price
    c2 = _mk_candle(110.0)
    trader.exit_position({"close": c2["close"]})
    assert trader.position is None
    assert exchange.cancelled and exchange.cancelled[0] == ("AAPL", "ORDER-1")
    assert trader.pnl > 0


def test_should_exit_conditions():
    strategy = DummyStrategy()
    exchange = DummyExchange(balance=1_000)
    trader = LiveTrader(strategy=strategy, exchange=exchange, symbol="AAPL")

    # No position -> should not exit
    assert trader.should_exit_position({"close": 100.0}) is False

    # Enter position and set stops
    c1 = _mk_candle(100.0)
    strategy.store.candles.add_candle(c1)
    strategy._should_long = True
    trader.on_candle()

    # set stop loss and take profit
    trader.stop_loss = 90.0
    trader.take_profit = 110.0

    # Hit take profit
    assert trader.should_exit_position({"close": 110.0}) is True
    # Hit stop loss
    assert trader.should_exit_position({"close": 90.0}) is True
