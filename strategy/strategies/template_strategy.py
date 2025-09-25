from strategy.strategy import Order, Strategy


class MyStrategy(Strategy):
    def should_long(self) -> bool:
        pass

    def go_long(self) -> Order:
        pass

    def should_short(self) -> bool:
        pass

    def go_short(self) -> Order:
        pass

    def should_cancel_entry(self) -> bool:
        return True
