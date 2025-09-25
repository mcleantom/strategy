import numpy as np
import pytest

import strategy.utils.helpers as sh
from strategy.db.candle import Candle


def test_generate_unique_id_unique_and_string():
    a = sh.generate_unique_id()
    b = sh.generate_unique_id()
    assert isinstance(a, str) and isinstance(b, str)
    assert a != b


def test_timestamp_conversions_roundtrip():
    ts_ms = 1_700_000_000_000
    arr = sh.timestamp_to_arrow(ts_ms)
    assert sh.arrow_to_timestamp(arr) == ts_ms
    assert isinstance(sh.timestamp_to_time(ts_ms), str)


def test_date_diff_in_days_abs():
    d1 = sh.timestamp_to_arrow(0)
    d2 = sh.timestamp_to_arrow(3 * 24 * 3600 * 1000)
    assert sh.date_diff_in_days(d1, d2) == 3
    assert sh.date_diff_in_days(d2, d1) == 3


def test_to_numpy_array_and_to_structured_array():
    candles = [
        Candle(timestamp=1, open=10, close=11, high=12, low=9, volume=100),
        Candle(timestamp=2, open=11, close=12, high=13, low=10, volume=110),
    ]
    arr = sh.to_numpy_array(candles)
    assert arr.dtype.names == ("timestamp", "open", "close", "high", "low", "volume")
    # to_structured_array expects (n,6) ndarray of floats/ints
    dense = np.array([[1, 10.0, 11.0, 12.0, 9.0, 100.0], [2, 11.0, 12.0, 13.0, 10.0, 110.0]])
    struct = sh.to_structured_array(dense)
    assert struct.dtype.names == arr.dtype.names
    assert struct[0]["open"] == 10.0 and struct[1]["close"] == 12.0


def test_to_structured_array_invalid_shape_raises():
    bad = np.array([[1, 2], [3, 4]])
    with pytest.raises(ValueError):
        sh.to_structured_array(bad)


def test_to_candle_from_struct_row_and_positional():
    struct = np.zeros(1, dtype=[("open", "f8"), ("close", "f8"), ("high", "f8"), ("low", "f8"), ("volume", "f8")])
    struct[0] = (10.0, 11.0, 12.0, 9.0, 100.0)
    c1 = sh.to_candle(struct[0])
    assert isinstance(c1, Candle)
    assert c1.open == 10.0 and c1.close == 11.0
    # positional row fallback
    c2 = sh.to_candle([10.0, 11.0, 12.0, 9.0, 100.0])
    assert c2.high == 12.0 and c2.low == 9.0


def test_slice_candles_and_np_shift():
    # slice_candles
    arr = np.zeros(
        500,
        dtype=[("timestamp", "i8"), ("open", "f8"), ("close", "f8"), ("high", "f8"), ("low", "f8"), ("volume", "f8")],
    )
    sliced = sh.slice_candles(arr, sequential=False)
    assert len(sliced) == 240
    sliced2 = sh.slice_candles(arr[:100], sequential=False)
    assert len(sliced2) == 100
    # np_shift
    dense = np.array([1, 2, 3, 4, 5])
    shifted = sh.np_shift(dense, 2, fill_value=0)
    assert shifted.tolist() == [0, 0, 1, 2, 3]
    shifted_back = sh.np_shift(dense, -2, fill_value=9)
    assert shifted_back.tolist() == [3, 4, 5, 9, 9]
