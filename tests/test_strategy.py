from __future__ import annotations

from collections.abc import Awaitable, Callable

import numpy as np
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from strategy.db.candle import CandleModel
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy
from strategy.utils.helpers import to_structured_array
from tests.strategies import BuyAndHoldStrategy


@pytest.fixture  # type: ignore[misc]
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
            timeframe="1m",
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
            timeframe="1m",
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
            timeframe="1m",
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
            timeframe="1m",
        ),
    ]


async def test_example_strategy(
    test_candles: list[CandleModel],
    save_candles: Callable[[list[CandleModel]], Awaitable[None]],
    db_session: AsyncSession,
) -> None:
    entry_price = test_candles[0].close
    exit_price = test_candles[-1].close
    entry_ts = int(test_candles[0].timestamp)
    exit_ts = int(test_candles[-1].timestamp)
    await save_candles(test_candles)
    backtester = Backtester(
        strategy=BuyAndHoldStrategy(),
        initial_balance=10_000,
        symbol="AAPL",
        start_ts=entry_ts,
        end_ts=exit_ts + 1,
    )
    await backtester.backtest_stream(db=db_session, warmup_bars=0)

    assert len(backtester.trades) == 1
    assert backtester.trades[0].type == "long"
    assert backtester.trades[0].entry_price == entry_price
    assert backtester.trades[0].exit_price == exit_price
    # PnL is exit - entry for long
    assert (
        backtester.pnl
        == backtester.trades[0].exit_price - backtester.trades[0].entry_price
    )


async def test_no_balance_throws(
    test_candles: list[CandleModel],
    save_candles: Callable[[list[CandleModel]], Awaitable[None]],
    db_session: AsyncSession,
) -> None:
    start_ts = int(test_candles[0].timestamp)
    end_ts = int(test_candles[-1].timestamp)
    await save_candles(test_candles)
    backtester = Backtester(
        strategy=BuyAndHoldStrategy(),
        initial_balance=0,
        symbol="AAPL",
        start_ts=start_ts,
        end_ts=end_ts + 1,
    )
    with pytest.raises(RuntimeError) as e:
        await backtester.backtest_stream(db=db_session, warmup_bars=0)
    assert str(e.value) == "Ran out of money"


async def test_exit_stop_loss_long() -> None:
    backtester = Backtester(
        strategy=BuyAndHoldStrategy(),
        initial_balance=10_000,
        symbol="AAPL",
    )
    backtester.position = "long"
    backtester.stop_loss = 101
    close = 100
    candle = to_structured_array(np.array([[1, 100, close, 100, 100, 100]]))
    assert backtester.should_exit_position(candle)


def test_exit_stop_loss_short() -> None:
    backtester = Backtester(
        strategy=BuyAndHoldStrategy(),
        initial_balance=10_000,
        symbol="AAPL",
    )
    backtester.position = "short"
    backtester.stop_loss = 99
    close = 100
    candle = to_structured_array(np.array([[1, 100, close, 100, 100, 100]]))
    assert backtester.should_exit_position(candle)


async def test_exit_short_position(
    test_candles: list[CandleModel],
    save_candles: Callable[[list[CandleModel]], Awaitable[None]],
    db_session: AsyncSession,
) -> None:
    class ShortOnceStrategy(Strategy):
        def __init__(self) -> None:
            super().__init__()
            self.shorted = False

        def should_short(self) -> bool:
            return not self.shorted

        def go_short(self) -> Order:
            self.shorted = True
            return Order(
                quantity=1,
                price=float(self.store.candles.most_recent_candle.close),
                stop_loss=None,
                take_profit=None,
            )

        def should_long(self) -> bool:
            return False

        def go_long(self) -> Order:
            raise NotImplementedError

        def should_exit_position(self) -> bool:
            return False

    start_ts = int(test_candles[0].timestamp)
    end_ts = int(test_candles[-1].timestamp)
    entry_price = test_candles[0].close
    exit_price = test_candles[-1].close
    backtester = Backtester(
        strategy=ShortOnceStrategy(),
        initial_balance=10_000,
        symbol="AAPL",
        start_ts=start_ts,
        end_ts=end_ts + 1,
    )
    await save_candles(test_candles)

    await backtester.backtest_stream(db=db_session, warmup_bars=0)

    assert len(backtester.trades) == 1
    trade = backtester.trades[0]
    assert trade.type == "short"
    assert trade.entry_price == entry_price
    assert trade.exit_price == exit_price
    # PnL for short = entry - exit
    assert backtester.pnl == trade.entry_price - trade.exit_price
