from collections import namedtuple

import numpy as np
import talib

from strategy.db.candle import Candle

AC = namedtuple("AC", ["osc", "change"])


def acosc(candles: list[Candle], sequential: bool = False) -> AC:
    high = np.array([c.high for c in candles])
    low = np.array([c.low for c in candles])
    med = talib.MEDPRICE(high, low)
    ao = talib.SMA(med, 5) - talib.SMA(med, 34)

    res = ao - talib.SMA(ao, 5)
    mom = talib.MOM(res, timeperiod=1)

    if sequential:
        return AC(res, mom)
    else:
        return AC(res[-1], mom[-1])
