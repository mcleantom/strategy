from strategy.db.candle import Candle


class CandleStore:
    def __init__(self):
        self.candles: list[Candle] = []

    def add_candle(self, candle: Candle):
        self.candles.append(candle)

    @property
    def most_recent_candle(self) -> Candle:
        return self.candles[-1]
