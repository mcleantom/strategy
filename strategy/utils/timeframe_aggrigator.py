from __future__ import annotations

from collections import deque
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

    def feed_chunk(self, one_min_chunk: npt.NDArray) -> npt.NDArray:
        """Feed a chunk of 1m candles.

        Feed a chunk of 1m candles (structured array with fields:
        'timestamp','open','close','high','low','volume') ordered by timestamp.
        Returns a structured array of aggregated bars *completed* within this chunk.
        """
        if self.dtype is None:
            self.dtype = one_min_chunk.dtype

        out: list[tuple[float, float, float, float, float, float]] = []

        for i in range(len(one_min_chunk)):
            c = one_min_chunk[i]
            self.buf.append(c)
            if len(self.buf) == self.num:
                tmp = np.array(list(self.buf), dtype=self.dtype)
                aggregated = (
                    float(tmp["timestamp"][0]),
                    float(tmp["open"][0]),
                    float(tmp["close"][-1]),
                    float(tmp["high"].max()),
                    float(tmp["low"].min()),
                    float(tmp["volume"].sum()),
                )
                out.append(aggregated)
                for _ in range(self.num):
                    self.buf.popleft()

        if not out:
            return np.empty((0,), dtype=self.dtype)
        return np.array(out, dtype=self.dtype)
