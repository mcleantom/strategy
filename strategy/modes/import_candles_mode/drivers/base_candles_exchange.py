from abc import ABC, abstractmethod

import requests


class CandleExchange(ABC):
    def __init__(self, name: str, count: int, rate_limit_per_second: float):
        self.name = name
        self.count = count
        self.sleep_time = 1 / rate_limit_per_second

    @property
    def backup_exchange(self):
        return None

    @abstractmethod
    def fetch(self, symbol: str, start_timestamp: int, timeframe: str) -> list:
        pass

    @abstractmethod
    def get_starting_time(self, symbol: str) -> int:
        pass

    @abstractmethod
    def get_available_symbols(self) -> list:
        pass

    @staticmethod
    def validate_response(response: requests.Response):
        if response.status_code == 502:
            raise ConnectionError("Error: 502 bad gateway, try again later")
        elif response.status_code // 100 == 5:
            raise ConnectionError("ERROR: {} {}".format(response.status_code, response.reason))

        # unsupported inputs
        if response.status_code == 400:
            raise ValueError(response.content)

        # unsupported inputs
        if response.status_code == 404:
            raise ValueError(f"ERROR {response.status_code} {response.reason}. Check the symbol")

        # if the response code is not in the 200-299, raise an exception
        if response.status_code // 100 != 2:
            raise ConnectionError(f"ERROR {response.status_code} {response.reason}")
