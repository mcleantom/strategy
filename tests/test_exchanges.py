from unittest import TestCase
from strategy.exchange.alpaca_exchange import AlpacaExchange
import requests


class TestExchanges(TestCase):

    def test_market_order(self):
        exchange = AlpacaExchange()
        response = exchange.market_order("AAPL", 1, 150.0, "buy", False)
        self.assertIn("id", response)

    def test_limit_order(self):
        exchange = AlpacaExchange()
        response = exchange.limit_order("AAPL", 1, 145.0, "buy", False)
        self.assertIn("id", response)

    def test_stop_order(self):
        exchange = AlpacaExchange()
        response = exchange.stop_order("AAPL", 1, 140.0, "sell", False)
        self.assertIn("id", response)

    def test_cancel_all_orders(self):
        exchange = AlpacaExchange()
        try:
            exchange.cancel_all_orders("AAPL")
        except requests.exceptions.HTTPError as e:
            self.fail(f"cancel_all_orders raised an HTTPError: {e}")
