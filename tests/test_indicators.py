import numpy as np
import numpy.typing as npt

from tests.data.test_candle_indicators import test_candles_10, test_candles_19

import strategy.indicators as ta
from strategy.db.candle import Candle
from strategy.helpers import to_numpy_array


def _to_db_candles(raw_candles: list[tuple[float, ...]]) -> npt.NDArray:
    return to_numpy_array(
        [Candle(timestamp=c[0], high=c[3], low=c[4], close=c[2], open=c[1], volume=c[5]) for c in raw_candles]
    )


def test_acosc():
    candles = _to_db_candles(test_candles_19)
    single = ta.acosc(candles)
    sequence = ta.acosc(candles, sequential=True)
    assert round(single.osc, 2) == round(-21.97, 2)
    assert round(single.change, 2) == round(-9.22, 2)
    assert sequence.osc[-1] == single.osc
    assert len(sequence.osc) == len(candles)


def test_ad():
    candles = _to_db_candles(test_candles_19)
    single = ta.ad(candles)
    sequence = ta.ad(candles, sequential=True)
    assert round(single, 0) == round(6346031, 0)
    assert len(sequence) == len(candles)
    assert sequence[-1] == single


def test_adosc():
    candles = _to_db_candles(test_candles_19)
    single = ta.adosc(candles, fast_period=3, slow_period=10)
    sequence = ta.adosc(candles, fast_period=3, slow_period=10, sequential=True)
    assert round(float(single) / 1000000, 3) == -1.122
    assert len(sequence) == len(candles)
    assert sequence[-1] == single


def test_adx():
    candles = _to_db_candles(test_candles_10)
    result = ta.adx(candles, period=14, sequential=True)
    assert isinstance(result, np.ndarray)
    assert round(float(result[-1])) == 26


def test_adxr():
    candles = _to_db_candles(test_candles_19)
    single = ta.adxr(candles, period=14)
    sequence = ta.adxr(candles, period=14, sequential=True)
    assert round(single, 0) == 36
    assert len(sequence) == len(candles)
    assert sequence[-1] == single


def test_alligator():
    candles = _to_db_candles(test_candles_19)
    single = ta.alligator(candles)
    sequence = ta.alligator(candles, sequential=True)
    assert round(single.teeth, 0) == 236
    assert round(single.jaw, 0) == 233
    assert round(single.lips, 0) == 222
    assert sequence.teeth[-1] == single.teeth
    assert len(sequence.teeth) == len(candles)
