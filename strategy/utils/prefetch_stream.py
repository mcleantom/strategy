# prefetch.py
from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterable
    from types import TracebackType

    from strategy.utils.types import CandleChunk


@dataclass
class PrefetchStream:
    """PrefetchStream.

    Wraps an async iterator of CandleChunk and prefetches `prefetch` items
    into a bounded asyncio.Queue to overlap DB I/O and compute.
    """

    source: AsyncIterable[CandleChunk]
    prefetch: int = 3  # chunks to stay ahead
    yield_sleep: float = 0.0  # tiny sleep to yield control (optional)

    def __post_init__(self) -> None:
        self._queue: asyncio.Queue[CandleChunk | None] = asyncio.Queue(self.prefetch)
        self._producer_task: asyncio.Task[None] | None = None
        self._exc: BaseException | None = None

    async def __aenter__(self) -> Self:
        self._producer_task = asyncio.create_task(
            self._producer(),
            name="candle-producer",
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        del exc_type, exc, tb
        await self.aclose()

    async def aclose(self) -> None:
        if self._producer_task and not self._producer_task.done():
            self._producer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._producer_task

    async def _producer(self) -> None:
        try:
            async for item in self.source:
                await self._queue.put(item)
                if self.yield_sleep:
                    await asyncio.sleep(self.yield_sleep)
        except BaseException as e:
            self._exc = e
        finally:
            await self._queue.put(None)  # sentinel

    def __aiter__(self) -> AsyncGenerator[CandleChunk]:
        return self._consumer()

    async def _consumer(self) -> AsyncGenerator[CandleChunk]:
        try:
            while True:
                item = await self._queue.get()
                if item is None:
                    break
                yield item
            if self._exc:
                raise self._exc
        finally:
            await self.aclose()
