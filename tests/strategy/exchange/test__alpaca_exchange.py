import aiohttp
import pytest
from aioresponses import aioresponses

from strategy.exchange.alpaca_exchange import AlpacaExchange

BASE = "https://paper-api.alpaca.markets/v2"


async def test_market_order():
    with aioresponses() as m:
        m.post(f"{BASE}/orders", payload={"id": "ord_market_1"})
        async with AlpacaExchange(api_key="k", api_secret="s") as ex:
            oid = await ex.market_order("AAPL", 1, 150.0, "buy", False)
            assert oid == "ord_market_1"


async def test_limit_order():
    with aioresponses() as m:
        m.post(f"{BASE}/orders", payload={"id": "ord_limit_2"})
        async with AlpacaExchange(api_key="k", api_secret="s") as ex:
            oid = await ex.limit_order("AAPL", 1, 145.0, "buy", False)
            assert oid == "ord_limit_2"


async def test_stop_order():
    with aioresponses() as m:
        m.post(f"{BASE}/orders", payload={"id": "ord_stop_3"})
        async with AlpacaExchange(api_key="k", api_secret="s") as ex:
            oid = await ex.stop_order("AAPL", 1, 140.0, "sell", False)
            assert oid == "ord_stop_3"


async def test_cancel_all_orders():
    with aioresponses() as m:
        # First list existing orders
        m.get(
            f"{BASE}/orders",
            payload=[{"id": "o1"}, {"id": "o2"}],
        )
        # Then cancel each by id
        m.delete(f"{BASE}/orders/o1", status=204, payload={})
        m.delete(f"{BASE}/orders/o2", status=204, payload={})

        async with AlpacaExchange(api_key="k", api_secret="s") as ex:
            # Should not raise
            await ex.cancel_all_orders("AAPL")


async def test_get_balance():
    with aioresponses() as m:
        m.get(f"{BASE}/account", payload={"equity": "12345.67"})
        async with AlpacaExchange(api_key="k", api_secret="s") as ex:
            bal = await ex.get_balance()
            assert bal == 12345.67


async def test_fetch_precisions():
    with aioresponses() as m:
        m.get(f"{BASE}/assets", payload=[{"symbol": "AAPL"}, {"symbol": "MSFT"}])
        async with AlpacaExchange(api_key="k", api_secret="s") as ex:
            assets = await ex._fetch_precisions()
            assert {a["symbol"] for a in assets} == {"AAPL", "MSFT"}


async def test_400_response():
    with aioresponses() as m:
        m.get(f"{BASE}/account", payload={"message": "unauthorized."}, status=401)
        async with AlpacaExchange(api_key="k", api_secret="s") as ex:
            with pytest.raises(aiohttp.ClientResponseError) as err:
                await ex.get_balance()
    assert err.value.message == 'Unauthorized; body={"message": "unauthorized."}'


def test_no_api_key():
    with pytest.raises(RuntimeError) as exc:
        AlpacaExchange()
    assert str(exc.value) == "ALPACA_KEY and ALPACA_SECRET must be set or passed in."


async def test_dont_own_session():
    async with (
        aiohttp.ClientSession() as session,
        AlpacaExchange(
            session=session,
            api_key="k",
            api_secret="s",
        ) as exchange,
    ):
        assert not exchange._owns_session
        assert exchange._session == session
    assert exchange._session is None
