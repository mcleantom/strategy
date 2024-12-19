from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy.typing as npt

from strategy.store.store import Store
from strategy.models.position import Position, PositionType


@dataclass
class Order:
    quantity: float
    price: float
    take_profit: float | None = None
    stop_loss: float | None = None


class Strategy(ABC):
    def __init__(self, store: Store | None = None):
        self.store = store if store else Store()
        self.name = None
        self.symbol = None
        self.exchange = None
        self.timeframe = None
        self.hp = None
        self.index = 0
        self.vars = {}
        self.increased_count = 0
        self.reduced_count = 0
        self.buy = None
        self.sell = None
        self.stop_loss = None
        self.take_profit = None
        self.position: Position | None = None
        self._available_margin = 0

    @abstractmethod
    def go_long(self) -> Order:
        pass

    @abstractmethod
    def go_short(self) -> Order:
        pass

    @abstractmethod
    def should_long(self) -> bool:
        pass

    @abstractmethod
    def should_short(self) -> bool:
        pass

    @abstractmethod
    def should_cancel_entry(self) -> bool:
        pass

    @property
    def price(self) -> float:
        return float(self.candles["close"][-1])

    @property
    def available_margin(self) -> float:
        return self._available_margin

    @property
    def candles(self) -> npt.NDArray:
        return self.store.candles.candles

    @property
    def fee_rate(self) -> float:
        return 0

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
