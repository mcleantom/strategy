from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

import talib

from strategy.utils.helpers import slice_candles

if TYPE_CHECKING:
    import numpy.typing as npt


@overload
def adosc(
    candles: npt.NDArray,
    fast_period: int = 3,
    slow_period: int = 10,
    *,
    sequential: Literal[True],
) -> npt.NDArray: ...
@overload
def adosc(
    candles: npt.NDArray,
    fast_period: int = 3,
    slow_period: int = 10,
    *,
    sequential: Literal[False] = False,
) -> float: ...


def adosc(
    candles: npt.NDArray,
    fast_period: int = 3,
    slow_period: int = 10,
    *,
    sequential: bool = False,
) -> float | npt.NDArray:
    """ADOSC - Chaikin A/D Oscillator."""
    candles = slice_candles(candles, sequential=sequential)
    high = candles["high"]
    low = candles["low"]
    close = candles["close"]
    volume = candles["volume"]
    res: npt.NDArray = talib.ADOSC(
        high,
        low,
        close,
        volume,
        fastperiod=fast_period,
        slowperiod=slow_period,
    )
    return res if sequential else float(res[-1])
