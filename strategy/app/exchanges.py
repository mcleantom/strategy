from enum import Enum

from fastapi import APIRouter

from strategy.modes.import_candles_mode import drivers


class Exchange(str, Enum):
    alpaca = "alpaca"


exchanges_router = APIRouter(tags=["Exchanges"])


@exchanges_router.get("/exchange/{exchange}/symbols")
def get_exchanges_symbols(exchange: Exchange) -> list[str]:
    return drivers[exchange.value]().get_available_symbols()
