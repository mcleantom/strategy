from __future__ import annotations

from typing import Any

from strategy.exchange.base_exchange import Exchange

__all__ = [
    "DummyExchange",
]


class DummyExchange(Exchange):
    """Buy and hold."""

    def __init__(self, balance: float = 10_000):
        self._balance = balance
        self.orders: list[dict[str, Any]] = []
        self.cancelled: list[tuple[str]] = []

    async def market_order(
        self,
        symbol: str,
        qty: float,
        current_price: float,
        side: str,
        reduce_only: bool = False,
    ) -> str:
        self.orders.append(
            {
                "symbol": symbol,
                "qty": qty,
                "price": current_price,
                "side": side,
                "reduce_only": reduce_only,
            },
        )
        return "ORDER-1"

    async def limit_order(
        self,
        symbol: str,
        qty: float,
        price: float,
        side: str,
        *,
        reduce_only: bool,
    ) -> str:
        raise NotImplementedError

    async def stop_order(
        self,
        symbol: str,
        qty: float,
        price: float,
        side: str,
        *,
        reduce_only: bool,
    ) -> str:
        raise NotImplementedError

    async def cancel_all_orders(self, symbol: str) -> None:
        raise NotImplementedError

    async def cancel_order(self, order_id: str) -> None:
        self.cancelled.append((order_id,))

    async def get_balance(self) -> float:
        return self._balance

    async def _fetch_precisions(self) -> list[dict[str, str]]:
        raise NotImplementedError
