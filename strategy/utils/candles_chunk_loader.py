from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sqlalchemy import asc, func, select

from strategy.db.base import AsyncSessionLocal
from strategy.db.candle import CandleModel

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import numpy.typing as npt


@dataclass
class CandleChunkLoader:
    """Async loader that yields *ordered* 1m candles in chunks without loading everything into memory."""

    symbol: str
    start_ts: int
    end_ts: int | None = None
    limit: int = 50_000
    overlap: int = 0

    async def __aiter__(self) -> AsyncIterator[npt.NDArray[np.void]]:
        last_ts = self.start_ts - 1
        symbol = self.symbol

        while True:
            async with AsyncSessionLocal() as session:
                stmt = (
                    select(CandleModel)
                    .where(
                        CandleModel.symbol == symbol,
                        CandleModel.timeframe == "1m",
                        CandleModel.timestamp > last_ts,
                        *(
                            []
                            if self.end_ts is None
                            else [CandleModel.timestamp <= self.end_ts]
                        ),
                    )
                    .order_by(asc(CandleModel.timestamp))
                    .limit(self.limit)
                )
                result = await session.execute(stmt)
                rows = result.scalars().all()

            if not rows:
                break

            struct_dtype = np.dtype(
                [
                    ("timestamp", "i8"),
                    ("open", "f8"),
                    ("close", "f8"),
                    ("high", "f8"),
                    ("low", "f8"),
                    ("volume", "f8"),
                ],
            )

            out = np.empty(len(rows), dtype=struct_dtype)

            for i, r in enumerate(rows):
                out["timestamp"][i] = int(r.timestamp)
                out["open"][i] = float(r.open)
                out["close"][i] = float(r.close)
                out["high"][i] = float(r.high)
                out["low"][i] = float(r.low)
                out["volume"][i] = float(r.volume)

            yield out

            last_ts = int(out["timestamp"][-1])

            if self.overlap > 0:
                last_ts -= self.overlap * 60_000

            if self.end_ts is not None and last_ts >= self.end_ts:
                break

    async def count(self) -> int:
        """Count the number of candles in the database."""
        async with AsyncSessionLocal() as session:
            stmt = (
                select(func.count())
                .select_from(CandleModel)
                .where(
                    CandleModel.symbol == self.symbol,
                    CandleModel.timeframe == "1m",
                    CandleModel.timestamp >= self.start_ts,
                    *(
                        []
                        if self.end_ts is None
                        else [CandleModel.timestamp <= self.end_ts]
                    ),
                )
            )
            result = await session.execute(stmt)
            return int(result.scalar_one())
