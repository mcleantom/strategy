from __future__ import annotations

from typing import Literal, NamedTuple, overload

import numpy as np
import numpy.typing as npt

from strategy.utils.helpers import np_shift, slice_candles


class AGArray(NamedTuple):
    jaw: np.ndarray
    teeth: np.ndarray
    lips: np.ndarray


class AGScalar(NamedTuple):
    jaw: float
    teeth: float
    lips: float


@overload
def alligator(
    candles: npt.NDArray,
    source_type: str = "close",
    *,
    sequential: Literal[True],
) -> AGArray: ...
@overload
def alligator(
    candles: npt.NDArray,
    source_type: str = "close",
    *,
    sequential: Literal[False] = False,
) -> AGScalar: ...
def alligator(
    candles: npt.NDArray,
    source_type: str = "close",
    *,
    sequential: bool = False,
) -> AGArray | AGScalar:
    """Alligator."""
    candles = slice_candles(candles, sequential=sequential)
    source = candles[source_type]
    jaw = np_shift(numpy_ewma(source, 13), 8, fill_value=np.nan)
    teeth = np_shift(numpy_ewma(source, 8), 5, fill_value=np.nan)
    lips = np_shift(numpy_ewma(source, 5), 3, fill_value=np.nan)
    if sequential:
        return AGArray(jaw, teeth, lips)
    return AGScalar(float(jaw[-1]), float(teeth[-1]), float(lips[-1]))


def numpy_ewma(data: npt.NDArray, window: int) -> npt.NDArray:
    """Exponentially Weighted Moving Average."""
    alpha = 1 / window
    n = data.shape[0]
    scale_arr = (1 - alpha) ** (-1 * np.arange(n))
    weights = (1 - alpha) ** np.arange(n)
    pw0 = (1 - alpha) ** (n - 1)
    mult = data * pw0 * scale_arr
    cum_sums = mult.cumsum()
    return cum_sums * scale_arr[::-1] / weights.cumsum()
