from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import talib

if TYPE_CHECKING:
    import numpy.typing as npt

class AC(NamedTuple):
    osc: float
    change: float


def acosc(candles: npt.NDArray, *, sequential: bool = False) -> AC:
    high = candles["high"]
    low = candles["low"]
    med = talib.MEDPRICE(high, low)
    ao: float = talib.SMA(med, 5) - talib.SMA(med, 34)

    res: float = ao - talib.SMA(ao, 5)
    mom = talib.MOM(res, timeperiod=1)

    if sequential:
        return AC(res, mom)
    return AC(res[-1], mom[-1])
