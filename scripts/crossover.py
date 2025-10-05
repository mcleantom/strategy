from __future__ import annotations

import asyncio

import arrow
from loguru import logger

from strategy.db.base import AsyncSessionLocal
from strategy.indicators import ema
from strategy.models.enums import ETimeframe
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy
from strategy.utils.helpers import arrow_to_timestamp


class EmaCrossoverStrategy(Strategy):
    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 50,
        quantity: float = 1.0,
    ) -> None:
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.quantity = quantity
        self.last_signal = None  # prevent repeated same-side triggers

    def should_long(self) -> bool:
        candles = self.candles
        if len(candles) < self.slow_period + 2:
            return False  # not enough data

        fast = ema(candles, self.fast_period, sequential=True)
        slow = ema(candles, self.slow_period, sequential=True)

        cross_up = fast[-2] < slow[-2] and fast[-1] > slow[-1]
        if cross_up and self.last_signal != "long":
            self.last_signal = "long"
            return True
        return False

    def should_short(self) -> bool:
        candles = self.candles
        if len(candles) < self.slow_period + 2:
            return False

        fast = ema(candles, self.fast_period, sequential=True)
        slow = ema(candles, self.slow_period, sequential=True)

        cross_down = fast[-2] > slow[-2] and fast[-1] < slow[-1]
        if cross_down and self.last_signal != "short":
            self.last_signal = "short"
            return True
        return False

    def should_exit_position(self):
        candles = self.candles
        if len(candles) < self.slow_period + 2:
            return False

        fast = ema(candles, self.fast_period, sequential=True)
        slow = ema(candles, self.slow_period, sequential=True)

        # Exit only on opposite crossover
        if self.is_long and fast[-1] < slow[-1]:
            return True
        return bool(self.is_short and fast[-1] > slow[-1])

    def go_long(self) -> Order:
        price = float(self.candles["close"][-1])
        return Order(quantity=self.quantity, price=price)

    def go_short(self) -> Order:
        price = float(self.candles["close"][-1])
        return Order(quantity=self.quantity, price=price)


async def main() -> None:
    strategy = EmaCrossoverStrategy(fast_period=10, slow_period=50, quantity=1.0)
    backtester = Backtester(
        strategy=strategy,
        symbol="AAPL",
        timeframe=ETimeframe.MINUTE_15,
        initial_balance=10_000,
        start_ts=arrow_to_timestamp(arrow.get("1990-01-01", "YYYY-MM-DD")),
        end_ts=arrow_to_timestamp(arrow.get("2025-01-02", "YYYY-MM-DD")),
    )
    async with AsyncSessionLocal() as db:
        await backtester.backtest_stream(db=db)
    logger.info(backtester.balance)
    backtester.plot_results()


if __name__ == "__main__":
    asyncio.run(main())
