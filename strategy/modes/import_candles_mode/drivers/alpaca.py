import os
import time

import arrow
import requests
from loguru import logger

import strategy.helpers as sh
from strategy.modes.import_candles_mode.drivers.base_candles_exchange import CandleExchange


class AlpacaExchange(CandleExchange):
    def __init__(self):
        super().__init__(name="alpaca", count=10_000, rate_limit_per_second=2)
        self.base_url = "https://data.alpaca.markets/v2"
        self.api_key = os.environ["APCA_API_KEY_ID"]
        self.api_secret = os.environ["APCA_API_SECRET_KEY"]

    def get_starting_time(self, symbol: str) -> int:
        url = f"{self.base_url}/stocks/{symbol}/bars"
        params = {
            "timeframe": "1Min",
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

    def fetch(self, symbol: str, start_timestamp: int, timeframe: str = "1Min") -> list[dict[str, float|str]]:
        """Fetch candle data from Alpaca."""
        logger.info(f"Getting stock data for {self._convert_timestamp_to_iso(start_timestamp)}")
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
        from strategy.db.base import SessionLocal
        from strategy.db.candle import Candle
        from sqlalchemy.dialects.postgresql import insert

        session = SessionLocal()
        session.query(Candle).delete()
        session.commit()
        alpaca = AlpacaExchange()
        candles = alpaca.fetch(symbol="AAPL", start_timestamp=alpaca.get_starting_time("AAPL"), timeframe="1Min")
        total_candles_tmp = 0
        while len(candles) > 1:
            logger.info(f"Saving {len(candles)} stock info starting from {sh.timestamp_to_time(candles[0]['timestamp'])}")
            total_candles_tmp += len(candles)
            statement = insert(Candle).values(candles)
            statement = statement.on_conflict_do_nothing(
                index_elements=["exchange", "symbol", "timeframe", "timestamp"]
            )
            session.execute(statement)
            session.commit()
            total_candles = session.query(Candle).count()
            logger.info(f"Total candles in the database: {total_candles}, expected: {total_candles_tmp}")
            max_timestamp = int(max(c["timestamp"] for c in candles))
            candles = alpaca.fetch(symbol="AAPL", start_timestamp=max_timestamp, timeframe="1Min")

        starting_time = alpaca.get_starting_time(symbol="AAPL")
        available_symbols = alpaca.get_available_symbols()

    main()
