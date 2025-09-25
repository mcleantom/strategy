from strategy.strategy import Order, Strategy


class MyStrategy(Strategy):
    def should_long(self) -> bool:
        raise NotImplementedError

    def go_long(self) -> Order:
        raise NotImplementedError

    def should_short(self) -> bool:
        raise NotImplementedError

    def go_short(self) -> Order | None:
        raise NotImplementedError

    def should_cancel_entry(self) -> bool:
        return False
