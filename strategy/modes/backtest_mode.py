from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from tqdm.asyncio import tqdm as tqdm_async

import strategy.utils.helpers as sh
from strategy.models.enums import ETimeframe
from strategy.utils.candles_chunk_loader import CandleChunkLoader
from strategy.utils.prefetch_stream import PrefetchStream
from strategy.utils.timeframe_aggrigator import TimeframeAggregator
from loguru import logger
from strategy.models.position import PositionType

if TYPE_CHECKING:
    from datetime import datetime

    import numpy.typing as npt
    from sqlalchemy.ext.asyncio import AsyncSession

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
        start_ts: int = 0,
        end_ts: int = 2**31 - 1,
    ):
        self.strategy = strategy
        self.symbol = symbol
        self.balance: float = initial_balance
        self.available_margin: float = initial_balance
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
        *,
        db: AsyncSession,
        warmup_bars: int = 250,
        show_progress: bool = True,
    ) -> None:
        """Backtest the strategy using a stream of candles."""
        chunker = CandleChunkLoader(
            symbol=self.symbol,
            start_ts=self.start_ts,
            end_ts=self.end_ts,
            limit=100_000,
            overlap=0,
            db=db,
        )
        aggregator = TimeframeAggregator(self.timeframe)

        warmed = 0
        processed = 0

        progress = None
        if show_progress:
            num = self.timeframe.to_minutes()
            total_1m = await chunker.count()
            if total_1m == 0:
                raise RuntimeError("No candles found for backtest")
            total_agg = total_1m // num
            warmup = warmup_bars
            total_tradable = max(0, total_agg - warmup)
            progress = tqdm_async(
                total=total_tradable,
                desc="Backtesting",
                unit="bars",
                dynamic_ncols=True,
                mininterval=0.5,
                leave=True,
            )

        async with PrefetchStream(chunker, prefetch=3) as stream:
            async for one_min_chunk in stream:
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
                    self.strategy.available_margin = self.available_margin

                    if self.position is None and self.strategy.should_long():
                        self.enter_long(self.strategy.go_long(), candle)
                    elif self.position is None and self.strategy.should_short():
                        self.enter_short(self.strategy.go_short(), candle)
                    if self.position is not None and self.should_exit_position(candle):
                        self.exit_position(candle)

                    if self.balance <= 0:
                        raise RuntimeError("Ran out of money")

                    self.calculate_returns(candle)

                processed += len(tradable)
                if progress is not None:
                    progress.set_postfix(
                        balance=f"{self.balance:,.2f}",
                        margin=f"{self.available_margin:,.2f}",
                        pnl=f"{self.pnl:,.2f}",
                        position=self.position if self.position else "none",
                        trades=len(self.trades),
                    )
                    progress.update(len(tradable))

            if progress is not None:
                progress.close()

            if self.position is not None and len(self.strategy.store.candles.candles) > 0:
                last = self.strategy.store.candles.candles[-1]
                self.exit_position(last)
                self.calculate_returns(last)

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
        self.available_margin = self.balance - float(order.quantity) * float(order.price)
        self.strategy.position = PositionType.long

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
        self.available_margin = self.balance

    def enter_short(self, order: Order, candle: npt.NDArray) -> None:
        """Enters a short position."""
        self.position = "short"
        self.entry_price = float(order.price)
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        self.last_order = order
        self.last_timestamp = int(candle["timestamp"])
        self.available_margin = self.balance - float(order.quantity) * float(order.price)
        self.strategy.position = PositionType.short

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
        self.available_margin = self.balance

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
        self.strategy.position = None

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

    def plot_results(self) -> None:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        close_prices = [float(c["close"]) for c in self.strategy.store.candles.candles]
        timestamps = [
            sh.timestamp_to_arrow(int(c["timestamp"])).datetime
            for c in self.strategy.store.candles.candles
        ]
        equity_dates = [e.date for e in self.equity_curve]
        equity_values = [e.value for e in self.equity_curve]

        # --- Plot ---
        fig, ax1 = plt.subplots(figsize=(14, 7))
        ax2 = ax1.twinx()

        # Price
        ax1.plot(timestamps, close_prices, color="gray", label="Close Price", linewidth=1.2)
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Price", color="gray")
        ax1.tick_params(axis="y", labelcolor="gray")

        # Equity curve
        ax2.plot(equity_dates, equity_values, color="blue", label="Equity Curve", linewidth=1.4)
        ax2.set_ylabel("Equity", color="blue")
        ax2.tick_params(axis="y", labelcolor="blue")

        # Trade markers
        for trade in self.trades:
            ax1.scatter(
                trade.entry_timestamp,
                trade.entry_price,
                marker="^",
                color="green",
                s=70,
                label="Entry" if trade == self.trades[0] else "",
                zorder=5,
            )
            ax1.scatter(
                trade.exit_timestamp,
                trade.exit_price,
                marker="v",
                color="red",
                s=70,
                label="Exit" if trade == self.trades[0] else "",
                zorder=5,
            )

        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        # Legend
        ax1.legend(loc="upper left")
        ax2.legend(loc="upper right")

        plt.title(f"Backtest Results: {self.symbol}")
        plt.tight_layout()
        plt.show()
