from collections import namedtuple

import numpy as np
import numpy.typing as npt

from strategy.db.candle import Candle
from strategy.helpers import np_shift, slice_candles, to_numpy_array

AG = namedtuple("AG", ["jaw", "teeth", "lips"])


def alligator(candles: npt.NDArray, source_type: str = "close", sequential: bool = False) -> AG:
    """
    Alligator
    """
    candles = slice_candles(candles, sequential)
    source = candles[source_type]
    jaw = np_shift(numpy_ewma(source, 13), 8, fill_value=np.nan)
    teeth = np_shift(numpy_ewma(source, 8), 5, fill_value=np.nan)
    lips = np_shift(numpy_ewma(source, 5), 3, fill_value=np.nan)
    if sequential:
        return AG(jaw, teeth, lips)
    return AG(jaw[-1], teeth[-1], lips[-1])


def numpy_ewma(data: npt.NDArray, window: int):
    """Exponentially Weighted Moving Average"""
    alpha = 1 / window
    n = data.shape[0]
    scale_arr = (1 - alpha) ** (-1 * np.arange(n))
    weights = (1 - alpha) ** np.arange(n)
    pw0 = (1 - alpha) ** (n - 1)
    mult = data * pw0 * scale_arr
    cum_sums = mult.cumsum()
    return cum_sums * scale_arr[::-1] / weights.cumsum()
