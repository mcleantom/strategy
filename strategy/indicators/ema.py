import numpy.typing as npt
import talib

from strategy.helpers import slice_candles


def ema(
    candles: npt.NDArray, period: int = 5, source_type: str = "close", sequential: bool = False
) -> float | npt.NDArray:
    candles = slice_candles(candles, sequential)
    source = candles[source_type]

    res = talib.EMA(source, timeperiod=period)

    return res if sequential else res[-1]
