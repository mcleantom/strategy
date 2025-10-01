from __future__ import annotations

import asyncio
from dataclasses import dataclass

import arrow
from loguru import logger

from strategy.indicators import atr, ema
from strategy.models.enums import ETimeframe
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy
from strategy.utils.helpers import arrow_to_timestamp


@dataclass
class EMAPullbackConfig:
    trend_fast: int = 50  # 50-EMA
    trend_slow: int = 200  # 200-EMA (trend filter)
    pullback_band_bps: float = (
        10  # enter when price is within 10 bps below fast EMA (0.10%)
    )
    atr_period: int = 14
    tp_atr: float = 2.0  # take-profit in ATRs
    sl_atr: float = 1.2  # stop-loss in ATRs
    min_bars_between_trades: int = 20
    max_bars_in_trade: int = 90
    cooldown_bars: int = 10
    risk_per_trade: float = 0.002  # 0.2% of equity per trade
    trade_start_minute: int = 10  # skip first 10 bars of each hour (reduce open noise)
    trade_end_buffer_min: int = 5  # skip last 5 bars of each hour


class EMAPullbackV1(Strategy):
    def __init__(self, cfg: EMAPullbackConfig | None = None) -> None:
        super().__init__()
        self.cfg = cfg or EMAPullbackConfig()
        self._cooldown = 0
        self._bars_since_entry = 10**9
        self._bars_in_trade = 0
        self.dbg = {
            "bars_seen": 0,
            "trend_fail": 0,
            "pullback_fail": 0,
            "atr_fail": 0,
            "time_fail": 0,
            "cooldown_fail": 0,
            "minbars_fail": 0,
            "passed_all": 0,
        }

    # ---- utils
    def _have(self, n: int) -> bool:
        return bool(self.candles.shape[0] >= n)

    def _close(self) -> float:
        return float(self.store.candles.most_recent_candle.close)

    def _minute_of_hour(self) -> int:
        # last bar timestamp (seconds)
        ts = self.candles["timestamp"][-1]
        tsf = float(ts)
        if tsf > 1e12:  # normalize ms → sec if needed  # noqa: PLR2004
            tsf /= 1000.0
        return int(tsf // 60) % 60

    def _trend_ok(self) -> bool:
        if not self._have(max(self.cfg.trend_slow, self.cfg.atr_period) + 1):
            return False
        efast = float(ema(self.candles, self.cfg.trend_fast, sequential=False))
        eslow = float(ema(self.candles, self.cfg.trend_slow, sequential=False))
        return efast > eslow

    def _pullback_ok(self) -> bool:
        efast = float(ema(self.candles, self.cfg.trend_fast, sequential=False))
        px = self._close()
        # enter when price pulls slightly below fast EMA (buy the dip in uptrend)
        band = efast * (self.cfg.pullback_band_bps / 1e4)  # bps → fraction
        return px <= efast and px >= (efast - band)

    def _atr(self) -> float | None:
        if not self._have(self.cfg.atr_period + 1):
            return None
        return float(atr(self.candles, period=self.cfg.atr_period, sequential=False))

    def _time_window_ok(self) -> bool:
        if self.cfg.trade_start_minute == 0 and self.cfg.trade_end_buffer_min == 0:
            return True
        m = self._minute_of_hour()
        return (m >= self.cfg.trade_start_minute) and (
            m < 60 - self.cfg.trade_end_buffer_min
        )

    def _qty(self, sl_atr_value: float) -> float:
        equity = float(getattr(self, "available_margin", 0.0) or 0.0)
        if equity <= 0 or sl_atr_value <= 0:
            return 0.0
        risk_cash = equity * self.cfg.risk_per_trade
        return risk_cash / sl_atr_value

    def _levels_from_atr(self, entry: float, atr_val: float) -> tuple[float, float]:
        tp = entry + self.cfg.tp_atr * atr_val
        sl = entry - self.cfg.sl_atr * atr_val
        return tp, sl

    def _tick(self) -> None:
        if self._cooldown > 0:
            self._cooldown -= 1
        self._bars_since_entry += 1
        if self.position is not None:
            self._bars_in_trade += 1
        self.dbg["bars_seen"] += 1

    def should_long(self) -> bool:  # noqa: PLR0911
        self._tick()
        if self.position is not None:
            return False
        if self._cooldown > 0:
            self.dbg["cooldown_fail"] += 1
            return False
        if self._bars_since_entry < self.cfg.min_bars_between_trades:
            self.dbg["minbars_fail"] += 1
            return False
        if not self._time_window_ok():
            self.dbg["time_fail"] += 1
            return False
        if not self._trend_ok():
            self.dbg["trend_fail"] += 1
            return False
        if not self._pullback_ok():
            self.dbg["pullback_fail"] += 1
            return False
        a = self._atr()
        if a is None or a == 0.0:
            self.dbg["atr_fail"] += 1
            return False
        self.dbg["passed_all"] += 1
        return True

    def go_long(self) -> Order:
        entry = self._close()
        a = self._atr() or 0.0
        # risk per unit = sl_atr * ATR
        per_unit_risk = self.cfg.sl_atr * a if a > 0 else 0.0
        qty = self._qty(per_unit_risk)
        tp, sl = self._levels_from_atr(entry, a if a > 0 else 1.0)
        self._bars_in_trade = 0
        self._bars_since_entry = 0
        return Order(quantity=qty, price=entry, take_profit=tp, stop_loss=sl)

    def should_short(self) -> bool:
        return False  # long-only baseline to compare with B&H

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_exit_position(self) -> bool:
        # time stop
        if self.position is None:
            return False
        if self._bars_in_trade >= self.cfg.max_bars_in_trade:
            self._cooldown = self.cfg.cooldown_bars
            return True
        # mean-revert exit: take profits on return to/above fast EMA
        efast = float(ema(self.candles, self.cfg.trend_fast, sequential=False))
        if self._close() >= efast:
            self._cooldown = self.cfg.cooldown_bars
            return True
        return False


async def main() -> None:
    cfg = EMAPullbackConfig(
        trend_fast=34,
        trend_slow=150,
        pullback_band_bps=25,
        atr_period=14,
        tp_atr=2.0,
        sl_atr=1.2,
        min_bars_between_trades=20,
        max_bars_in_trade=120,
        cooldown_bars=10,
        risk_per_trade=0.002,
        trade_start_minute=0,
        trade_end_buffer_min=0,
    )
    strategy = EMAPullbackV1(cfg=cfg)
    backtester = Backtester(
        strategy=strategy,
        symbol="AAPL",
        initial_balance=10_000,
        timeframe=ETimeframe.MINUTE_1,
        start_ts=arrow_to_timestamp(arrow.get("1990-01-01", "YYYY-MM-DD")),
        end_ts=arrow_to_timestamp(arrow.get("2025-01-02", "YYYY-MM-DD")),
    )
    await backtester.backtest_stream()
    logger.info(backtester.balance)


if __name__ == "__main__":
    asyncio.run(main())
