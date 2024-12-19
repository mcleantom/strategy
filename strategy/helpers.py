import uuid

import arrow
import numpy as np
import numpy.typing as npt

from strategy.db.candle import Candle


def generate_unique_id():
    return str(uuid.uuid4())


def arrow_to_timestamp(arrow_time: arrow.arrow.Arrow) -> int:
    return arrow_time.int_timestamp * 1000


def timestamp_to_arrow(timestamp: int) -> arrow.arrow.Arrow:
    return arrow.get(timestamp / 1000)


def timestamp_to_time(timestamp: int) -> str:
    return str(arrow.get(timestamp / 1000))


def date_diff_in_days(date1: arrow.arrow.Arrow, date2: arrow.arrow.Arrow) -> int:
    dif = date2 - date1
    return abs(dif.days)


def now_to_timestamp() -> int:
    return arrow.utcnow().int_timestamp * 1000


def to_numpy_array(candles: list[Candle]) -> npt.NDArray:
    return np.array(
        [(candle.open, candle.close, candle.high, candle.low, candle.volume) for candle in candles],
        dtype=[("open", "f8"), ("close", "f8"), ("high", "f8"), ("low", "f8"), ("volume", "f8")],
    )


def to_structured_array(array: npt.NDArray, field_names: list[str] | None = None) -> npt.NDArray:
    if field_names is None:
        field_names = ["open", "close", "high", "low", "volume"]
    if array.ndim != 2:
        raise ValueError("Input array must be two dimensional")
    if len(field_names) != array.shape[1]:
        raise ValueError("Number of field names must match the number of columns in the array")
    dtype = [(name, array.dtype) for name in field_names]
    structured_array = np.zeros(array.shape[0], dtype=dtype)
    for i, name in enumerate(field_names):
        structured_array[name] = array[:, i]
    return structured_array


def to_candle(arr: npt.NDArray) -> Candle:
    assert len(arr) == 1
    return Candle(
        open=arr[0],
        close=arr[1],
        high=arr[2],
        low=arr[3],
        volume=arr[4]
    )


def slice_candles(candles: np.ndarray, sequential: bool) -> npt.NDArray:
    warmup_candles_num = 240
    if not sequential and candles.shape[0] > warmup_candles_num:
        candles = candles[-warmup_candles_num:]
    return candles


def np_shift(arr: npt.NDArray, num: int, fill_value=0) -> npt.NDArray:
    result = np.empty_like(arr)

    if num > 0:
        result[:num] = fill_value
        result[num:] = arr[:-num]
    elif num < 0:
        result[num:] = fill_value
        result[:num] = arr[-num:]
    else:
        result[:] = arr

    return result
