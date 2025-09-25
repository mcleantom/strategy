import numpy.typing as npt

from strategy.circular_buffer import CircularBuffer
from strategy.db.candle import Candle
from strategy.helpers import to_candle, to_structured_array


class CandleStore:
    def __init__(self):
        self.candles = CircularBuffer((1000, 6), drop_at=500)
        self.candles.array = to_structured_array(self.candles.array)

    def add_candle(self, candle: npt.ArrayLike):
        self.candles.append(candle)

    @property
    def most_recent_candle(self) -> Candle:
        return to_candle(self.candles[-1])
