from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

import talib

if TYPE_CHECKING:
    import numpy.typing as npt


# overloads
@overload
def adxr(
    candles: npt.NDArray,
    period: int = 14,
    *,
    sequential: Literal[True],
) -> npt.NDArray: ...
@overload
def adxr(
    candles: npt.NDArray,
    period: int = 14,
    *,
    sequential: Literal[False] = False,
) -> float: ...


def adxr(
    candles: npt.NDArray,
    period: int = 14,
    *,
    sequential: bool = False,
) -> float | npt.NDArray:
    """ADXR - Average Directional Movement Index Rating."""
    high = candles["high"]
    low = candles["low"]
    close = candles["close"]
    res: npt.NDArray = talib.ADXR(high, low, close, timeperiod=period)
    return res if sequential else float(res[-1])
