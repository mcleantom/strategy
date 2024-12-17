import numpy as np
import numpy.typing as npt
import talib
from strategy.helpers import slice_candles, to_numpy_array
from strategy.db.candle import Candle


def ema(candles: list[Candle], period: int = 5, source_type: str = "close", sequential: bool = False) -> float | npt.NDArray:
    candles = to_numpy_array(candles)

    candles = slice_candles(candles, sequential)
    source = candles[source_type]

    res = talib.EMA(source, timeperiod=period)

    return res if sequential else res[-1]
