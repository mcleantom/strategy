from unittest import TestCase

from strategy.strategy import Strategy, Order
from strategy.db.candle import Candle
from strategy.modes.backtest_mode import Backtester


class ExampleStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.has_bought = False

    def should_long(self) -> bool:
        return not self.has_bought

    def go_long(self) -> Order:
        self.has_bought = True
        return Order(quantity=1, price=self.store.candles.most_recent_candle.close, stop_loss=None, take_profit=None)

    def should_short(self) -> bool:
        return False

    def go_short(self) -> None:
        pass

    def should_cancel_entry(self) -> bool:
        return False


class TestBacktester(TestCase):

    def test_buy_short(self):
        strategy = ExampleStrategy()
        backtester = Backtester(strategy, initial_balance=1000)
        order = Order(
            quantity=10,
            price=100
        )
        candle = Candle(
            timestamp=1
        )
        backtester.enter_short(order,candle)
        self.assertEquals(backtester.balance, 2000)
        candle = Candle(
            timestamp=1,
            close=100
        )
        backtester.exit_short(candle)
        self.assertEqual(backtester.balance, 1000)

