import numpy as np
import numpy.typing as npt
import talib

from strategy.db.candle import Candle


def adx(candles: list[Candle], period: int = 14) -> float | npt.NDArray:
    high = np.array([c.high for c in candles])
    low = np.array([c.low for c in candles])
    close = np.array([c.close for c in candles])
    res = talib.ADX(high, low, close, timeperiod=period)
    return res
