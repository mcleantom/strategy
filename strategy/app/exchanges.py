from enum import Enum

from fastapi import APIRouter

from strategy.modes.import_candles_mode import CANDLE_DRIVERS


class Exchange(str, Enum):
    alpaca = "alpaca"


exchanges_router = APIRouter(tags=["Exchanges"])


@exchanges_router.get("/exchange/{exchange}/symbols")
def get_exchanges_symbols(exchange: Exchange) -> list[str]:
    driver_ctor = CANDLE_DRIVERS.get(exchange.value)
    if driver_ctor is None:
        return []
    return driver_ctor().get_available_symbols()
