import datetime

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
from strategy.db.backtest import BacktestResultModel, EquityCurveModel, BaselineCurveModel, RiskMetricsModel, TradeMetricsModel, PerformanceMetricsModel


backtest_router = APIRouter(tags=["Backtest"])


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


@backtest_router.post("/backtests")
async def run_backtest(session: SessionDep, backtest: BacktestRequest, strategy_to_run: Strategy = Depends(load_strategy)) -> BacktestResult:
    logger.info(f"Loading candles")
    stmt = select(Candle).where(Candle.symbol == "AAPL").order_by(Candle.timestamp.asc()).limit(100_000)
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

    backtest_result = BacktestResultModel(
        strategy_name=strategy.__class__.__name__,
        start_balance=initial_balance,
        end_balance=equity_series.iloc[-1],
        start_time=pd.to_datetime(candles["timestamp"][0]),
        end_time=pd.to_datetime(candles["timestamp"][-1])
    )

    session.add(backtest_result)
    await session.commit()
    await session.refresh(backtest_result, ["id"])

    for equity_item in equity_curve:
        equity_curve_db = EquityCurveModel(
            backtest_result_id=backtest_result.id,
            timestamp=pd.to_datetime(equity_item.unix_seconds, unit='s'),
            value=equity_item.value
        )
        session.add(equity_curve_db)

    for baseline_item in baseline:
        baseline_curve_db = BaselineCurveModel(
            backtest_result_id=backtest_result.id,
            timestamp=pd.to_datetime(baseline_item.unix_seconds, unit='s'),
            value=baseline_item.close
        )
        session.add(baseline_curve_db)

    performance_metrics_db = PerformanceMetricsModel(
        backtest_result_id=backtest_result.id,
        pnl=performance_metrics.pnl,
        win_rate=performance_metrics.win_rate,
        sharpe_ratio=performance_metrics.sharpe_ratio,
        mdart_sharpe=performance_metrics.mdart_sharpe,
        calmar_ratio=performance_metrics.calmar_ratio,
        omega_ratio=performance_metrics.omega_ratio,
        serenity_index=performance_metrics.serenity_index,
        average_win_loss=performance_metrics.average_win_loss,
        average_win=performance_metrics.average_win,
        average_loss=performance_metrics.average_loss
    )
    session.add(performance_metrics_db)

    risk_metrics_db = RiskMetricsModel(
        backtest_result_id=backtest_result.id,
        total_losing_streak=risk_metrics.total_losing_streak,
        largest_losing_trade=risk_metrics.largest_losing_trade,
        largest_winning_trade=risk_metrics.largest_winning_trade,
        total_winning_streak=risk_metrics.total_winning_streak,
        current_streak=risk_metrics.current_streak,
        expectancy=risk_metrics.expectancy,
        expected_net_profit=risk_metrics.expected_net_profit,
        average_holding_period=risk_metrics.average_holding_period,
        gross_profit=risk_metrics.gross_profit,
        gross_loss=risk_metrics.gross_loss,
        max_drawdown=risk_metrics.max_drawdown
    )
    session.add(risk_metrics_db)

    trade_metrics_db = TradeMetricsModel(
        backtest_result_id=backtest_result.id,
        total_trades=trade_metrics.total_trades,
        total_winning_trades=trade_metrics.total_winning_trades,
        total_losing_trades=trade_metrics.total_losing_trades,
        starting_balance=trade_metrics.starting_balance,
        finishing_balance=trade_metrics.finishing_balance,
        longs_count=trade_metrics.longs_count,
        longs_percentage=trade_metrics.longs_percentage,
        shorts_count=trade_metrics.shorts_count,
        shorts_percentage=trade_metrics.shorts_percentage,
        fee=trade_metrics.fee,
        total_open_trades=trade_metrics.total_open_trades,
        open_pl=trade_metrics.open_pl
    )
    session.add(trade_metrics_db)

    await session.commit()

    return BacktestResult(
        trades=backtester.trades,
        equity_curve=equity_curve,
        baseline=baseline,
        performance_metrics=performance_metrics,
        risk_metrics=risk_metrics,
        trade_metrics=trade_metrics
    )


