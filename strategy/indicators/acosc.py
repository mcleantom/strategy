from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NamedTuple, overload

import talib

if TYPE_CHECKING:
    import numpy.typing as npt


class ACArray(NamedTuple):
    osc: npt.NDArray
    change: npt.NDArray


class ACScalar(NamedTuple):
    osc: float
    change: float


@overload
def acosc(candles: npt.NDArray, *, sequential: Literal[True]) -> ACArray: ...
@overload
def acosc(candles: npt.NDArray, *, sequential: Literal[False] = False) -> ACScalar: ...


def acosc(candles: npt.NDArray, *, sequential: bool = False) -> ACArray | ACScalar:
    high = candles["high"]
    low = candles["low"]
    med = talib.MEDPRICE(high, low)

    ao: npt.NDArray = talib.SMA(med, 5) - talib.SMA(med, 34)
    res: npt.NDArray = ao - talib.SMA(ao, 5)
    mom: npt.NDArray = talib.MOM(res, timeperiod=1)

    if sequential:
        return ACArray(res, mom)
    return ACScalar(float(res[-1]), float(mom[-1]))
