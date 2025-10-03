# test_pnl_calculation.py
from __future__ import annotations

import numpy as np
import pytest

from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy


class NoopStrategy(Strategy):
    """Strategy placeholder — we won't use signals in these tests."""

    def __init__(self) -> None:
        super().__init__()

    def should_long(self) -> bool:  # not used
        return False

    def should_short(self) -> bool:  # not used
        return False

    def go_long(self) -> Order:
        raise NotImplementedError

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_exit_position(self) -> bool:
        return False


# Reusable structured-candle factory (matches your Backtester usage)
DTYPE = [
    ("timestamp", "i8"),
    ("open", "f8"),
    ("close", "f8"),
    ("high", "f8"),
    ("low", "f8"),
    ("volume", "f8"),
]


def candle(
    ts: int,
    c_open: float,
    c_close: float,
    c_high: float | None = None,
    c_low: float | None = None,
    c_volume: float = 0.0,
) -> np.ndarray:
    if c_high is None:
        c_high = max(c_open, c_close)
    if c_low is None:
        c_low = min(c_open, c_close)
    return np.array([(ts, c_open, c_close, c_high, c_low, c_volume)], dtype=DTYPE)[0]


@pytest.mark.parametrize(  # type: ignore[misc]
    ("qty", "entry", "exit_", "expected_balance"),
    [
        # Long profit: +100
        (10, 100.0, 110.0, 1000.0 + (110.0 - 100.0) * 10),
        # Long loss: -100
        (10, 100.0, 90.0, 1000.0 + (90.0 - 100.0) * 10),
    ],
)
def test_long_pnl(
    qty: float,
    entry: float,
    exit_: float,
    expected_balance: float,
) -> None:
    strat = NoopStrategy()
    bt = Backtester(strat, initial_balance=1000.0, symbol="AAPL")

    enter_c = candle(1, entry, entry)
    exit_c = candle(2, exit_, exit_)

    order = Order(quantity=qty, price=entry, stop_loss=None, take_profit=None)
    bt.enter_long(order, enter_c)
    # Entry should not realize PnL
    assert bt.balance == 1000.0

    bt.exit_long(exit_c)
    assert bt.balance == pytest.approx(expected_balance, rel=1e-12)
    # Also verify stored trade PnL equals balance change
    assert bt.trades[-1].pnl == pytest.approx(expected_balance - 1000.0, rel=1e-12)


@pytest.mark.parametrize(  # type: ignore[misc]
    ("qty", "entry", "exit_", "expected_balance"),
    [
        # Short profit: entry 100 -> exit 90 => +100
        (10, 100.0, 90.0, 1000.0 + (100.0 - 90.0) * 10),
        # Short loss: entry 100 -> exit 110 => -100
        (10, 100.0, 110.0, 1000.0 + (100.0 - 110.0) * 10),
    ],
)
def test_short_pnl(
    qty: float,
    entry: float,
    exit_: float,
    expected_balance: float,
) -> None:
    strat = NoopStrategy()
    bt = Backtester(strat, initial_balance=1000.0, symbol="AAPL")

    enter_c = candle(1, entry, entry)
    exit_c = candle(2, exit_, exit_)

    order = Order(quantity=qty, price=entry, stop_loss=None, take_profit=None)
    bt.enter_short(order, enter_c)
    # Entry should not realize PnL
    assert bt.balance == 1000.0

    bt.exit_short(exit_c)
    assert bt.balance == pytest.approx(expected_balance, rel=1e-12)
    # Catch the classic sign bug here if balance decreased on a profitable short
    assert bt.trades[-1].pnl == pytest.approx(expected_balance - 1000.0, rel=1e-12)
