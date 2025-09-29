from __future__ import annotations

import os
import time

import arrow
import requests
from loguru import logger

import strategy.utils.helpers as sh
from strategy.modes.import_candles_mode.drivers.base_candles_importer import (
    CandlesImporter,
)


class AlpacaImporter(CandlesImporter):
    """Alpaca candles importer."""

    def __init__(self) -> None:
        super().__init__(name="alpaca", count=10_000, rate_limit_per_second=2)
        self.base_url = "https://data.alpaca.markets/v2"
        self.api_key = os.environ["ALPACA_KEY"]
        self.api_secret = os.environ["ALPACA_SECRET"]
        self.account_id = ""

    def get_starting_time(self, symbol: str) -> int:
        url = f"{self.base_url}/stocks/{symbol}/bars"
        params: dict[str, str | int] = {
            "timeframe": "1Min",
            "limit": 1,
            "start": "1970-01-01T00:00:00Z",
        }
        response = requests.get(
            url,
            headers=self._get_headers(),
            params=params,
            timeout=10,
        )
        self.validate_response(response)
        data = response.json()
        if "bars" in data and len(data["bars"]) > 0:
            return self._convert_iso_to_timestamp(data["bars"][0]["t"])
        raise ValueError(f"No available data for symbol: {symbol}")

    def get_available_symbols(self) -> list[str]:
        url = f"{self.base_url.replace('data', 'api')}/assets"
        response = requests.get(url, headers=self._get_headers(), timeout=10)
        self.validate_response(response)
        data = response.json()
        return [asset["symbol"] for asset in data if asset["tradable"]]

    def _get_headers(self) -> dict[str, str]:
        """Helper method to construct the headers required for Alpaca API requests."""
        return {"APCA-API-KEY-ID": self.api_key, "APCA-API-SECRET-KEY": self.api_secret}

    def fetch(
        self,
        symbol: str,
        start_timestamp: int,
        timeframe: str = "1Min",
    ) -> list[dict[str, float | str]]:
        """Fetch candle data from Alpaca."""
        logger.info(
            f"Getting stock data for {self._convert_timestamp_to_iso(start_timestamp)}",
        )
        url = f"{self.base_url}/stocks/{symbol}/bars"

        old_timeframe = timeframe
        if timeframe.endswith("m"):
            timeframe = timeframe.replace("m", "Min")

        params: dict[str, str | int] = {
            "start": self._convert_timestamp_to_iso(start_timestamp),
            "timeframe": timeframe,
            "limit": self.count,
            "adjustment": "raw",
        }
        response = requests.get(
            url,
            headers=self._get_headers(),
            params=params,
            timeout=10,
        )
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
        raise ValueError(f"Unexpected response format: {data}")

    @staticmethod
    def _convert_timestamp_to_iso(timestamp: int) -> str:
        """Convert a Unix timestamp to an ISO 8601 formatted string."""
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp * 0.001))

    @staticmethod
    def _convert_iso_to_timestamp(iso_time: str) -> int:
        """Convert an ISO 8601 formatted string to a Unix timestamp."""
        return sh.arrow_to_timestamp(arrow.get(iso_time))
