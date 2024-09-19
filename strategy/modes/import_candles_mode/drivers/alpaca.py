import os
import time

import arrow
import requests

import strategy.helpers as sh
from strategy.modes.import_candles_mode.drivers.base_candles_exchange import CandleExchange


class AlpacaExchange(CandleExchange):
    def __init__(self):
        super().__init__(name="alpaca", count=1000, rate_limit_per_second=2)
        self.base_url = "https://data.alpaca.markets/v2"
        self.api_key = os.environ["APCA_API_KEY_ID"]
        self.api_secret = os.environ["APCA_API_SECRET_KEY"]

    def get_starting_time(self, symbol: str) -> int:
        url = f"{self.base_url}/stocks/{symbol}/bars"
        params = {
            "timeframe": "1Day",
            "limit": 1,
            "start": "1970-01-01T00:00:00Z",
        }
        response = requests.get(url, headers=self._get_headers(), params=params)
        self.validate_response(response)
        data = response.json()
        if "bars" in data and len(data["bars"]) > 0:
            return self._convert_iso_to_timestamp(data["bars"][0]["t"])
        else:
            raise ValueError(f"No available data for symbol: {symbol}")

    def get_available_symbols(self) -> list:
        url = f'{self.base_url.replace("data", "api")}/assets'
        response = requests.get(url, headers=self._get_headers())
        self.validate_response(response)
        data = response.json()
        return [asset["symbol"] for asset in data if asset["tradable"]]

    def _get_headers(self):
        """Helper method to construct the headers required for Alpaca API requests."""
        return {"APCA-API-KEY-ID": self.api_key, "APCA-API-SECRET-KEY": self.api_secret}

    def fetch(self, symbol: str, start_timestamp: int, timeframe: str = "1Min") -> list:
        """Fetch candle data from Alpaca."""
        url = f"{self.base_url}/stocks/{symbol}/bars"

        old_timeframe = timeframe
        if timeframe.endswith("m"):
            timeframe = timeframe.replace("m", "Min")

        params = {"start": self._convert_timestamp_to_iso(start_timestamp), "timeframe": timeframe, "limit": self.count}
        response = requests.get(url, headers=self._get_headers(), params=params)
        self.validate_response(response)

        data = response.json()
        if "bars" in data:
            return [
                {
                    "id": sh.generate_unique_id(),
                    "timestamp": sh.arrow_to_timestamp(arrow.get(c["t"])),
                    "open": c["o"],
                    "close": c["c"],
                    "high": c["h"],
                    "low": c["l"],
                    "volume": c["v"],
                    "exchange": self.name,
                    "symbol": symbol,
                    "timeframe": old_timeframe,
                }
                for c in data["bars"]
            ]
        else:
            raise ValueError(f"Unexpected response format: {data}")

    @staticmethod
    def _convert_timestamp_to_iso(timestamp: int) -> str:
        """Convert a Unix timestamp to an ISO 8601 formatted string."""
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp * 0.001))

    @staticmethod
    def _convert_iso_to_timestamp(iso_time: str) -> int:
        """Convert an ISO 8601 formatted string to a Unix timestamp."""
        return sh.arrow_to_timestamp(arrow.get(iso_time))


if __name__ == "__main__":

    def main():
        alpaca = AlpacaExchange()
        candles = alpaca.fetch(symbol="AAPL", start_timestamp=1622548800, timeframe="1Min")
        print(candles)
        starting_time = alpaca.get_starting_time(symbol="AAPL")
        print(starting_time)
        available_symbols = alpaca.get_available_symbols()
        print(available_symbols)

    main()
