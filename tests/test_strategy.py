from unittest import TestCase

from strategy.db.base import SessionLocal
from strategy.db.candle import Candle
from strategy.modes.backtest_mode import Backtester
from strategy.strategy import Order, Strategy


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


class TestStrategy(TestCase):
    def test_example_strategy(self):
        candles = [
            Candle(
                timestamp=1,
                open=100,
                high=110,
                low=90,
                close=105,
                volume=1000,
                exchange="NYSE",
                symbol="AAPL",
                timeframe="1D",
            ),
            Candle(
                timestamp=2,
                open=106,
                high=115,
                low=104,
                close=110,
                volume=1000,
                exchange="NYSE",
                symbol="AAPL",
                timeframe="1D",
            ),
            Candle(
                timestamp=3,
                open=111,
                high=120,
                low=109,
                close=115,
                volume=1000,
                exchange="NYSE",
                symbol="AAPL",
                timeframe="1D",
            ),
            Candle(
                timestamp=4,
                open=116,
                high=125,
                low=114,
                close=120,
                volume=1000,
                exchange="NYSE",
                symbol="AAPL",
                timeframe="1D",
            ),
        ]

        strategy = ExampleStrategy()
        backtester = Backtester(strategy=strategy, initial_balance=10_000)
        backtester.backtest(candles)

        self.assertEquals(len(backtester.trades), 1)
        self.assertEqual(backtester.trades[0].type, "long")
        self.assertEqual(backtester.trades[0].entry_price, 105)
        self.assertEqual(backtester.trades[0].exit_price, 120)
        self.assertEqual(backtester.pnl, 120 - 105)

    def test_real_data(self):
        session = SessionLocal()
        aapl_candles = session.query(Candle).filter(Candle.symbol == "AAPL").all()
        strategy = ExampleStrategy()
        backtester = Backtester(strategy=strategy, initial_balance=10_000)
        backtester.backtest(aapl_candles)
        print(backtester.pnl)
