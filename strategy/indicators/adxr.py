import numpy.typing as npt
import talib


def adxr(candles: npt.NDArray, period: int = 14, sequential: bool = False) -> float | npt.NDArray:
    """
    ADXR - Average Directional Movement Index Rating
    """
    high = candles["high"]
    low = candles["low"]
    close = candles["close"]
    res = talib.ADXR(high, low, close, timeperiod=period)
    return res if sequential else res[-1]