@backtest_router.get("/backtests/{backtest_id}", response_model=BacktestResult)
async def get_backtest_result(
    backtest_id: int,
    session: SessionDep
) -> BacktestResult:
    # Query the backtest result from the database
    stmt = select(BacktestResultModel).where(BacktestResultModel.id == backtest_id)
    result = await session.execute(stmt)
    backtest_result = result.scalars().first()

    # If the backtest result does not exist, return a 404 error
    if not backtest_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest result not found")

    # Query related data (equity curve, baseline, metrics, etc.)
    equity_curve_stmt = select(EquityCurveModel).where(EquityCurveModel.backtest_result_id == backtest_id)
    baseline_curve_stmt = select(BaselineCurveModel).where(BaselineCurveModel.backtest_result_id == backtest_id)
    performance_metrics_stmt = select(PerformanceMetricsModel).where(PerformanceMetricsModel.backtest_result_id == backtest_id)
    risk_metrics_stmt = select(RiskMetricsModel).where(RiskMetricsModel.backtest_result_id == backtest_id)
    trade_metrics_stmt = select(TradeMetricsModel).where(TradeMetricsModel.backtest_result_id == backtest_id)

    # Execute queries
    equity_curve_result = await session.execute(equity_curve_stmt)
    baseline_curve_result = await session.execute(baseline_curve_stmt)
    performance_metrics_result = await session.execute(performance_metrics_stmt)
    risk_metrics_result = await session.execute(risk_metrics_stmt)
    trade_metrics_result = await session.execute(trade_metrics_stmt)

    # Fetch the related data
    equity_curve = [EquityItem(value=item.value, unix_seconds=int(item.timestamp.timestamp())) for item in equity_curve_result.scalars()]
    baseline = [BaselineItem(close=item.value, unix_seconds=int(item.timestamp.timestamp())) for item in baseline_curve_result.scalars()]
    performance_metrics = performance_metrics_result.scalars().first()
    risk_metrics = risk_metrics_result.scalars().first()
    trade_metrics = trade_metrics_result.scalars().first()

    # Build the response object
    backtest_response = BacktestResult(
        trades=[],  # You might want to populate this with the relevant trades from your backtester if needed
        equity_curve=equity_curve,
        baseline=baseline,
        performance_metrics=PerformanceMetrics(
            pnl=performance_metrics.pnl,
            win_rate=performance_metrics.win_rate,
            sharpe_ratio=performance_metrics.sharpe_ratio,
            mdart_sharpe=performance_metrics.mdart_sharpe,
            calmar_ratio=performance_metrics.calmar_ratio,
            omega_ratio=performance_metrics.omega_ratio,
            serenity_index=performance_metrics.serenity_index,
            average_win_loss=performance_metrics.average_win_loss,
            average_win=performance_metrics.average_win,
            average_loss=performance_metrics.average_loss
        ),
        risk_metrics=RiskMetrics(
            total_losing_streak=risk_metrics.total_losing_streak,
            largest_losing_trade=risk_metrics.largest_losing_trade,
            largest_winning_trade=risk_metrics.largest_winning_trade,
            total_winning_streak=risk_metrics.total_winning_streak,
            current_streak=risk_metrics.current_streak,
            expectancy=risk_metrics.expectancy,
            expected_net_profit=risk_metrics.expected_net_profit,
            average_holding_period=risk_metrics.average_holding_period,
            gross_profit=risk_metrics.gross_profit,
            gross_loss=risk_metrics.gross_loss,
            max_drawdown=risk_metrics.max_drawdown
        ),
        trade_metrics=TradeMetrics(
            total_trades=trade_metrics.total_trades,
            total_winning_trades=trade_metrics.total_winning_trades,
            total_losing_trades=trade_metrics.total_losing_trades,
            starting_balance=trade_metrics.starting_balance,
            finishing_balance=trade_metrics.finishing_balance,
            longs_count=trade_metrics.longs_count,
            longs_percentage=trade_metrics.longs_percentage,
            shorts_count=trade_metrics.shorts_count,
            shorts_percentage=trade_metrics.shorts_percentage,
            fee=trade_metrics.fee,
            total_open_trades=trade_metrics.total_open_trades,
            open_pl=trade_metrics.open_pl
        )
    )
    return backtest_response


class ListBacktestIdsResultItem(BaseModel):
    id: int
    strategy_name: str
    date_created: datetime.datetime


@backtest_router.get("/backtests", response_model=list[ListBacktestIdsResultItem])
async def list_backtest_ids(session: SessionDep) -> list[ListBacktestIdsResultItem]:
    stmt = select(
        BacktestResultModel.id,
        BacktestResultModel.strategy_name,
        BacktestResultModel.date_created
    ).order_by(BacktestResultModel.date_created)
    result = await session.execute(stmt)
    backtest_data = result.all()
    backtest_items = [
        ListBacktestIdsResultItem(
            id=row.id,
            strategy_name=row.strategy_name,
            date_created=row.date_created
        ) for row in backtest_data
    ]
    return backtest_items


@backtest_router.delete("/backtests/{backtest_id}")
async def delete_backtest_result(backtest_id: int, session: SessionDep):
    query = select(BacktestResultModel).filter(BacktestResultModel.id == backtest_id)
    result = await session.execute(query)
    backtest = result.scalar_one_or_none()

    if backtest is None:
        raise HTTPException(status_code=404, detail="Backtest result not found")

    await session.delete(backtest)
    await session.commit()
