from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

import talib

if TYPE_CHECKING:
    import numpy.typing as npt


@overload
def ad(candles: npt.NDArray, *, sequential: Literal[True]) -> npt.NDArray: ...
@overload
def ad(candles: npt.NDArray, *, sequential: Literal[False] = False) -> float: ...


def ad(candles: npt.NDArray, *, sequential: bool = False) -> float | npt.NDArray:
    """Chaikin A/D Line."""
    high = candles["high"]
    low = candles["low"]
    close = candles["close"]
    volume = candles["volume"]
    res: npt.NDArray = talib.AD(high, low, close, volume)
    return res if sequential else float(res[-1])
