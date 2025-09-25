from dataclasses import dataclass
from datetime import datetime

import numpy as np
import numpy.typing as npt
import pandas as pd
from tqdm import tqdm

import strategy.helpers as sh
from strategy.helpers import to_numpy_array
from strategy.models.enums import ETimeframe
from strategy.modes.import_candles_mode import generate_candles_from_one_minute_candles
from strategy.strategy import Order, Strategy


@dataclass
class Trade:
    type: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    entry_timestamp: datetime
    exit_timestamp: datetime


@dataclass
class Equity:
    value: float
    date: datetime


class Backtester:
    def __init__(
        self, strategy: Strategy, initial_balance: float = 100_000, timeframe: ETimeframe = ETimeframe.MINUTE_1
    ):
        self.strategy = strategy
        self.balance: float = initial_balance
        self.position: str | None = None
        self.entry_price: float = 0.0
        self.pnl: float = 0.0
        self.trades: list[Trade] = []
        self.stop_loss: float | None = None
        self.take_profit: float | None = None
        self.daily_returns: list[float] = []
        self.equity_curve: list[Equity] = []
        self.candles: npt.NDArray | list = []
        self.last_order: Order | None = None
        self.last_timestamp: int | None = None
        self.timeframe = timeframe

    def backtest(self, candles: npt.NDArray):
        # Accept lists of ORM Candle and convert to structured array
        if not isinstance(candles, np.ndarray):
            candles = to_numpy_array(candles)

        candles = generate_candles_from_one_minute_candles(candles, self.timeframe)
        self.candles = candles

        self.equity_curve.append(
            Equity(value=self.balance, date=sh.timestamp_to_arrow(int(candles["timestamp"][0])).datetime)
        )
        # Avoid warmup for small datasets used in unit tests
        warmup_candles = 0 if len(candles) < 300 else 250
        for i in range(warmup_candles):
            self.strategy.store.candles.add_candle(candles[i])

        candles = candles[warmup_candles:]
        progress_bar = tqdm(
            enumerate(candles),
            total=len(candles),
            desc="Backtesting Candles",
        )
        for _, candle in progress_bar:
            self.strategy.store.candles.add_candle(candle)
            self.strategy._available_margin = self.balance
            if self.strategy.should_long() and self.position is None:
                self.enter_long(self.strategy.go_long(), candle)
            elif self.strategy.should_short() and self.position is None:
                short_order = self.strategy.go_short()
                if short_order is not None:
                    self.enter_short(short_order, candle)
            if self.should_exit_position(candle) and self.position is not None:
                self.exit_position(candle)
            if self.balance <= 0:
                raise RuntimeError("Ran out of money")
            prev_equity = self.equity_curve[-1].value
            if prev_equity != 0:
                daily_return = (self.balance - prev_equity) / prev_equity
            else:
                daily_return = 0.0
            self.daily_returns.append(float(daily_return))
            self.equity_curve.append(
                Equity(value=self.balance, date=sh.timestamp_to_arrow(int(candle["timestamp"])).datetime)
            )

            progress_bar.set_postfix({"Balance": f"{self.balance:.2f}", "Trades": len(self.trades)})

        progress_bar.close()

        # Exit any open position at the last candle
        if self.position is not None and len(candles) > 0:
            self.exit_position(candles[-1])

    def enter_long(self, order: Order, candle: npt.NDArray) -> None:
        self.position = "long"
        self.entry_price = float(order.price)
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        # self.balance -= order.price * order.quantity
        self.last_order = order
        self.last_timestamp = int(candle["timestamp"])

    def exit_long(self, candle: npt.NDArray) -> None:
        if self.last_order is None:
            return
        exit_price = float(candle["close"])
        trade_pnl = (exit_price - self.entry_price) * float(self.last_order.quantity)
        self.pnl += trade_pnl
        self.balance += trade_pnl  # exit_price * self.last_order.quantity
        self.trades.append(
            Trade(
                type="long",
                entry_price=self.entry_price,
                exit_price=exit_price,
                quantity=float(self.last_order.quantity),
                pnl=trade_pnl,
                entry_timestamp=(
                    sh.timestamp_to_arrow(int(self.last_timestamp)).datetime
                    if self.last_timestamp
                    else sh.timestamp_to_arrow(int(candle["timestamp"])).datetime
                ),
                exit_timestamp=sh.timestamp_to_arrow(int(candle["timestamp"])).datetime,
            )
        )
        self.position = None

    def enter_short(self, order: Order, candle: npt.NDArray) -> None:
        self.position = "short"
        self.entry_price = float(order.price)
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        # self.balance += order.price * order.quantity
        self.last_order = order
        self.last_timestamp = int(candle["timestamp"])

    def exit_short(self, candle: npt.NDArray) -> None:
        if self.last_order is None:
            return
        exit_price = float(candle["close"])
        trade_pnl = (self.entry_price - exit_price) * float(self.last_order.quantity)
        self.pnl += trade_pnl
        self.balance -= trade_pnl  # exit_price * self.last_order.quantity
        self.trades.append(
            Trade(
                type="short",
                entry_price=self.entry_price,
                exit_price=exit_price,
                quantity=float(self.last_order.quantity),
                pnl=trade_pnl,
                entry_timestamp=(
                    sh.timestamp_to_arrow(int(self.last_timestamp)).datetime
                    if self.last_timestamp
                    else sh.timestamp_to_arrow(int(candle["timestamp"])).datetime
                ),
                exit_timestamp=sh.timestamp_to_arrow(int(candle["timestamp"])).datetime,
            )
        )

    def should_exit_position(self, candle: npt.NDArray) -> bool:
        should_exit = False
        if self.position == "long":
            price = float(candle["close"])
            if self.stop_loss is not None and price <= self.stop_loss:
                should_exit = True
            elif self.take_profit is not None and price >= self.take_profit:
                should_exit = True
        elif self.position == "short":
            price = float(candle["close"])
            if self.stop_loss is not None and price >= self.stop_loss:
                should_exit = True
            elif self.take_profit is not None and price <= self.take_profit:
                should_exit = True
        if self.strategy.should_cancel_entry():
            should_exit = True
        return should_exit

    def exit_position(self, candle: npt.NDArray):
        if self.position == "long":
            self.exit_long(candle)
        elif self.position == "short":
            self.exit_short(candle)
        self.position = None

    def generate_report(self):
        import quantstats as qs

        qs.extend_pandas()
        dates = [sh.timestamp_to_arrow(int(candle["timestamp"])).datetime for candle in self.candles]
        returns = pd.Series(self.daily_returns, index=pd.to_datetime(dates))
        qs.reports.html(returns, output="backtest_Report.html", title="backtest performance")
        qs.reports.full(returns)
