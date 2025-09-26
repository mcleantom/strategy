from __future__ import annotations

import numpy as np

from strategy.models.position import Position, PositionType
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy


def _mk_candle(ts: int, price: float):
    dtype = [
        ("timestamp", "i8"),
        ("open", "f8"),
        ("close", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("volume", "f8"),
    ]
    return np.array([(ts, price, price, price, price, 0.0)], dtype=dtype)[0]


class NoOpStrategy(Strategy):
    """Does nothing."""

    def should_long(self) -> bool:
        return False

    def go_long(self):
        raise AssertionError

    def should_short(self) -> bool:
        return False

    def go_short(self):
        return None

    def should_cancel_entry(self) -> bool:
        return False


def test_is_long_is_short_flags():
    s = NoOpStrategy()
    assert not s.is_long
    assert not s.is_short
    s.position = Position(
        exchange_name="x",
        symbol="AAPL",
        entry_price=100.0,
        exit_price=0.0,
        quantity=1.0,
        opened_at=None,  # type: ignore[arg-type]
        closed_at=None,  # type: ignore[arg-type]
        type=PositionType.long,
    )
    assert s.is_long
    assert not s.is_short
    s.position.type = PositionType.short
    assert not s.is_long
    assert s.is_short


def test_available_margin_updates_during_backtest():
    class MarginStrategy(Strategy):
        def __init__(self):
            super().__init__()
            self.seen_margins = []
            self._went_long = False

        def should_long(self) -> bool:
            return not self._went_long

        def go_long(self) -> Order:
            self._went_long = True
            return Order(quantity=1.0, price=float(self.candles[-1]["close"]))

        def should_short(self) -> bool:
            return False

        def go_short(self):
            return None

        def should_cancel_entry(self) -> bool:
            return False

    strat = MarginStrategy()
    bt = Backtester(strategy=strat, initial_balance=500.0)
    candles = np.array([_mk_candle(0, 10.0), _mk_candle(60_000, 10.0)])
    bt.backtest(candles)
    # _available_margin should reflect last loop balance at least once
    assert strat.available_margin == 500.0
