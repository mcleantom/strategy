from collections import namedtuple

import numpy as np
import numpy.typing as npt
import talib

from strategy.db.candle import Candle

AC = namedtuple("AC", ["osc", "change"])


def acosc(candles: npt.NDArray, sequential: bool = False) -> AC:
    high = candles["high"]
    low = candles["low"]
    med = talib.MEDPRICE(high, low)
    ao = talib.SMA(med, 5) - talib.SMA(med, 34)

    res = ao - talib.SMA(ao, 5)
    mom = talib.MOM(res, timeperiod=1)

    if sequential:
        return AC(res, mom)
    else:
        return AC(res[-1], mom[-1])
