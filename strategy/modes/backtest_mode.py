from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import arrow
from tqdm import tqdm
from tqdm.asyncio import tqdm as tqdm_async

import strategy.utils.helpers as sh
from strategy.models.enums import ETimeframe
from strategy.modes.import_candles_mode import generate_candles_from_one_minute_candles
from strategy.utils.candles_chunk_loader import CandleChunkLoader
from strategy.utils.helpers import arrow_to_timestamp
from strategy.utils.timeframe_aggrigator import TimeframeAggregator

if TYPE_CHECKING:
    from datetime import datetime

    import numpy.typing as npt

    from strategy.strategy import Order, Strategy


@dataclass
class Trade:
    """Trade."""

    type: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    entry_timestamp: datetime
    exit_timestamp: datetime


@dataclass
class Equity:
    """Equity."""

    value: float
    date: datetime


class Backtester:
    """Backtester."""

    def __init__(
        self,
        strategy: Strategy,
        symbol: str,
        initial_balance: float = 100_000,
        timeframe: ETimeframe = ETimeframe.MINUTE_1,
        start_ts: int = arrow_to_timestamp(arrow.get("2025-01-01", "YYYY-MM-DD")),
        end_ts: int = arrow_to_timestamp(arrow.get("2025-01-02", "YYYY-MM-DD")),
    ):
        self.strategy = strategy
        self.symbol = symbol
        self.balance: float = initial_balance
        self.position: Literal["short", "long"] | None = None
        self.entry_price: float = 0.0
        self.pnl: float = 0.0
        self.trades: list[Trade] = []
        self.stop_loss: float | None = None
        self.take_profit: float | None = None
        self.bar_returns: list[float] = []
        self.equity_curve: list[Equity] = []
        self.candles: npt.NDArray = []
        self.last_order: Order | None = None
        self.last_timestamp: int | None = None
        self.timeframe = timeframe
        self.start_ts = start_ts
        self.end_ts = end_ts

    async def backtest_stream(  # noqa: C901, PLR0912, PLR0915
        self,
        warmup_bars: int | None = None,
        *,
        show_progress: bool = True,
    ) -> None:
        """Backtest the strategy using a stream of candles."""
        chunker = CandleChunkLoader(
            symbol=self.symbol,
            start_ts=self.start_ts,
            end_ts=self.end_ts,
            limit=100_000,
            overlap=0,
        )
        aggregator = TimeframeAggregator(self.timeframe)

        if warmup_bars is None:
            warmup_bars = 250

        warmed = 0
        processed = 0

        progress = None
        if show_progress:
            num = self.timeframe.to_minutes()
            total_1m = await chunker.count()
            total_agg = total_1m // num
            warmup = warmup_bars or 250
            total_tradable = max(0, total_agg - warmup)
            progress = tqdm_async(
                total=total_tradable,
                desc="Backtesting",
                unit="bars",
                dynamic_ncols=True,
                mininterval=0.5,
                leave=True,
            )

        async for one_min_chunk in chunker:
            agg_chunk = aggregator.feed_chunk(one_min_chunk)
            if len(agg_chunk) == 0:
                continue

            if not self.equity_curve:
                self.equity_curve.append(
                    Equity(
                        value=self.balance,
                        date=sh.timestamp_to_arrow(
                            int(agg_chunk["timestamp"][0]),
                        ).datetime,
                    ),
                )

            if warmed < warmup_bars:
                need = warmup_bars - warmed
                take = min(need, len(agg_chunk))
                if take:
                    for i in range(take):
                        self.strategy.store.candles.add_candle(agg_chunk[i])
                    warmed += take
                start = take
            else:
                start = 0

            tradable = agg_chunk[start:]
            if len(tradable) == 0:
                continue

            for candle in tradable:
                self.strategy.store.candles.add_candle(candle)
                self.strategy.available_margin = self.balance

                if self.strategy.should_long() and self.position is None:
                    self.enter_long(self.strategy.go_long(), candle)
                elif self.strategy.should_short() and self.position is None:
                    self.enter_short(self.strategy.go_short(), candle)

                if self.should_exit_position(candle) and self.position is not None:
                    self.exit_position(candle)

                if self.balance <= 0:
                    raise RuntimeError("Ran out of money")

                self.calculate_returns(candle)

            processed += len(tradable)
            if progress is not None:
                progress.update(len(tradable))

        if progress is not None:
            progress.close()

        if self.position is not None and len(self.strategy.store.candles.candles) > 0:
            last = self.strategy.store.candles.candles[-1]
            self.exit_position(last)
            self.calculate_returns(last)

    def backtest(self, candles: npt.NDArray) -> None:
        """Runs the backtesting loop."""
        candles = generate_candles_from_one_minute_candles(candles, self.timeframe)
        self.candles = candles

        self.equity_curve.append(
            Equity(
                value=self.balance,
                date=sh.timestamp_to_arrow(int(candles["timestamp"][0])).datetime,
            ),
        )
        min_warmup_candles = 300
        self.warmup_candles = 0 if len(candles) < min_warmup_candles else 250
        for i in range(self.warmup_candles):
            self.strategy.store.candles.add_candle(candles[i])

        candles = candles[self.warmup_candles :]
        progress_bar = tqdm(
            enumerate(candles),
            total=len(candles),
            desc="Backtesting Candles",
        )
        for _, candle in progress_bar:
            self.strategy.store.candles.add_candle(candle)
            self.strategy.available_margin = self.balance
            if self.strategy.should_long() and self.position is None:
                self.enter_long(self.strategy.go_long(), candle)
            elif self.strategy.should_short() and self.position is None:
                short_order = self.strategy.go_short()
                self.enter_short(short_order, candle)
            if self.should_exit_position(candle) and self.position is not None:
                self.exit_position(candle)
            if self.balance <= 0:
                raise RuntimeError("Ran out of money")
            progress_bar.set_postfix(
                {"Balance": f"{self.balance:.2f}", "Trades": len(self.trades)},
            )

        progress_bar.close()

        # Exit any open position at the last candle
        if self.position is not None and len(candles) > 0:
            self.exit_position(candles[-1])
            self.calculate_returns(candles[-1])

    def calculate_returns(self, candle: npt.NDArray) -> None:
        equity_now = self._equity_on_bar(candle)
        prev_equity = self.equity_curve[-1].value
        self.bar_returns.append((equity_now - prev_equity) / prev_equity)
        self.equity_curve.append(
            Equity(
                value=equity_now,
                date=sh.timestamp_to_arrow(candle["timestamp"]).datetime,
            ),
        )

    def enter_long(self, order: Order, candle: npt.NDArray) -> None:
        """Enters a long position."""
        self.position = "long"
        self.entry_price = float(order.price)
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        self.last_order = order
        self.last_timestamp = int(candle["timestamp"])

    def exit_long(self, candle: npt.NDArray) -> None:
        """Exits a long position."""
        if self.last_order is None:
            raise RuntimeError(
                "Tried to exit long position, when there was no last order",
            )
        exit_price = self._fill_exit_price(candle)
        trade_pnl = (exit_price - self.entry_price) * float(self.last_order.quantity)
        self.pnl += trade_pnl
        self.balance += trade_pnl
        self.trades.append(
            Trade(
                type="long",
                entry_price=self.entry_price,
                exit_price=exit_price,
                quantity=float(self.last_order.quantity),
                pnl=trade_pnl,
                entry_timestamp=(
                    sh.timestamp_to_arrow(int(self.last_timestamp)).datetime
                    if self.last_timestamp
                    else sh.timestamp_to_arrow(int(candle["timestamp"])).datetime
                ),
                exit_timestamp=sh.timestamp_to_arrow(int(candle["timestamp"])).datetime,
            ),
        )

    def enter_short(self, order: Order, candle: npt.NDArray) -> None:
        """Enters a short position."""
        self.position = "short"
        self.entry_price = float(order.price)
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        self.last_order = order
        self.last_timestamp = int(candle["timestamp"])

    def exit_short(self, candle: npt.NDArray) -> None:
        """Exits a short position."""
        if self.last_order is None:
            raise RuntimeError(
                "Tried to exit short position when there was no last order",
            )
        exit_price = self._fill_exit_price(candle)
        trade_pnl = (self.entry_price - exit_price) * float(self.last_order.quantity)
        self.pnl += trade_pnl
        self.balance += trade_pnl
        self.trades.append(
            Trade(
                type="short",
                entry_price=self.entry_price,
                exit_price=exit_price,
                quantity=float(self.last_order.quantity),
                pnl=trade_pnl,
                entry_timestamp=(
                    sh.timestamp_to_arrow(int(self.last_timestamp)).datetime
                    if self.last_timestamp
                    else sh.timestamp_to_arrow(int(candle["timestamp"])).datetime
                ),
                exit_timestamp=sh.timestamp_to_arrow(int(candle["timestamp"])).datetime,
            ),
        )

    def should_exit_position(self, candle: npt.NDArray) -> bool:
        """Exits a position if hit a stop loss/take profit or the strategy says to exit."""
        if self.position is None:
            return False
        should_exit = False
        high, low = (
            float(candle["high"]),
            float(candle["low"]),
        )
        if self.position == "long":
            if self.stop_loss is not None and low <= self.stop_loss:
                return True
            if self.take_profit is not None and high >= self.take_profit:
                return True
        else:
            if self.stop_loss is not None and high >= self.stop_loss:
                return True
            if self.take_profit is not None and low <= self.take_profit:
                return True
        if self.strategy.should_exit_position():
            should_exit = True
        return should_exit

    def exit_position(self, candle: npt.NDArray) -> None:
        if self.position == "long":
            self.exit_long(candle)
        else:
            self.exit_short(candle)
        self.position = None

    def _fill_exit_price(self, candle: npt.NDArray) -> float:
        high, low, close = (
            float(candle["high"]),
            float(candle["low"]),
            float(candle["close"]),
        )
        if self.position == "long":
            if self.stop_loss is not None and low <= self.stop_loss:
                return float(self.stop_loss)
            if self.take_profit is not None and high >= self.take_profit:
                return float(self.take_profit)
            return close
        if self.stop_loss is not None and high >= self.stop_loss:
            return float(self.stop_loss)
        if self.take_profit is not None and low <= self.take_profit:
            return float(self.take_profit)
        return close

    def _equity_on_bar(self, candle: npt.NDArray) -> float:
        close = float(candle["close"])
        u_pnl = 0.0
        if self.position and self.last_order:
            qty = float(self.last_order.quantity)
            if self.position == "long":
                u_pnl = (close - self.entry_price) * qty
            else:
                u_pnl = (self.entry_price - close) * qty
        return self.balance + u_pnl
