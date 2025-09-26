from __future__ import annotations

from typing import TYPE_CHECKING

import talib

from strategy.utils.helpers import slice_candles

if TYPE_CHECKING:
    import numpy.typing as npt


def ema(
    candles: npt.NDArray,
    period: int = 5,
    source_type: str = "close",
    *,
    sequential: bool = False,
) -> float | npt.NDArray:
    candles = slice_candles(candles, sequential=sequential)
    source = candles[source_type]

    res = talib.EMA(source, timeperiod=period)

    return res if sequential else res[-1]
