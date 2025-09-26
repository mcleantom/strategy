from __future__ import annotations

from strategy.strategy import Order, Strategy


class MyStrategy(Strategy):
    """Base strategy."""

    def should_long(self) -> bool:
        raise NotImplementedError

    def go_long(self) -> Order:
        raise NotImplementedError

    def should_short(self) -> bool:
        raise NotImplementedError

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_cancel_entry(self) -> bool:
        return True
