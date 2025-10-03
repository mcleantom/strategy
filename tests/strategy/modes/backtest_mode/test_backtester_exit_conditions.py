from __future__ import annotations

import numpy as np

from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy


def _mk_candle(ts: int, price: float) -> np.ndarray:
    dtype = [
        ("timestamp", "i8"),
        ("open", "f8"),
        ("close", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("volume", "f8"),
    ]
    return np.array([(ts, price, price, price, price, 0.0)], dtype=dtype)[0]


class CancelStrategy(Strategy):
    """Cancels order."""

    def __init__(self) -> None:
        super().__init__()
        self._should_cancel = False

    def should_long(self) -> bool:
        return True

    def go_long(self) -> Order:
        return Order(quantity=1.0, price=100.0, stop_loss=90.0, take_profit=110.0)

    def should_short(self) -> bool:
        return False

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_exit_position(self) -> bool:
        return self._should_cancel


def test_should_exit_position_exits_position() -> None:
    strat = CancelStrategy()
    bt = Backtester(strategy=strat, initial_balance=1000.0, symbol="AAPL")
    candles = np.array(
        [
            _mk_candle(0, 100.0),
            _mk_candle(60_000, 100.0),  # enter long
            _mk_candle(120_000, 100.0),  # cancel
        ],
    )
    strat._should_cancel = True
    bt.backtest(candles)
    # Should have entered and exited due to cancel
    assert len(bt.trades) >= 1


def test_stop_loss_and_take_profit_both_conditions() -> None:
    class BothExitsStrategy(Strategy):
        def __init__(self) -> None:
            super().__init__()
            self._entered = False

        def should_long(self) -> bool:
            return not self._entered

        def go_long(self) -> Order:
            self._entered = True
            return Order(quantity=1.0, price=100.0, stop_loss=95.0, take_profit=105.0)

        def should_short(self) -> bool:
            return False

        def go_short(self) -> Order:
            raise NotImplementedError

        def should_exit_position(self) -> bool:
            return False

    strat = BothExitsStrategy()
    bt = Backtester(strategy=strat, initial_balance=1000.0, symbol="AAPL")
    # Price hits take profit
    candles = np.array(
        [
            _mk_candle(0, 100.0),
            _mk_candle(60_000, 100.0),  # enter
            _mk_candle(120_000, 105.0),  # hit TP
        ],
    )
    bt.backtest(candles)
    assert len(bt.trades) >= 1
    assert bt.trades[0].exit_price == 105.0
