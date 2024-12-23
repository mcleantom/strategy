from strategy.strategy import Strategy, Order


class MyStrategy(Strategy):

    def should_long(self) -> bool:
        pass

    def go_long(self) -> Order:
        pass

    def should_short(self) -> bool:
        pass

    def go_short(self):
        pass

    def should_cancel_entry(self) -> bool:
        return False
