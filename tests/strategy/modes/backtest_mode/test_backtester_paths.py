from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from strategy.models.enums import ETimeframe
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy

if TYPE_CHECKING:
    import numpy.typing as npt


def _mk_candle(ts: int, price: float) -> npt.NDArray:
    dtype = [
        ("timestamp", "i8"),
        ("open", "f8"),
        ("close", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("volume", "f8"),
    ]
    return np.array([(ts, price, price, price, price, 0.0)], dtype=dtype)[0]


class ShortOnlyStrategy(Strategy):
    """Only shorts."""

    def __init__(self) -> None:
        super().__init__()
        self._allow_short = True

    def should_long(self) -> bool:
        return False

    def go_long(self) -> Order:
        raise NotImplementedError

    def should_short(self) -> bool:
        return self._allow_short and self.position is None

    def go_short(self) -> Order:
        # enter at current close, TP 10 lower
        price = float(self.candles[-1]["close"])
        return Order(
            quantity=1.0,
            price=price,
            stop_loss=price + 100.0,
            take_profit=price - 10.0,
        )

    def should_exit_position(self) -> bool:
        return False


def test_warmup_path_and_short_flow_with_exit() -> None:
    # create > 300 one-minute candles so warmup triggers (250)
    candles = np.zeros(
        350,
        dtype=[
            ("timestamp", "i8"),
            ("open", "f8"),
            ("close", "f8"),
            ("high", "f8"),
            ("low", "f8"),
            ("volume", "f8"),
        ],
    )
    for i in range(350):
        price = 100.0 if i < 340 else 90.0  # drop to trigger take_profit on short
        candles[i] = (i * 60_000, price, price, price, price, 0.0)

    strat = ShortOnlyStrategy()
    bt = Backtester(
        strategy=strat,
        initial_balance=1_000.0,
        timeframe=ETimeframe.MINUTE_1,
        symbol="AAPL",
    )
    bt.backtest(candles)

    # We should have at least one short trade closed when price drops
    assert any(t.type == "short" for t in bt.trades)
    # Equity curve should be populated for each candle post-warmup
    assert len(bt.equity_curve) == len(candles) - bt.warmup_candles + 2


def test_should_exit_conditions_long_and_short() -> None:
    # Build a tiny sequence to test exit logic paths directly
    candles = np.array(
        [
            _mk_candle(0, 100.0),
            _mk_candle(60_000, 101.0),
            _mk_candle(120_000, 102.0),
        ],
    )

    class LongStrategy(Strategy):
        def __init__(self) -> None:
            super().__init__()
            self._went_long = False

        def should_long(self) -> bool:
            return not self._went_long

        def go_long(self) -> Order:
            self._went_long = True
            price = float(self.candles[-1]["close"])
            return Order(
                quantity=1.0,
                price=price,
                stop_loss=price - 1.0,
                take_profit=price + 1.0,
            )

        def should_short(self) -> bool:
            return False

        def go_short(self) -> Order:
            raise NotImplementedError

        def should_exit_position(self) -> bool:
            return False

    strat = LongStrategy()
    bt = Backtester(
        strategy=strat,
        initial_balance=1_000.0,
        symbol="AAPL",
    )
    bt.backtest(candles)

    # we should have a long trade closed by the end
    assert any(t.type == "long" for t in bt.trades)
