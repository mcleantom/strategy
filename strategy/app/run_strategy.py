import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from strategy.db.candle import Candle
from strategy.modes.backtest_mode import Backtester, Trade, Equity
from strategy.modes.import_candles_mode import generate_candles_from_one_minute_candles
from strategy.strategy import Order, Strategy
from strategy.app.deps import SessionDep
from sqlalchemy.future import select
from strategy.models.enums import ETimeframe
from strategy.strategies.trend_swing_trader_v1 import TrendSwingTrader
from loguru import logger


run_strategy_router = APIRouter(tags=["Strategy"])


class BaselineItem(BaseModel):
    close: float
    unix_seconds: int


class EquityItem(BaseModel):
    value: float
    unix_seconds: int


class BacktestResult(BaseModel):
    trades: list[Trade]
    equity_curve: list[EquityItem]
    baseline: list[BaselineItem]


class BacktestRequest(BaseModel):
    timeframe: ETimeframe


@run_strategy_router.post("/backtest")
async def run_strategy(session: SessionDep, backtest: BacktestRequest) -> BacktestResult:
    logger.info(f"Loading candles")
    stmt = select(Candle).where(Candle.symbol == "AAPL").order_by(Candle.timestamp.asc()).limit(600_000)
    result = await session.execute(stmt)
    candles = result.scalars().all()
    logger.info(f"Loaded candles")
    strategy = TrendSwingTrader()
    backtester = Backtester(strategy=strategy, initial_balance=10_000, timeframe=backtest.timeframe)
    backtester.backtest(candles)
    initial_price = candles[0].close
    initial_balance = 10_000

    asset_amount = initial_balance / initial_price
    baseline = []
    for candle in candles:
        buy_and_hold_equity = asset_amount * candle.close
        baseline.append(
            BaselineItem(
                close=buy_and_hold_equity,
                unix_seconds=candle.timestamp // 1000
            )
        )

    equity_curve = [
        EquityItem(
            value=item.value,
            unix_seconds=int(item.date.timestamp())
        )
        for i, item in enumerate(backtester.equity_curve)
    ]

    return BacktestResult(
        trades=backtester.trades,
        equity_curve=equity_curve,
        baseline=baseline
    )
