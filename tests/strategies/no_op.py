from __future__ import annotations

from strategy.strategy import Order, Strategy


class NoOpStrategy(Strategy):
    """Does nothing."""

    def should_long(self) -> bool:
        return False

    def go_long(self) -> Order:
        raise NotImplementedError

    def should_short(self) -> bool:
        return False

    def go_short(self) -> Order:
        raise NotImplementedError

    def should_exit_position(self) -> bool:
        return False
