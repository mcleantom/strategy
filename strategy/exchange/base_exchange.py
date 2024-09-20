from abc import ABC, abstractmethod


class Exchange(ABC):
    @abstractmethod
    def market_order(self, symbol: str, qty: float, current_price: float, side: str, reduce_only: bool):
        pass

    @abstractmethod
    def limit_order(self, symbol: str, qty: float, price: float, side: str, reduce_only: bool):
        pass

    @abstractmethod
    def stop_order(self, symbol: str, qty: float, price: float, side: str, reduce_only: bool):
        pass

    @abstractmethod
    def cancel_all_orders(self, symbol: str) -> None:
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> None:
        pass

    @abstractmethod
    def _fetch_precisions(self) -> None:
        pass
