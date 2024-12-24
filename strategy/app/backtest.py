from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from strategy.db.candle import Candle
from strategy.modes.backtest_mode import Backtester, Trade
from strategy.app.deps import SessionDep
from sqlalchemy.future import select
from strategy.models.enums import ETimeframe
from loguru import logger
import quantstats as qs
import pandas as pd
import importlib.util
import inspect
from strategy.strategy import Strategy
from strategy.app.strategies import STRATEGIES_DIR
from strategy.helpers import to_numpy_array


run_strategy_router = APIRouter(tags=["Strategy"])


def load_strategy(strategy_name: str) -> Strategy:
    strategy_path = (STRATEGIES_DIR / strategy_name).with_suffix(".py")
    if not strategy_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy does not exist")
    spec = importlib.util.spec_from_file_location(strategy_name, strategy_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, Strategy) and obj is not Strategy:
            return obj()

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No valid strategy class found"
    )


class BaselineItem(BaseModel):
    close: float
    unix_seconds: int


class EquityItem(BaseModel):
    value: float
    unix_seconds: int


class PerformanceMetrics(BaseModel):
    pnl: float
    win_rate: float
    sharpe_ratio: float
    mdart_sharpe: float
    calmar_ratio: float
    omega_ratio: float
    serenity_index: float
    average_win_loss: float
    average_win: float
    average_loss: float


class RiskMetrics(BaseModel):
    total_losing_streak: int
    largest_losing_trade: float
    largest_winning_trade: float
    total_winning_streak: int
    current_streak: int
    expectancy: float
    expected_net_profit: float
    average_holding_period: float
    gross_profit: float
    gross_loss: float
    max_drawdown: float


class TradeMetrics(BaseModel):
    total_trades: int
    total_winning_trades: int
    total_losing_trades: int
    starting_balance: float
    finishing_balance: float
    longs_count: int
    longs_percentage: float
    shorts_count: int
    shorts_percentage: float
    fee: float
    total_open_trades: int
    open_pl: float


class BacktestResult(BaseModel):
    trades: list[Trade]
    equity_curve: list[EquityItem]
    baseline: list[BaselineItem]
    performance_metrics: PerformanceMetrics
    risk_metrics: RiskMetrics
    trade_metrics: TradeMetrics


class BacktestRequest(BaseModel):
    timeframe: ETimeframe


@run_strategy_router.post("/backtest")
async def run_strategy(session: SessionDep, backtest: BacktestRequest, strategy_to_run: Strategy = Depends(load_strategy)) -> BacktestResult:
    logger.info(f"Loading candles")
    stmt = select(Candle).where(Candle.symbol == "AAPL").order_by(Candle.timestamp.asc())#.limit(500_000)
    result = await session.execute(stmt)
    candles = result.scalars().all()
    logger.info(f"Loaded candles")
    strategy = strategy_to_run
    initial_balance = 10_000
    backtester = Backtester(strategy=strategy, initial_balance=initial_balance, timeframe=backtest.timeframe)
    candles = to_numpy_array(candles)
    backtester.backtest(candles)
    initial_price = candles["close"][0]

    equity_curve_series = pd.Series(
        [item.value for item in backtester.equity_curve],
        index=pd.to_datetime([item.date for item in backtester.equity_curve])
    ).resample("1D").last().interpolate(method="linear")

    baseline_series = pd.Series(
        candles["close"] * (initial_balance / initial_price),
        index=pd.to_datetime(candles["timestamp"], unit="ms")
    ).resample("1D").last().interpolate(method="linear")

    baseline = [
        BaselineItem(
            close=value,
            unix_seconds=int(timestamp.timestamp())
        )
        for timestamp, value in baseline_series.items()
    ]
    equity_curve = [
        EquityItem(
            value=value,
            unix_seconds=int(timestamp.timestamp())
        )
        for timestamp, value in equity_curve_series.items()
    ]

    equity_series = pd.Series(
        [item.value for item in backtester.equity_curve],
        index=pd.to_datetime([item.date for item in backtester.equity_curve])
    )
    return_series = equity_series.pct_change().dropna()

    average_win = qs.stats.avg_win(equity_series)
    average_loss = qs.stats.avg_loss(equity_series)

    performance_metrics = PerformanceMetrics(
        pnl=equity_series.iloc[-1] - equity_series.iloc[0],
        win_rate=sum(1 for trade in backtester.trades if trade.pnl > 0) / len(backtester.trades),
        sharpe_ratio=qs.stats.sharpe(return_series),
        mdart_sharpe=0,
        calmar_ratio=qs.stats.calmar(return_series),
        omega_ratio=qs.stats.omega(pd.DataFrame(return_series)),
        serenity_index=qs.stats.serenity_index(return_series),
        average_win_loss=average_win / average_loss if average_loss != 0 else 0,
        average_win=average_win,
        average_loss=average_loss
    )

    risk_metrics = RiskMetrics(
        total_losing_streak=0,
        largest_losing_trade=min(trade.pnl for trade in backtester.trades),
        largest_winning_trade=max(trade.pnl for trade in backtester.trades),
        total_winning_streak=0,
        current_streak=0,
        expectancy=0,
        expected_net_profit=0,
        average_holding_period=0,
        gross_profit=sum(trade.pnl for trade in backtester.trades if trade.pnl > 0),
        gross_loss=sum(trade.pnl for trade in backtester.trades if trade.pnl < 0),
        max_drawdown=qs.stats.max_drawdown(equity_series)
    )

    longs_count = sum(1 for trade in backtester.trades if trade.type == "long")
    shorts_count = sum(1 for trade in backtester.trades if trade.type == "short")
    trade_metrics = TradeMetrics(
        total_trades=len(backtester.trades),
        total_winning_trades=sum(1 for trade in backtester.trades if trade.pnl > 0),
        total_losing_trades=sum(1 for trade in backtester.trades if trade.pnl < 0),
        starting_balance=10_000,
        finishing_balance=equity_series.iloc[-1],
        longs_count=longs_count,
        longs_percentage=(longs_count / len(backtester.trades)) * 100,
        shorts_count=shorts_count,
        shorts_percentage=(shorts_count / len(backtester.trades)) * 100,
        fee=0,
        total_open_trades=0,
        open_pl=0
    )

    return BacktestResult(
        trades=backtester.trades,
        equity_curve=equity_curve,
        baseline=baseline,
        performance_metrics=performance_metrics,
        risk_metrics=risk_metrics,
        trade_metrics=trade_metrics
    )
