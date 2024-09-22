from dataclasses import dataclass
from datetime import datetime

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
        self.current_candle = None
        self.stop_loss = None
        self.take_profit = None

    def backtest(self, candles: list[Candle]):
        for candle in candles:
            self.current_candle = candle
            self.strategy.candles.append(candle)

            if self.strategy.should_long() and self.position is None:
                self.enter_long(self.strategy.go_long())
            elif self.strategy.should_short() and self.position is None:
                self.enter_short(self.strategy.go_short())
            elif self.position == "long" and self.strategy.should_cancel_entry():
                self.exit_long(candle)
            elif self.position == "short" and self.strategy.should_cancel_entry():
                self.exit_short(candle)
            if self.exit_position(candle):
                if self.position == "long":
                    self.exit_long(candle)
                elif self.position == "short":
                    self.exit_short(candle)

        if self.position == "long":
            self.exit_long(candles[-1])
        elif self.position == "short":
            self.exit_short(candles[-1])

    def enter_long(self, order: Order) -> None:
        self.position = "long"
        self.entry_price = order.price
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit

    def exit_long(self, candle: Candle) -> None:
        exit_price = candle.close
        trade_pnl = exit_price - self.entry_price
        self.pnl += trade_pnl
        self.trades.append(
            Trade(
                type="long",
                entry_price=self.entry_price,
                exit_price=exit_price,
                pnl=trade_pnl,
                timestamp=sh.timestamp_to_arrow(candle.timestamp).datetime,
            )
        )

    def enter_short(self, order: Order) -> None:
        self.position = "short"
        self.entry_price = order.price
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit

    def exit_short(self, candle: Candle) -> None:
        exit_price = candle.close
        trade_pnl = self.entry_price - exit_price
        self.pnl += trade_pnl
        self.trades.append(
            Trade(
                type="short",
                entry_price=self.entry_price,
                exit_price=exit_price,
                pnl=trade_pnl,
                timestamp=sh.timestamp_to_arrow(candle.timestamp).datetime,
            )
        )

    def exit_position(self, candle: Candle) -> bool:
        should_exit = False
        if self.stop_loss and candle.low <= self.stop_loss:
            should_exit = True
        elif self.take_profit and candle.high >= self.take_profit:
            should_exit = True
        elif self.strategy.should_cancel_entry():
            should_exit = True
        return should_exit
