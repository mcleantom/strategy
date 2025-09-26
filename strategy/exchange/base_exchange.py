from __future__ import annotations

from abc import ABC, abstractmethod


class Exchange(ABC):
    @abstractmethod
    async def market_order(
        self,
        symbol: str,
        qty: float,
        current_price: float,
        side: str,
        *,
        reduce_only: bool,
    ) -> str:
        """Creates a market order and returns the order ID."""

    @abstractmethod
    async def limit_order(
        self,
        symbol: str,
        qty: float,
        price: float,
        side: str,
        *,
        reduce_only: bool,
    ) -> str:
        """Creates a limit order and returns the order ID."""

    @abstractmethod
    async def stop_order(
        self,
        symbol: str,
        qty: float,
        price: float,
        side: str,
        *,
        reduce_only: bool,
    ) -> str:
        """Creates a stop order and returns the order id."""

    @abstractmethod
    async def cancel_all_orders(self, symbol: str) -> None:
        """Cancels all orders for the given symbol."""

    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> None:
        """Cancels an order."""

    @abstractmethod
    async def get_balance(self) -> float:
        """Gets the account balance."""

    @abstractmethod
    async def _fetch_precisions(self) -> None:
        """Gets the precisions of orders."""
