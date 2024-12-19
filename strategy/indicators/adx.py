import numpy as np
import numpy.typing as npt
import talib

from strategy.db.candle import Candle


def adx(candles: npt.NDArray, period: int = 14, sequential: bool = False) -> float | npt.NDArray:
    high = candles["high"]
    low = candles["low"]
    close = candles["close"]
    res = talib.ADX(high, low, close, timeperiod=period)
    return res if sequential else res[-1]
