from __future__ import annotations

from strategy.db import CandleModel


def mk_candle(ts: int, price: float) -> CandleModel:
    return CandleModel(
        timestamp=ts,
        open=price,
        high=price,
        low=price,
        close=price,
        volume=0.0,
        exchange="NYSE",
        symbol="AAPL",
        timeframe="1m",
    )
