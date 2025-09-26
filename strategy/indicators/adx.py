from __future__ import annotations

from typing import TYPE_CHECKING

import talib

if TYPE_CHECKING:
    import numpy.typing as npt


def adx(
    candles: npt.NDArray,
    period: int = 14,
    *,
    sequential: bool = False,
) -> float | npt.NDArray:
    high = candles["high"]
    low = candles["low"]
    close = candles["close"]
    res = talib.ADX(high, low, close, timeperiod=period)
    return res if sequential else res[-1]
