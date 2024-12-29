from unittest import TestCase
from strategy.exchange.alpaca_exchange import AlpacaExchange


class TestExchanges(TestCase):

    def test_market_order(self):
        exchange = AlpacaExchange()
        exchange.market_order("AAPL", 1, 150.0, "buy", False)

    def test_limit_order(self):
        exchange = AlpacaExchange()
        exchange.limit_order("AAPL", 1, 145.0, "buy", False)

    def test_stop_order(self):
        exchange = AlpacaExchange()
        exchange.stop_order("AAPL", 1, 140.0, "sell", False)

    def test_cancel_all_orders(self):
        exchange = AlpacaExchange()
        exchange.cancel_all_orders("AAPL")

    def test_balance(self):
        exchange = AlpacaExchange()
        exchange.get_balance()
