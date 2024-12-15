import numpy as np
import numpy.typing as npt
import talib

from strategy.db.candle import Candle


def adxr(candles: list[Candle], period: int = 14, sequential: bool = False) -> float | npt.NDArray:
    """
    ADXR - Average Directional Movement Index Rating
    """
    high = np.array([c.high for c in candles])
    low = np.array([c.low for c in candles])
    close = np.array([c.close for c in candles])
    res = talib.AD(high, low, close, timeperiod=period)
    return res if sequential else res[-1]
