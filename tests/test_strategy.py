from __future__ import annotations

import os

import numpy as np
import pytest

from strategy.db.candle import CandleModel
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy
from strategy.utils.helpers import to_numpy_array, to_structured_array


class BuyAndHoldStrategy(Strategy):
    """Buy and hold strategy."""

    def __init__(self):
        super().__init__()
        self.has_bought = False

    def should_long(self) -> bool:
        return not self.has_bought

    def go_long(self) -> Order:
        self.has_bought = True
        return Order(
            quantity=1,
            price=self.store.candles.most_recent_candle.close,
            stop_loss=None,
            take_profit=None,
        )

    def should_short(self) -> bool:
        return False

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_cancel_entry(self) -> bool:
        return False


@pytest.fixture
def test_candles() -> list[CandleModel]:
    return [
        CandleModel(
            timestamp=1,
            open=100,
            high=110,
            low=90,
            close=105,
            volume=1000,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1D",
        ),
        CandleModel(
            timestamp=2,
            open=106,
            high=115,
            low=104,
            close=110,
            volume=1000,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1D",
        ),
        CandleModel(
            timestamp=3,
            open=111,
            high=120,
            low=109,
            close=115,
            volume=1000,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1D",
        ),
        CandleModel(
            timestamp=4,
            open=116,
            high=125,
            low=114,
            close=120,
            volume=1000,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1D",
        ),
    ]


def test_example_strategy(
    test_candles: list[CandleModel],
):
    backtester = Backtester(strategy=BuyAndHoldStrategy(), initial_balance=10_000)
    candles = to_numpy_array(test_candles)
    backtester.backtest(candles)

    assert len(backtester.trades) == 1
    assert backtester.trades[0].type == "long"
    assert backtester.trades[0].entry_price == candles[0]["close"]
    assert backtester.trades[0].exit_price == candles[-1]["close"]
    # PnL is exit - entry for long
    assert (
        backtester.pnl
        == backtester.trades[0].exit_price - backtester.trades[0].entry_price
    )


requires_db = pytest.mark.skipif(
    os.getenv("LIVE_DB") != "1",
    reason="Skipping DB-dependent test",
)


def test_no_balance_throws(test_candles: list[CandleModel]):
    backtester = Backtester(strategy=BuyAndHoldStrategy(), initial_balance=0)
    candles = to_numpy_array(test_candles)
    with pytest.raises(RuntimeError) as e:
        backtester.backtest(candles)
    assert str(e.value) == "Ran out of money"


def test_exit_stop_loss_long():
    backtester = Backtester(strategy=BuyAndHoldStrategy(), initial_balance=10_000)
    backtester.position = "long"
    backtester.stop_loss = 101
    close = 100
    candle = to_structured_array(np.array([[1, 100, close, 100, 100, 100]]))
    assert backtester.should_exit_position(candle)


def test_exit_stop_loss_short():
    backtester = Backtester(strategy=BuyAndHoldStrategy(), initial_balance=10_000)
    backtester.position = "short"
    backtester.stop_loss = 99
    close = 100
    candle = to_structured_array(np.array([[1, 100, close, 100, 100, 100]]))
    assert backtester.should_exit_position(candle)


def test_exit_short_position(test_candles: list[CandleModel]):
    class ShortOnceStrategy(Strategy):
        def __init__(self):
            super().__init__()
            self.shorted = False

        def should_short(self) -> bool:
            return not self.shorted

        def go_short(self) -> Order:
            self.shorted = True
            return Order(
                quantity=1,
                price=self.store.candles.most_recent_candle.close,
                stop_loss=None,
                take_profit=None,
            )

        def should_long(self) -> bool:
            return False

        def go_long(self) -> Order:
            raise NotImplementedError

        def should_cancel_entry(self) -> bool:
            return False

    backtester = Backtester(strategy=ShortOnceStrategy(), initial_balance=10_000)
    candles = to_numpy_array(test_candles)

    backtester.backtest(candles)

    assert len(backtester.trades) == 1
    trade = backtester.trades[0]
    assert trade.type == "short"
    assert trade.entry_price == candles[0]["close"]
    assert trade.exit_price == candles[-1]["close"]
    # PnL for short = entry - exit
    assert backtester.pnl == trade.entry_price - trade.exit_price
