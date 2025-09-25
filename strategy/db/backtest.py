from __future__ import annotations  # Enable future annotations for forward references

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class EquityCurveModel(Base):
    __tablename__ = "equity_curve"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    backtest_result_id: Mapped[int] = mapped_column(Integer, ForeignKey("backtest_results.id", ondelete="CASCADE"))
    timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    backtest_result: Mapped[BacktestResultModel] = relationship("BacktestResultModel", back_populates="equity_curve")


class BaselineCurveModel(Base):
    __tablename__ = "baseline_curve"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    backtest_result_id: Mapped[int] = mapped_column(Integer, ForeignKey("backtest_results.id", ondelete="CASCADE"))
    timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    backtest_result: Mapped[BacktestResultModel] = relationship("BacktestResultModel", back_populates="baseline_curve")


class PerformanceMetricsModel(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    backtest_result_id: Mapped[int] = mapped_column(Integer, ForeignKey("backtest_results.id", ondelete="CASCADE"))
    pnl: Mapped[float] = mapped_column(Float, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    mdart_sharpe: Mapped[float] = mapped_column(Float, nullable=True)
    calmar_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    omega_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    serenity_index: Mapped[float] = mapped_column(Float, nullable=True)
    average_win_loss: Mapped[float] = mapped_column(Float, nullable=True)
    average_win: Mapped[float] = mapped_column(Float, nullable=True)
    average_loss: Mapped[float] = mapped_column(Float, nullable=True)

    backtest_result: Mapped[BacktestResultModel] = relationship(
        "BacktestResultModel", back_populates="performance_metrics"
    )


class RiskMetricsModel(Base):
    __tablename__ = "risk_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    backtest_result_id: Mapped[int] = mapped_column(Integer, ForeignKey("backtest_results.id", ondelete="CASCADE"))
    total_losing_streak: Mapped[int] = mapped_column(Integer, nullable=False)
    largest_losing_trade: Mapped[float] = mapped_column(Float, nullable=False)
    largest_winning_trade: Mapped[float] = mapped_column(Float, nullable=False)
    total_winning_streak: Mapped[int] = mapped_column(Integer, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False)
    expectancy: Mapped[float] = mapped_column(Float, nullable=False)
    expected_net_profit: Mapped[float] = mapped_column(Float, nullable=False)
    average_holding_period: Mapped[float] = mapped_column(Float, nullable=False)
    gross_profit: Mapped[float] = mapped_column(Float, nullable=False)
    gross_loss: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False)

    backtest_result: Mapped[BacktestResultModel] = relationship("BacktestResultModel", back_populates="risk_metrics")


class TradeMetricsModel(Base):
    __tablename__ = "trade_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    backtest_result_id: Mapped[int] = mapped_column(Integer, ForeignKey("backtest_results.id", ondelete="CASCADE"))
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    total_winning_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    total_losing_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    starting_balance: Mapped[float] = mapped_column(Float, nullable=False)
    finishing_balance: Mapped[float] = mapped_column(Float, nullable=False)
    longs_count: Mapped[int] = mapped_column(Integer, nullable=False)
    longs_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    shorts_count: Mapped[int] = mapped_column(Integer, nullable=False)
    shorts_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, nullable=False)
    total_open_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    open_pl: Mapped[float] = mapped_column(Float, nullable=False)

    backtest_result: Mapped[BacktestResultModel] = relationship("BacktestResultModel", back_populates="trade_metrics")


class BacktestResultModel(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    strategy_name: Mapped[str] = mapped_column(String, nullable=False)
    start_balance: Mapped[float] = mapped_column(Float, nullable=False)
    end_balance: Mapped[float] = mapped_column(Float, nullable=False)
    start_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    date_created: Mapped[DateTime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    equity_curve: Mapped[list[EquityCurveModel]] = relationship(
        EquityCurveModel, back_populates="backtest_result", cascade="all, delete-orphan"
    )
    baseline_curve: Mapped[list[BaselineCurveModel]] = relationship(
        BaselineCurveModel, back_populates="backtest_result", cascade="all, delete-orphan"
    )
    performance_metrics: Mapped[PerformanceMetricsModel] = relationship(
        PerformanceMetricsModel, back_populates="backtest_result", cascade="all, delete-orphan", uselist=False
    )
    risk_metrics: Mapped[RiskMetricsModel] = relationship(
        RiskMetricsModel, back_populates="backtest_result", cascade="all, delete-orphan", uselist=False
    )
    trade_metrics: Mapped[TradeMetricsModel] = relationship(
        TradeMetricsModel, back_populates="backtest_result", cascade="all, delete-orphan", uselist=False
    )
