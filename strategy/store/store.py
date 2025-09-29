from __future__ import annotations

from strategy.store.candles import CandleStore


class Store:
    """Store."""

    def __init__(self) -> None:
        self.candles = CandleStore()
