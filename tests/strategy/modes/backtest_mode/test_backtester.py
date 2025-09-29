from __future__ import annotations

import numpy as np

from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy


class ExampleStrategy(Strategy):
    """Buy and hold."""

    def __init__(self) -> None:
        super().__init__()
        self.has_bought = False

    def should_long(self) -> bool:
        return not self.has_bought

    def go_long(self) -> Order:
        self.has_bought = True
        return Order(
            quantity=1,
            price=float(self.store.candles.most_recent_candle.close),
            stop_loss=None,
            take_profit=None,
        )

    def should_short(self) -> bool:
        return False

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_cancel_entry(self) -> bool:
        return False


def test_buy_short() -> None:
    strategy = ExampleStrategy()
    backtester = Backtester(strategy, initial_balance=1000)
    order = Order(quantity=10, price=100)
    # Use structured array rows in place of ORM Candle for backtester methods
    dtype = [
        ("timestamp", "i8"),
        ("open", "f8"),
        ("close", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("volume", "f8"),
    ]
    candle_enter = np.array([(1, 100, 100, 100, 100, 0)], dtype=dtype)[0]
    backtester.enter_short(order, candle_enter)
    assert (
        backtester.balance == 1000
    )  # balance changes realized on exit only in current implementation

    candle_exit = np.array([(1, 100, 100, 100, 100, 0)], dtype=dtype)[0]
    backtester.exit_short(candle_exit)
    assert backtester.balance == 1000
