import numpy.typing as npt
import talib

from strategy.utils.helpers import slice_candles


def adosc(
    candles: npt.NDArray, fast_period: int = 3, slow_period: int = 10, sequential: bool = False
) -> float | npt.NDArray:
    """
    ADOSC - Chaikin A/D Oscillator
    """
    candles = slice_candles(candles, sequential)
    high = candles["high"]
    low = candles["low"]
    close = candles["close"]
    volume = candles["volume"]
    res = talib.ADOSC(high, low, close, volume, fastperiod=fast_period, slowperiod=slow_period)
    return res if sequential else res[-1]
