# strategy/exchange/alpaca_exchange.py
from __future__ import annotations

import os
from http import HTTPStatus
from typing import Any

import aiohttp

from .base_exchange import Exchange


class AlpacaExchange(Exchange):
    def __init__(
        self,
        *,
        session: aiohttp.ClientSession | None = None,
        base_url: str = "https://paper-api.alpaca.markets/v2",
        api_key: str | None = None,
        api_secret: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("ALPACA_KEY")
        self.api_secret = api_secret or os.environ.get("ALPACA_SECRET")
        if not self.api_key or not self.api_secret:
            raise RuntimeError("ALPACA_KEY and ALPACA_SECRET must be set or passed in.")
        self._session = session
        self._owns_session = session is None
        self._headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

    # ---- lifecycle ---------------------------------------------------------
    async def __aenter__(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)
            self._owns_session = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._owns_session and self._session:
            await self._session.close()
        self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:  # pragma: no cover
        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._headers)
            self._owns_session = True
        return self._session

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        async with self.session.request(method, url, **kwargs) as resp:
            if resp.status >= HTTPStatus.BAD_REQUEST:
                body = await resp.text()
                try:
                    resp.raise_for_status()
                except aiohttp.ClientResponseError as e:
                    raise aiohttp.ClientResponseError(
                        request_info=e.request_info,
                        history=e.history,
                        status=e.status,
                        message=f"{e.message}; body={body}",
                        headers=e.headers,
                    ) from e
            return await resp.json()

    async def market_order(
        self,
        symbol: str,
        qty: float,
        current_price: float,
        side: str,
        *,
        reduce_only: bool,
    ) -> str:
        del current_price
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "market",
            "time_in_force": "gtc",
            "reduce_only": reduce_only,
        }
        data = await self._request("POST", "/orders", json=order_data)
        return data["id"]

    async def limit_order(
        self,
        symbol: str,
        qty: float,
        price: float,
        side: str,
        *,
        reduce_only: bool,
    ) -> str:
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "limit",
            "limit_price": price,
            "time_in_force": "gtc",
            "reduce_only": reduce_only,
        }
        data = await self._request("POST", "/orders", json=order_data)
        return data["id"]

    async def stop_order(
        self,
        symbol: str,
        qty: float,
        price: float,
        side: str,
        *,
        reduce_only: bool,
    ) -> str:
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "stop",
            "stop_price": price,
            "time_in_force": "gtc",
            "reduce_only": reduce_only,
        }
        data = await self._request("POST", "/orders", json=order_data)
        return data["id"]

    async def cancel_all_orders(self, symbol: str) -> None:
        orders: list[dict[str, Any]] = await self._request(
            "GET",
            "/orders",
            json={"symbols": [symbol]},
        )
        for order in orders:
            await self.cancel_order(symbol, order["id"])

    async def cancel_order(self, order_id: str) -> None:
        await self._request("DELETE", f"/orders/{order_id}")

    async def get_balance(self) -> float:
        account_data = await self._request("GET", "/account")
        return float(account_data["equity"])

    async def _fetch_precisions(self):
        return await self._request("GET", "/assets")
