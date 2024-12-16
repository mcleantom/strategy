from enum import Enum
from fastapi import APIRouter
from strategy.modes.import_candles_mode.drivers.alpaca import AlpacaExchange


class Exchange(str, Enum):
    alpaca = "alpaca"


exchanges_router = APIRouter(tags=["Exchanges"])


@exchanges_router.get("/exchange/{exchange}/symbols")
def get_exchanges_symbols(exchange: Exchange) -> list[str]:
    return AlpacaExchange().get_available_symbols()
