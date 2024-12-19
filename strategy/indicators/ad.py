import numpy as np
import numpy.typing as npt
import talib

from strategy.db.candle import Candle


def ad(candles: npt.NDArray, sequential: bool = False) -> float | npt.NDArray:
    """
    Chaikin A/D Line
    """
    high = candles["high"]
    low = candles["low"]
    close = candles["close"]
    volume = candles["volume"]
    res = talib.AD(high, low, close, volume)
    return res if sequential else res[-1]
