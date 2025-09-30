from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from strategy.db import CandleModel
from strategy.db.base import AsyncSessionLocal
from strategy.models.enums import ETimeframe
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy
from strategy.utils.helpers import to_numpy_array


@dataclass
class BuyAndHoldConfig:
    """Config for Buy & Hold."""

    invest_all: bool = True
    invest_fraction: float = 1.0
    fixed_quantity: float | None = None
    start_after_bars: int = 0


class BuyAndHold(Strategy):
    """Buys once and holds until the backtest ends.

    - If invest_all=True: quantity = (available_margin * invest_fraction) / entry_price
    - Else: quantity = fixed_quantity (default 1 if None)
    No stop/TP; no re-entries; no shorts.
    """

    def __init__(self, cfg: BuyAndHoldConfig | None = None) -> None:
        super().__init__()
        self.cfg = cfg or BuyAndHoldConfig()
        self._bars_seen = 0
        self._bought = False

    # ---------- helpers ----------

    def _close(self) -> float:
        return float(self.store.candles.most_recent_candle.close)

    def _quantity(self, price: float) -> float:
        if not self.cfg.invest_all:
            return float(
                self.cfg.fixed_quantity if self.cfg.fixed_quantity is not None else 1.0,
            )
        if price <= 0.0:
            return 0.0
        equity = self.available_margin
        invest = max(0.0, min(1.0, self.cfg.invest_fraction)) * equity
        return invest / price if price > 0 else 0.0

    # ---------- Strategy API ----------

    def should_long(self) -> bool:
        self._bars_seen += 1
        if self._bought:
            return False
        # Buy once after waiting start_after_bars bars
        return self._bars_seen > self.cfg.start_after_bars

    def go_long(self) -> Order:
        price = self._close()
        qty = self._quantity(price)  # use available_margin * invest_fraction
        self._bought = True
        return Order(quantity=qty, price=price, stop_loss=None, take_profit=None)

    def should_short(self) -> bool:
        return False

    def go_short(self) -> Order:
        raise NotImplementedError("BuyAndHold never shorts.")

    def should_exit_position(self) -> bool:
        return False


async def main() -> None:
    timeframe = ETimeframe.DAY_1
    backtester = Backtester(
        strategy=BuyAndHold(
            BuyAndHoldConfig(
                invest_all=True,
                invest_fraction=1.0,
                start_after_bars=0,
            ),
        ),
        initial_balance=10_000,
        timeframe=timeframe,
    )
    stmt = (
        select(CandleModel)
        .where(CandleModel.symbol == "AAPL")
        .order_by(CandleModel.timestamp)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
    db_candles = result.scalars().all()
    candles = to_numpy_array(db_candles)
    backtester.backtest(candles)


if __name__ == "__main__":
    asyncio.run(main())
