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


class GetCandlesResponseItem(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float


@candles_router.get("/candles/{exchange}/{symbol}", response_model=list[GetCandlesResponseItem])
async def get_candles(
        exchange: str,
        symbol: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        session: SessionDep
) -> list[GetCandlesResponseItem]:
    statement = (
        select(Candle)
        .where(
            Candle.exchange == exchange,
            Candle.symbol == symbol,
            Candle.timestamp >= int(start_time.timestamp() * 1000),
            Candle.timestamp <= int(end_time.timestamp() * 1000)
        )
        .order_by(Candle.timestamp.asc())
    )
    result = await session.execute(statement)
    candles = result.scalars().all()
    return [
        GetCandlesResponseItem(
            time=int(candle.timestamp / 1000),
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
        )
        for candle in candles
    ]
