from __future__ import annotations

from strategy.strategy import Order, Strategy

__all__ = [
    "DummyStrategy",
]


class DummyStrategy(Strategy):
    """Buy and hold."""

    def __init__(self) -> None:
        super().__init__()
        self._should_long = False

    def should_long(self) -> bool:
        return self._should_long

    def go_long(self) -> Order:
        return Order(quantity=1, price=float(self.candles[-1]["close"]))

    def should_short(self) -> bool:
        return False

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_cancel_entry(self) -> bool:
        return False
