from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from strategy.models.position import Position, PositionType
from strategy.store.store import Store

if TYPE_CHECKING:
    import numpy.typing as npt


@dataclass
class Order:
    """Order model."""

    quantity: float
    price: float
    take_profit: float | None = None
    stop_loss: float | None = None


class Strategy(ABC):
    """Base class for strategies."""

    def __init__(self, store: Store | None = None):
        self.store = store if store else Store()
        self.name = None
        self.symbol = None
        self.exchange = None
        self.timeframe = None
        self.hp = None
        self.index = 0
        self.vars: dict[str, object] = {}
        self.increased_count = 0
        self.reduced_count = 0
        self.buy = None
        self.sell = None
        self.stop_loss = None
        self.take_profit = None
        self.position: Position | None = None
        self._available_margin: float = 0.0

    @abstractmethod
    def go_long(self) -> Order:
        """Returns the long order."""

    @abstractmethod
    def go_short(self) -> Order:
        """Returns the short order."""

    @abstractmethod
    def should_long(self) -> bool:
        """Returns if the strategy should make a long order."""

    @abstractmethod
    def should_short(self) -> bool:
        """Returns if the strategy should make a short order."""

    @abstractmethod
    def should_cancel_entry(self) -> bool:
        """Returns if the strategy should cancel the order."""

    @property
    def available_margin(self) -> float:
        return self._available_margin

    @property
    def candles(self) -> npt.NDArray:
        return self.store.candles.candles

    @property
    def is_long(self) -> bool:
        if self.position is None:
            return False
        return self.position.type == PositionType.long

    @property
    def is_short(self) -> bool:
        if self.position is None:
            return False
        return self.position.type == PositionType.short
