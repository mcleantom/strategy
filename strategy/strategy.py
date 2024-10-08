from abc import ABC, abstractmethod
from dataclasses import dataclass

from strategy.store.store import Store


@dataclass
class Order:
    quantity: float
    price: float
    take_profit: float | None = None
    stop_loss: float | None = None


class Strategy(ABC):
    def __init__(self, store: Store | None = None):
        self.store = store if store else Store()

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
