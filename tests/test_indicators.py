from unittest import TestCase

import numpy as np

import strategy.indicators as si
from strategy.db.candle import Candle
from .data.test_candle_indicators import test_candles_10


class TestIndicators(TestCase):
    @staticmethod
    def to_db_candles(raw_candles: list[tuple[float]]) -> list[Candle]:
        return [Candle(timestamp=c[0], high=c[1], low=c[2], close=c[3], open=c[4], volume=c[5]) for c in raw_candles]

    def test_adx(self):
        candles = self.to_db_candles(test_candles_10)
        result = si.adx(candles, period=14)
        self.assertIsInstance(result, np.ndarray)
        self.assertEquals(round(result[-1]), 26)
