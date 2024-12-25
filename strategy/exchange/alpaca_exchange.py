from .base_exchange import Exchange
import os
import requests


class AlpacaExchange(Exchange):

    def __init__(self):
        self.base_url = "https://paper-api.alpaca.markets/v2"
        self.api_key = "PKXVNOY1VHW9APDIWRCG"  # os.environ["APCA_API_KEY_ID"]
        self.api_secret = "cRCaefbUDkeYIhubIAtqt7H2cUXbNifeqPMXhaid"  # os.environ["APCA_API_SECRET_KEY"]
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

    def market_order(self, symbol: str, qty: float, current_price: float, side: str, reduce_only: bool):
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "market",
            "time_in_force": "gtc",
            "reduce_only": reduce_only
        }
        response = requests.post(f"{self.base_url}/orders", json=order_data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def limit_order(self, symbol: str, qty: float, price: float, side: str, reduce_only: bool):
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "limit",
            "limit_price": price,
            "time_in_force": "gtc",
            "reduce_only": reduce_only
        }
        response = requests.post(f"{self.base_url}/orders", json=order_data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def stop_order(self, symbol: str, qty: float, price: float, side: str, reduce_only: bool):
        order_data = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "stop",
            "stop_price": price,
            "time_in_force": "gtc",
            "reduce_only": reduce_only
        }
        response = requests.post(f"{self.base_url}/orders", json=order_data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def cancel_all_orders(self, symbol: str) -> None:
        response = requests.get(f"{self.base_url}/orders", json={"symbols": [symbol]}, headers=self.headers)
        response.raise_for_status()
        orders = response.json()
        for order in orders:
            self.cancel_order(symbol, order["id"])

    def cancel_order(self, symbol: str, order_id: str) -> None:
        response = requests.delete(f"{self.base_url}/orders/{order_id}", headers=self.headers)
        response.raise_for_status()

    def _fetch_precisions(self) -> None:
        response = requests.get(f"{self.base_url}/assets", headers=self.headers)
        response.raise_for_status()
        assets = response.json()
        return assets
