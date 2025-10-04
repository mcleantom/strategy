from __future__ import annotations

from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from strategy.db import CandleModel
from strategy.models.position import Position, PositionType
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy
from tests.strategies import NoOpStrategy


def test_is_long_is_short_flags() -> None:
    s = NoOpStrategy()
    assert not bool(s.is_long)
    assert not bool(s.is_short)
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
    assert bool(s.is_long)
    assert not bool(s.is_short)
    s.position.type = PositionType.short
    assert not s.is_long
    assert s.is_short


async def test_available_margin_updates_during_backtest(
    save_candles: Callable[[list[CandleModel]], Awaitable[None]],
    db_session: AsyncSession,
) -> None:
    class MarginStrategy(Strategy):
        def __init__(self) -> None:
            super().__init__()
            self.seen_margins: list[float] = []
            self._went_long = False

        def should_long(self) -> bool:
            self.seen_margins.append(self.available_margin)
            return not self._went_long

        def go_long(self) -> Order:
            self._went_long = True
            return Order(
                quantity=1.0,
                price=float(self.candles[-1]["close"]),
            )

        def should_short(self) -> bool:
            return False

        def go_short(self) -> Order:
            raise NotImplementedError

        def should_exit_position(self) -> bool:
            return False

    strat = MarginStrategy()
    bt = Backtester(
        strategy=strat,
        initial_balance=500.0,
        symbol="AAPL",
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
    ]
    await save_candles(candles)
    await bt.backtest_stream(db=db_session, warmup_bars=0)
    assert strat.seen_margins == [500.0, 400.0]
