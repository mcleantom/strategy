from abc import ABC, abstractmethod
from dataclasses import dataclass

from strategy.db.candle import Candle


@dataclass
class Order:
    quantity: float
    price: float
    take_profit: float | None = None
    stop_loss: float | None = None


class Strategy(ABC):
    def __init__(self):
        self.candles: list[Candle] = []

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
