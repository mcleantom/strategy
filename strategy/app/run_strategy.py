import datetime

from fastapi import APIRouter
from pydantic import BaseModel
from strategy.db.candle import Candle
from strategy.modes.backtest_mode import Backtester, Trade, Equity
from strategy.strategy import Order, Strategy
from strategy.app.deps import SessionDep
from sqlalchemy.future import select
from strategy.strategies.trend_swing_trader_v1 import TrendSwingTrader
from loguru import logger


class ExampleStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.has_bought = False

    def should_long(self) -> bool:
        return not self.has_bought

    def go_long(self) -> Order:
        self.has_bought = True
        return Order(quantity=10, price=self.store.candles.most_recent_candle.close, stop_loss=None, take_profit=None)

    def should_short(self) -> bool:
        return False

    def go_short(self) -> None:
        pass

    def should_cancel_entry(self) -> bool:
        return False


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


@run_strategy_router.post("/backtest")
async def run_strategy(session: SessionDep) -> BacktestResult:
    logger.info(f"Loading candles")
    stmt = select(Candle).where(Candle.symbol == "AAPL").order_by(Candle.timestamp.asc())  #.limit(10_000)
    logger.info(f"Loaded candles")
    result = await session.execute(stmt)
    candles = result.scalars().all()
    strategy = TrendSwingTrader()
    backtester = Backtester(strategy=strategy, initial_balance=10_000)
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
                unix_seconds=candle.timestamp // 1000  # Ensure Unix seconds
            )
        )

    equity_curve = [
        EquityItem(
            value=item.value,
            unix_seconds=int(item.date.timestamp())  # Convert datetime to Unix seconds
        )
        for item in backtester.equity_curve
    ]

    return BacktestResult(
        trades=backtester.trades,
        equity_curve=equity_curve,
        baseline=baseline
    )