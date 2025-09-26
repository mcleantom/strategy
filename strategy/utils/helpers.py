from __future__ import annotations

import uuid

import arrow
import numpy as np
import numpy.typing as npt

from strategy.db.candle import CandleModel


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


def to_numpy_array(candles: list[CandleModel]) -> npt.NDArray:
    return np.array(
        [
            (
                candle.timestamp,
                candle.open,
                candle.close,
                candle.high,
                candle.low,
                candle.volume,
            )
            for candle in candles
        ],
        dtype=[
            ("timestamp", "i8"),
            ("open", "f8"),
            ("close", "f8"),
            ("high", "f8"),
            ("low", "f8"),
            ("volume", "f8"),
        ],
    )


def to_structured_array(array: npt.NDArray) -> npt.NDArray:
    # Validate input dimensions
    two_dimensions = 2
    n_candle_parameters = 6
    if array.ndim != two_dimensions or array.shape[1] != n_candle_parameters:
        raise ValueError("Input array must be two-dimensional with exactly 6 columns.")

    # Create a structured array with the specified dtype
    dtype = [
        ("timestamp", "i8"),
        ("open", "f8"),
        ("close", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("volume", "f8"),
    ]
    structured_array = np.zeros(array.shape[0], dtype=dtype)

    # Assign data to structured fields
    structured_array["timestamp"] = array[:, 0]
    structured_array["open"] = array[:, 1]
    structured_array["close"] = array[:, 2]
    structured_array["high"] = array[:, 3]
    structured_array["low"] = array[:, 4]
    structured_array["volume"] = array[:, 5]

    return structured_array


def to_candle(row_or_arr: np.void | np.ndarray) -> CandleModel:
    # Structured row (np.void) with named fields
    if isinstance(row_or_arr, np.void):
        row = row_or_arr
        return CandleModel(
            open=float(row["open"]),
            close=float(row["close"]),
            high=float(row["high"]),
            low=float(row["low"]),
            volume=float(row["volume"]),
        )

    # 1-row structured array
    if isinstance(row_or_arr, np.ndarray) and getattr(row_or_arr.dtype, "names", None):
        row = (
            row_or_arr[0] if row_or_arr.shape and row_or_arr.shape[0] == 1 else row_or_arr
        )
        return CandleModel(
            open=float(row["open"]),
            close=float(row["close"]),
            high=float(row["high"]),
            low=float(row["low"]),
            volume=float(row["volume"]),
        )

    # Fallback: positional row (open, close, high, low, volume)
    row = (
        row_or_arr[0]
        if hasattr(row_or_arr, "__len__")
        and len(row_or_arr)
        and hasattr(row_or_arr[0], "__len__")
        else row_or_arr
    )
    return CandleModel(
        open=float(row[0]),
        close=float(row[1]),
        high=float(row[2]),
        low=float(row[3]),
        volume=float(row[4]),
    )


def slice_candles(candles: np.ndarray, *, sequential: bool) -> npt.NDArray:
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
