from __future__ import annotations

from typing import TYPE_CHECKING

from strategy.utils.circular_buffer import CircularBuffer
from strategy.utils.helpers import to_candle, to_structured_array

if TYPE_CHECKING:
    import numpy.typing as npt

    from strategy.db.candle import CandleModel


class CandleStore:
    """Store of candles."""

    def __init__(self) -> None:
        self.candles = CircularBuffer((1000, 6), drop_at=500)
        self.candles.array = to_structured_array(self.candles.array)

    def add_candle(self, candle: npt.ArrayLike) -> None:
        self.candles.append(candle)

    @property
    def most_recent_candle(self) -> CandleModel:
        return to_candle(self.candles[-1])
