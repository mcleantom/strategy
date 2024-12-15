import numpy as np
import numpy.typing as npt
import talib

from strategy.db.candle import Candle


def ad(candles: list[Candle], sequential: bool = False) -> float | npt.NDArray:
    """
    Chaikin A/D Line
    """
    high = np.array([c.high for c in candles])
    low = np.array([c.low for c in candles])
    close = np.array([c.close for c in candles])
    volume = np.array([c.volume for c in candles])
    res = talib.AD(high, low, close, volume)
    return res if sequential else res[-1]
