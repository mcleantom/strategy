from __future__ import annotations

from collections.abc import AsyncGenerator

import aiohttp
import pytest
from aioresponses import aioresponses

from strategy.exchange.alpaca_exchange import AlpacaExchange

BASE = "https://paper-api.alpaca.markets/v2"


@pytest.fixture  # type: ignore[misc]
async def exchange() -> AsyncGenerator[AlpacaExchange]:
    async with AlpacaExchange(
        api_key="k",
        api_secret="s",  # noqa: S106
    ) as ex:
        yield ex


async def test_market_order(exchange: AlpacaExchange) -> None:
    with aioresponses() as m:
        m.post(f"{BASE}/orders", payload={"id": "ord_market_1"})
        oid = await exchange.market_order("AAPL", 1, 150.0, "buy", reduce_only=False)
        assert oid == "ord_market_1"


async def test_limit_order(exchange: AlpacaExchange) -> None:
    with aioresponses() as m:
        m.post(f"{BASE}/orders", payload={"id": "ord_limit_2"})
        oid = await exchange.limit_order("AAPL", 1, 145.0, "buy", reduce_only=False)
        assert oid == "ord_limit_2"


async def test_stop_order(exchange: AlpacaExchange) -> None:
    with aioresponses() as m:
        m.post(f"{BASE}/orders", payload={"id": "ord_stop_3"})
        oid = await exchange.stop_order("AAPL", 1, 140.0, "sell", reduce_only=False)
        assert oid == "ord_stop_3"


async def test_cancel_all_orders(exchange: AlpacaExchange) -> None:
    with aioresponses() as m:
        # First list existing orders
        m.get(
            f"{BASE}/orders",
            payload=[{"id": "o1"}, {"id": "o2"}],
        )
        # Then cancel each by id
        m.delete(f"{BASE}/orders/o1", status=204, payload={})
        m.delete(f"{BASE}/orders/o2", status=204, payload={})
        await exchange.cancel_all_orders("AAPL")


async def test_get_balance(exchange: AlpacaExchange) -> None:
    with aioresponses() as m:
        m.get(f"{BASE}/account", payload={"equity": "12345.67"})
        bal = await exchange.get_balance()
        assert bal == 12345.67


async def test_fetch_precisions(exchange: AlpacaExchange) -> None:
    with aioresponses() as m:
        m.get(f"{BASE}/assets", payload=[{"symbol": "AAPL"}, {"symbol": "MSFT"}])
        assets = await exchange._fetch_precisions()
        assert {a["symbol"] for a in assets} == {"AAPL", "MSFT"}


async def test_400_response(exchange: AlpacaExchange) -> None:
    with aioresponses() as m:
        m.get(f"{BASE}/account", payload={"message": "unauthorized."}, status=401)
        with pytest.raises(aiohttp.ClientResponseError) as err:
            await exchange.get_balance()
    assert err.value.message == 'Unauthorized; body={"message": "unauthorized."}'


def test_no_api_key() -> None:
    with pytest.raises(RuntimeError) as exc:
        AlpacaExchange()
    assert str(exc.value) == "ALPACA_KEY and ALPACA_SECRET must be set or passed in."


async def test_dont_own_session() -> None:
    async with (
        aiohttp.ClientSession() as session,
        AlpacaExchange(
            session=session,
            api_key="k",
            api_secret="s",  # noqa: S106
        ) as exchange,
    ):
        assert not exchange._owns_session
        assert exchange._session == session
    assert exchange._session is None
