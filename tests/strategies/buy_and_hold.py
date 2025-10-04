from __future__ import annotations

from strategy.strategy import Order, Strategy

__all__ = [
    "BuyAndHoldStrategy",
]


class BuyAndHoldStrategy(Strategy):
    """Buy and hold."""

    def __init__(self) -> None:
        super().__init__()
        self._has_gone_long = False

    def should_long(self) -> bool:
        if self._has_gone_long is False:
            self._has_gone_long = True
            return True
        return False

    def go_long(self) -> Order:
        return Order(quantity=1, price=float(self.candles[-1]["close"]))

    def should_short(self) -> bool:
        return False

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_exit_position(self) -> bool:
        return False
