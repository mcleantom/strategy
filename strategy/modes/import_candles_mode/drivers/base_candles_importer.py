from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests


class CandlesImporter(ABC):
    """Candles importer."""

    def __init__(self, name: str, count: int, rate_limit_per_second: float):
        self.name = name
        self.count = count
        self.sleep_time = 1 / rate_limit_per_second

    @property
    def backup_exchange(self) -> None | CandlesImporter:
        return None

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        start_timestamp: int,
        timeframe: str,
    ) -> list[dict[str, float | str]]:
        pass

    @abstractmethod
    def get_starting_time(self, symbol: str) -> int:
        pass

    @abstractmethod
    def get_available_symbols(self) -> list[str]:
        pass

    @staticmethod
    def validate_response(response: requests.Response) -> None:
        response.raise_for_status()
