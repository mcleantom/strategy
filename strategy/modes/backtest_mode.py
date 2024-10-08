from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from tqdm import tqdm

import strategy.helpers as sh
from strategy.db.candle import Candle
from strategy.strategy import Order, Strategy


@dataclass
class Trade:
    type: str
    entry_price: float
    exit_price: float
    pnl: float
    timestamp: datetime


class Backtester:
    def __init__(self, strategy: Strategy, initial_balance: float = 100_000):
        self.strategy = strategy
        self.balance = initial_balance
        self.position = None
        self.entry_price = 0
        self.pnl = 0
        self.trades: list[Trade] = []
        self.stop_loss = None
        self.take_profit = None
        self.daily_returns = []
        self.equity_curve = [initial_balance]
        self.candles = []
        self.last_order: Order | None = None

    def backtest(self, candles: list[Candle]):
        self.candles = candles
        for i, candle in tqdm(enumerate(candles), total=len(candles), desc="Backtesting Candles"):
            self.strategy.store.candles.add_candle(candle)

            if self.strategy.should_long() and self.position is None:
                self.enter_long(self.strategy.go_long())
            elif self.strategy.should_short() and self.position is None:
                self.enter_short(self.strategy.go_short())
            if i == len(candles) - 1 or self.should_exit_position(candle):
                self.exit_position(candle)

            daily_return = (self.balance - self.equity_curve[-1]) / self.equity_curve[-1]
            self.daily_returns.append(daily_return)
            self.equity_curve.append(self.balance)

    def enter_long(self, order: Order) -> None:
        self.position = "long"
        self.entry_price = order.price
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        self.balance -= order.price * order.quantity
        self.last_order = order

    def exit_long(self, candle: Candle) -> None:
        exit_price = candle.close
        trade_pnl = (exit_price - self.entry_price) * self.last_order.quantity
        self.pnl += trade_pnl
        self.balance += trade_pnl
        self.trades.append(
            Trade(
                type="long",
                entry_price=self.entry_price,
                exit_price=exit_price,
                pnl=trade_pnl,
                timestamp=sh.timestamp_to_arrow(candle.timestamp).datetime,
            )
        )
        self.position = None

    def enter_short(self, order: Order) -> None:
        self.position = "short"
        self.entry_price = order.price
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        self.balance += order.price * order.quantity
        self.last_order = order

    def exit_short(self, candle: Candle) -> None:
        exit_price = candle.close
        trade_pnl = (self.entry_price - exit_price) * self.last_order.quantity
        self.pnl += trade_pnl
        self.balance += trade_pnl
        self.trades.append(
            Trade(
                type="short",
                entry_price=self.entry_price,
                exit_price=exit_price,
                pnl=trade_pnl,
                timestamp=sh.timestamp_to_arrow(candle.timestamp).datetime,
            )
        )

    def should_exit_position(self, candle: Candle) -> bool:
        should_exit = False
        if self.stop_loss and candle.low <= self.stop_loss:
            should_exit = True
        elif self.take_profit and candle.high >= self.take_profit:
            should_exit = True
        elif self.strategy.should_cancel_entry():
            should_exit = True
        return should_exit

    def exit_position(self, candle: Candle):
        if self.position == "long":
            self.exit_long(candle)
        elif self.position == "short":
            self.exit_short(candle)

    def generate_report(self):
        import quantstats as qs

        qs.extend_pandas()
        dates = [sh.timestamp_to_arrow(candle.timestamp).datetime for candle in self.candles]
        returns = pd.Series(self.daily_returns, index=pd.to_datetime(dates))
        qs.reports.html(returns, output="backtest_Report.html", title="backtest performance")
        qs.reports.full(returns)
