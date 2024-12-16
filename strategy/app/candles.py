import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from strategy.db.candle import Candle
from .deps import SessionDep
from sqlalchemy.future import select
from strategy.modes.import_candles_mode import run


candles_router = APIRouter(tags=["Candles"])


class GetTickersResponseItem(BaseModel):
    exchange: str
    symbol: str


@candles_router.get("/tickers", response_model=list[GetTickersResponseItem])
async def get_tickers(session: SessionDep) -> list[GetTickersResponseItem]:
    statement = select(Candle.exchange, Candle.symbol).distinct()
    result = await session.execute(statement)
    candles_query = result.fetchall()
    return [
        GetTickersResponseItem(exchange=candle[0], symbol=candle[1])
        for candle in candles_query
    ]


@candles_router.post("/candles/import/{exchange}/{symbol}")
def import_candles(exchange: str, symbol: str, start_date: datetime.date):
    run(
        client_id="strategy",
        exchange=exchange,
        symbol=symbol,
        start_date_str=start_date.strftime("%Y-%m-%d")
    )
