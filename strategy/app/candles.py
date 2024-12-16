from fastapi import APIRouter
from pydantic import BaseModel
from strategy.db.candle import Candle
from .deps import SessionDep
from sqlalchemy.future import select

candles_router = APIRouter(tags=["Candles"])


class GetCandlesResponseItem(BaseModel):
    exchange: str
    symbol: str


@candles_router.get("/candles", response_model=list[GetCandlesResponseItem])
async def get_candles(session: SessionDep) -> list[GetCandlesResponseItem]:
    statement = select(Candle.exchange, Candle.symbol).distinct()
    result = await session.execute(statement)
    candles_query = result.fetchall()
    return [
        GetCandlesResponseItem(exchange=candle[0], symbol=candle[1])
        for candle in candles_query
    ]
