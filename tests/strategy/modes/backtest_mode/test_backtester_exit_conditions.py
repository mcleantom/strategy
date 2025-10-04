from __future__ import annotations

from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from strategy.db import CandleModel
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy


class CancelStrategy(Strategy):
    """Cancels order."""

    def __init__(self) -> None:
        super().__init__()

    def should_long(self) -> bool:
        return True

    def go_long(self) -> Order:
        return Order(quantity=1.0, price=100.0, stop_loss=90.0, take_profit=110.0)

    def should_short(self) -> bool:
        return False

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_exit_position(self) -> bool:
        return True


@pytest.mark.skip(reason="Doesnt actually test if should_exit_position closes position")  # type: ignore[misc]
async def test_should_exit_position_exits_position(
    save_candles: Callable[[list[CandleModel]], Awaitable[None]],
    db_session: AsyncSession,
) -> None:
    strat = CancelStrategy()
    bt = Backtester(
        strategy=strat,
        initial_balance=1000.0,
        symbol="AAPL",
        start_ts=0,
        end_ts=300_000,
    )
    candles = [
        CandleModel(
            timestamp=0,
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0.0,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1m",
        ),
        CandleModel(
            timestamp=1,
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0.0,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1m",
        ),
        CandleModel(
            timestamp=2,
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0.0,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1m",
        ),
    ]
    await save_candles(candles)
    await bt.backtest_stream(db=db_session, warmup_bars=0)
    assert len(bt.trades) >= 1


async def test_stop_loss_and_take_profit_both_conditions(
    save_candles: Callable[[list[CandleModel]], Awaitable[None]],
    db_session: AsyncSession,
) -> None:
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
    bt = Backtester(
        strategy=strat,
        initial_balance=1000.0,
        symbol="AAPL",
        start_ts=0,
        end_ts=300_000,
    )
    # Price hits take profit
    candles = [
        CandleModel(
            timestamp=0,
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0.0,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1m",
        ),
        CandleModel(
            timestamp=1,
            open=100.0,
            high=100.0,
            low=100.0,
            close=100.0,
            volume=0.0,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1m",
        ),  # enter
        CandleModel(
            timestamp=2,
            open=100.0,
            high=105.0,
            low=100.0,
            close=105.0,
            volume=0.0,
            exchange="NYSE",
            symbol="AAPL",
            timeframe="1m",
        ),  # hit TP
    ]
    await save_candles(candles)
    await bt.backtest_stream(db=db_session, warmup_bars=0)
    assert len(bt.trades) >= 1
    assert bt.trades[0].exit_price == 105.0
