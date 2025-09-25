import os

import pytest

from strategy.exchange.alpaca_exchange import AlpacaExchange

requires_live = pytest.mark.skipif(os.getenv("LIVE_EXCHANGE") != "1", reason="Skipping live exchange calls")


@requires_live
def test_market_order():
    exchange = AlpacaExchange()
    exchange.market_order("AAPL", 1, 150.0, "buy", False)


@requires_live
def test_limit_order():
    exchange = AlpacaExchange()
    exchange.limit_order("AAPL", 1, 145.0, "buy", False)


@requires_live
def test_stop_order():
    exchange = AlpacaExchange()
    exchange.stop_order("AAPL", 1, 140.0, "sell", False)


@requires_live
def test_cancel_all_orders():
    exchange = AlpacaExchange()
    exchange.cancel_all_orders("AAPL")


@requires_live
def test_balance():
    exchange = AlpacaExchange()
    exchange.get_balance()
