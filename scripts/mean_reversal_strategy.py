from __future__ import annotations

import asyncio

import numpy as np
from sqlalchemy import select

from strategy.db import CandleModel
from strategy.db.base import AsyncSessionLocal
from strategy.indicators import adx, atr, ema
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy
from strategy.utils.helpers import to_numpy_array


class MeanReversionV4(Strategy):
    """
    Mean Reversion with strict anti-churn controls.

    - z = (close - SMA(window)) / std(window)
    - Enter only when:
        * Regime is ranging: ADX <= max_adx
        * Trend alignment: long only if close > EMA(trend_period); short only if close < EMA
        * Signal persistence: last `confirm_bars` bars all beyond entry_z (same side)
        * Min ATR filter: ATR >= min_atr
        * Cooldown satisfied and min bars since last exit satisfied
    - Exit when:
        * |z| <= exit_z  (mean reversion achieved), OR
        * time stop hit
      (TP/SL also set using ATR at entry)

    Parameters
    ----------
    window : int                # z-score window
    entry_z : float             # entry band (>=)
    exit_z : float              # exit band (<=), must be < entry_z
    trend_period : int          # EMA period for regime direction
    adx_period : int            # ADX lookback
    max_adx : float             # only trade when ADX <= max_adx
    atr_period : int            # ATR lookback
    tp_atr : float | None       # TP in ATRs (None to disable)
    sl_atr : float | None       # SL in ATRs (None to disable)
    min_atr : float | None      # skip if ATR < min_atr (price units)
    confirm_bars : int          # require N consecutive bars beyond entry_z
    cooldown_bars : int         # bars to wait after exit
    min_bars_between_trades : int  # from last entry to next entry
    max_bars_in_trade : int | None # time stop in bars
    qty : float
    """

    def __init__(
        self,
        *,
        window: int = 40,
        entry_z: float = 1.8,
        exit_z: float = 0.5,
        trend_period: int = 200,
        adx_period: int = 14,
        max_adx: float = 18.0,
        atr_period: int = 14,
        tp_atr: float | None = 1.6,
        sl_atr: float | None = 1.0,
        min_atr: float | None = None,
        confirm_bars: int = 2,
        cooldown_bars: int = 8,
        min_bars_between_trades: int = 20,
        max_bars_in_trade: int | None = 60,
        qty: float = 1.0,
    ):
        super().__init__()
        assert exit_z < entry_z, "exit_z must be < entry_z for hysteresis"
        self.window = window
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.trend_period = trend_period
        self.adx_period = adx_period
        self.max_adx = max_adx
        self.atr_period = atr_period
        self.tp_atr = tp_atr
        self.sl_atr = sl_atr
        self.min_atr = min_atr
        self.confirm_bars = confirm_bars
        self.cooldown_bars = cooldown_bars
        self.min_bars_between_trades = min_bars_between_trades
        self.max_bars_in_trade = max_bars_in_trade
        self.qty = qty

        # runtime state
        self._bars_in_trade = 0
        self._cooldown_left = 0
        self._bars_since_last_entry = 10**9  # large so first trade isn't blocked

    # --------- helpers ---------

    def _have(self, n: int) -> bool:
        return getattr(self, "candles", None) is not None and self.candles.shape[0] >= n

    def _close(self) -> float:
        return float(self.store.candles.most_recent_candle.close)

    def _z_now(self) -> float | None:
        if not self._have(self.window):
            return None
        closes = self.candles["close"][-self.window:].astype(float)
        mu = float(np.mean(closes))
        sd = float(np.std(closes, ddof=1))
        if sd == 0.0:
            return None
        return (closes[-1] - mu) / sd

    def _z_series(self, n: int) -> np.ndarray | None:
        # last n z-scores for persistence check
        need = max(self.window + n - 1, self.window)
        if not self._have(need):
            return None
        closes = self.candles["close"][-(self.window + n - 1):].astype(float)
        zs = []
        for i in range(n):
            win = closes[i : i + self.window]
            mu = win.mean()
            sd = win.std(ddof=1)
            if sd == 0.0:
                return None
            zs.append((win[-1] - mu) / sd)
        return np.array(zs, dtype=float)

    def _ema_ok(self, side: str) -> bool:
        if not self._have(self.trend_period):
            return False
        e = float(ema(self.candles, period=self.trend_period, sequential=False))
        c = self._close()
        return (c > e) if side == "long" else (c < e)

    def _adx_ok(self) -> bool:
        if not self._have(self.adx_period + 1):
            return False
        a = float(adx(self.candles, period=self.adx_period, sequential=False))
        return a <= self.max_adx

    def _atr_val(self) -> float | None:
        if not self._have(self.atr_period + 1):
            return None
        return float(atr(self.candles, period=self.atr_period, sequential=False))

    def _levels_from_atr(self, entry: float, side: str) -> tuple[float | None, float | None]:
        a = self._atr_val()
        tp = sl = None
        if a is not None:
            if self.tp_atr is not None:
                tp = entry + self.tp_atr * a if side == "long" else entry - self.tp_atr * a
            if self.sl_atr is not None:
                sl = entry - self.sl_atr * a if side == "long" else entry + self.sl_atr * a
        return tp, sl

    def _tick(self):
        # call each bar via should_long/should_short
        if self.position is not None and self.max_bars_in_trade is not None:
            self._bars_in_trade += 1
        if self._cooldown_left > 0:
            self._cooldown_left -= 1
        self._bars_since_last_entry += 1

    def _can_enter(self) -> bool:
        if self._cooldown_left > 0:
            return False
        if self._bars_since_last_entry < self.min_bars_between_trades:
            return False
        if not self._adx_ok():
            return False
        a = self._atr_val()
        if self.min_atr is not None and (a is None or a < self.min_atr):
            return False
        return True

    def _persisted_signal(self, side: str) -> bool:
        zs = self._z_series(self.confirm_bars)
        if zs is None:
            return False
        if side == "long":
            return np.all(zs <= -self.entry_z)
        else:
            return np.all(zs >= self.entry_z)

    # --------- Strategy API ---------

    def should_long(self) -> bool:
        self._tick()
        if not self._can_enter():
            return False
        if not self._ema_ok("long"):
            return False
        # persistence + hysteresis
        if self._persisted_signal("long"):
            if self.position is None:
                return True
            if self.is_short:
                z = self._z_now()
                return (z is not None) and (abs(z) <= self.exit_z)
        return False

    def should_short(self) -> bool:
        self._tick()
        if not self._can_enter():
            return False
        if not self._ema_ok("short"):
            return False
        if self._persisted_signal("short"):
            if self.position is None:
                return True
            if self.is_long:
                z = self._z_now()
                return (z is not None) and (abs(z) <= self.exit_z)
        return False

    def go_long(self) -> Order:
        entry = self._close()
        tp, sl = self._levels_from_atr(entry, "long")
        self._bars_in_trade = 0
        self._bars_since_last_entry = 0
        return Order(quantity=self.qty, price=entry, take_profit=tp, stop_loss=sl)

    def go_short(self) -> Order:
        entry = self._close()
        tp, sl = self._levels_from_atr(entry, "short")
        self._bars_in_trade = 0
        self._bars_since_last_entry = 0
        return Order(quantity=self.qty, price=entry, take_profit=tp, stop_loss=sl)

    def should_cancel_entry(self) -> bool:
        return False

    # Optional: if your Backtester can consult this each bar to force exits
    def should_exit_position(self) -> bool:
        z = self._z_now()
        if self.position is None or z is None:
            return False

        # time stop
        if self.max_bars_in_trade is not None and self._bars_in_trade >= self.max_bars_in_trade:
            self._cooldown_left = self.cooldown_bars
            return True

        # mean-reversion achieved
        if abs(z) <= self.exit_z:
            self._cooldown_left = self.cooldown_bars
            return True

        return False



async def main():
    backtester = Backtester(
        strategy=MeanReversionV4(
            window=40,
            entry_z=1.8,
            exit_z=0.4,
            adx_period=14,
            max_adx=18,
            confirm_bars=8,
            min_bars_between_trades=20,
            tp_atr=1.6,
            sl_atr=1.0,
            max_bars_in_trade=60,
        ),
        initial_balance=10_000,
    )
    stmt = select(CandleModel).where(CandleModel.symbol == "AAPL").order_by(CandleModel.timestamp)
    async with AsyncSessionLocal() as session:
        result = await session.execute(stmt)
    candles = result.scalars().all()
    backtester.backtest(to_numpy_array(candles))


if __name__ == "__main__":
    asyncio.run(main())
