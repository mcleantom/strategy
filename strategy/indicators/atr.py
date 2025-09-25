import numpy.typing as npt
import talib

from strategy.utils.helpers import slice_candles


def atr(candles: npt.NDArray, period: int = 14, sequential: bool = False) -> float | npt.NDArray:
    """
    ATR - Average True Range
    """
    candles = slice_candles(candles, sequential)

    res = talib.ATR(candles["high"], candles["low"], candles["close"], timeperiod=period)

    return res if sequential else res[-1]
