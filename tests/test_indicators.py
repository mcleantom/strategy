from unittest import TestCase

import numpy as np
import numpy.typing as npt

from tests.data.test_candle_indicators import test_candles_10, test_candles_19

import strategy.indicators as ta
from strategy.db.candle import Candle
from strategy.helpers import to_numpy_array


class TestIndicators(TestCase):
    @staticmethod
    def to_db_candles(raw_candles: list[tuple[float]]) -> npt.NDArray:
        return to_numpy_array([Candle(timestamp=c[0], high=c[3], low=c[4], close=c[2], open=c[1], volume=c[5]) for c in raw_candles])

    def test_acosc(self):
        candles = self.to_db_candles(test_candles_19)
        single = ta.acosc(candles)
        sequence = ta.acosc(candles, sequential=True)
        self.assertAlmostEqual(single.osc, -21.97, 2)
        self.assertAlmostEqual(single.change, -9.22, 2)
        self.assertEquals(sequence.osc[-1], single.osc)
        self.assertEquals(len(sequence.osc), len(candles))

    def test_ad(self):
        candles = self.to_db_candles(test_candles_19)
        single = ta.ad(candles)
        sequence = ta.ad(candles, sequential=True)
        self.assertAlmostEqual(single, 6346031, 0)
        self.assertEquals(len(sequence), len(candles))
        self.assertEquals(sequence[-1], single)

    def test_adosc(self):
        candles = self.to_db_candles(test_candles_19)
        single = ta.adosc(candles, fast_period=3, slow_period=10)
        sequence = ta.adosc(candles, fast_period=3, slow_period=10, sequential=True)
        self.assertAlmostEqual(round(single / 1000000, 3), -1.122, 3)
        self.assertEquals(len(sequence), len(candles))
        self.assertEquals(sequence[-1], single)

    def test_adx(self):
        candles = self.to_db_candles(test_candles_10)
        result = ta.adx(candles, period=14, sequential=True)
        self.assertIsInstance(result, np.ndarray)
        self.assertEquals(round(float(result[-1])), 26)

    def test_adxr(self):
        candles = self.to_db_candles(test_candles_19)
        single = ta.adxr(candles, period=14)
        sequence = ta.adxr(candles, period=14, sequential=True)
        self.assertAlmostEqual(single, 36, 0)
        self.assertEquals(len(sequence), len(candles))
        self.assertEquals(sequence[-1], single)

    def test_alligator(self):
        candles = self.to_db_candles(test_candles_19)
        single = ta.alligator(candles)
        sequence = ta.alligator(candles, sequential=True)
        self.assertAlmostEqual(single.teeth, 236, 0)
        self.assertAlmostEqual(single.jaw, 233, 0)
        self.assertAlmostEqual(single.lips, 222, 0)
        self.assertEquals(sequence.teeth[-1], single.teeth)
        self.assertEquals(len(sequence.teeth), len(candles))
