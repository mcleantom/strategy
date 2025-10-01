from __future__ import annotations

from collections import deque
from math import inf
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    from strategy.models.enums import ETimeframe


class TimeframeAggregator:
    """Streaming aggregator from 1m candles to target timeframe.

    Feed consecutive 1m candles; pull aggregated bars as they become available.
    Keeps only O(num) 1m bars in memory.
    """

    def __init__(self, timeframe: ETimeframe) -> None:
        self.num = timeframe.to_minutes()
        self.buf: deque[np.void] = deque()
        self.dtype = None
        self.k: int = 0
        self.ts0: int = 0
        self.candle_open: float = 0.0
        self.candle_high: float = -inf
        self.candle_low: float = inf
        self.candle_volume: float = 0.0
        self.candle_close: float = 0.0

    def _reset(self) -> None:
        self.k = 0
        self.ts0 = 0
        self.candle_open = 0.0
        self.candle_high = -inf
        self.candle_low = inf
        self.candle_volume = 0.0
        self.candle_close = 0.0

    def feed_chunk(self, chunk: npt.NDArray) -> npt.NDArray:
        """Feed a chunk of 1m candles.

        Feed a chunk of 1m candles (structured array with fields:
        'timestamp','open','close','high','low','volume') ordered by timestamp.
        Returns a structured array of aggregated bars *completed* within this chunk.
        """
        if self.dtype is None:
            self.dtype = chunk.dtype
        if self.num == 1:
            return chunk

        out: list[tuple[float, float, float, float, float, float]] = []

        ts = chunk["timestamp"]
        candle_open = chunk["open"]
        candle_close = chunk["close"]
        candle_high = chunk["high"]
        candle_low = chunk["low"]
        candle_volume = chunk["volume"]

        for i in range(len(chunk)):
            if self.k == 0:
                self.ts0 = int(ts[i])
                self.candle_open = float(candle_open[i])
                self.candle_high = float(candle_high[i])
                self.candle_low = float(candle_low[i])
                self.candle_volume = float(candle_volume[i])
                self.candle_close = float(candle_close[i])
                self.k = 1
            else:
                if candle_high[i] > self.candle_high:
                    self.candle_high = float(candle_high[i])
                if candle_low[i] < self.candle_low:
                    self.candle_low = float(candle_low[i])
                self.candle_volume += float(candle_volume[i])
                self.candle_close = float(candle_close[i])
                self.k += 1

            if self.k == self.num:
                out.append(
                    (
                        self.ts0,
                        self.candle_open,
                        self.candle_close,
                        self.candle_high,
                        self.candle_low,
                        self.candle_volume,
                    ),
                )
                self._reset()

        return (
            np.array(out, dtype=self.dtype) if out else np.empty((0,), dtype=self.dtype)
        )
