from strategy.db.candle import Candle
from strategy.circular_buffer import CircularBuffer
from strategy.helpers import to_numpy_array, to_candle, to_structured_array


class CandleStore:
    def __init__(self):
        self.candles = CircularBuffer((1000, 5))
        self.candles.array = to_structured_array(self.candles.array)

    def add_candle(self, candle: Candle):
        self.candles.append(to_numpy_array([candle]))

    @property
    def most_recent_candle(self) -> Candle:
        return to_candle(self.candles[-1])
