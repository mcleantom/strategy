import time

import numpy as np

import strategy.utils.helpers as sh
from strategy.db.candle import Candle


def test_now_to_timestamp_monotonic():
    t1 = sh.now_to_timestamp()
    time.sleep(0.01)
    t2 = sh.now_to_timestamp()
    assert t2 >= t1


def test_to_candle_from_one_row_struct_array():
    arr = np.zeros(1, dtype=[("open", "f8"), ("close", "f8"), ("high", "f8"), ("low", "f8"), ("volume", "f8")])
    arr[0] = (10.5, 11.5, 12.5, 9.5, 123.0)
    candle = sh.to_candle(arr)
    assert isinstance(candle, Candle)
    assert candle.open == 10.5 and candle.volume == 123.0
