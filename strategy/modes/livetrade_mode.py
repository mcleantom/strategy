from dataclasses import dataclass
from datetime import datetime, timezone

from loguru import logger

from strategy.exchange.base_exchange import Exchange
from strategy.strategy import Order, Strategy


@dataclass
class LiveTrade:
    type: str
    entry_price: float
    quantity: float
    entry_timestamp: datetime


class LiveTrader:
    def __init__(self, strategy: Strategy, exchange: Exchange, symbol: str):
        self.strategy = strategy
        self.exchange = exchange
        self.symbol = symbol
        self.position: LiveTrade | None = None
        self.order_id: str | None = None
        self.stop_loss = None
        self.take_profit = None
        self.pnl = 0
        self.trades = []

    def on_candle(self):
        if self.position is None:
            if self.strategy.should_long():
                order = self.strategy.go_long()
                self.enter_position(order, "long", self.strategy.candles[-1])

    def enter_position(self, order: Order, position_type: str, candle):
        current_balance = self.exchange.get_balance()
        required_margin = order.price * order.quantity

        if current_balance < required_margin:
            logger.warning(f"Not enough balance to enter {position_type} position.")
            return

        self.position = LiveTrade(
            type=position_type,
            entry_price=order.price,
            quantity=order.quantity,
            entry_timestamp=datetime.now(tz=timezone.utc),
        )
        self.stop_loss = order.stop_loss
        self.take_profit = order.take_profit
        side = "buy" if position_type == "long" else "sell"
        logger.info(f"Entering {position_type} position: {order.quantity} at {order.price}")
        self.order_id = self.exchange.market_order(
            symbol=self.symbol, qty=order.quantity, current_price=order.price, side=side, reduce_only=False
        )

    def exit_position(self, candle):
        current_price = candle["close"]
        trade_pnl = 0
        if self.position.type == "long":
            trade_pnl = (current_price - self.position.entry_price) * self.position.quantity
        else:
            trade_pnl = (self.position.entry_price - current_price) * self.position.quantity

        self.pnl += trade_pnl
        logger.info(f"Exiting {self.position.type} position at {current_price}, PnL: {trade_pnl}")
        self.exchange.cancel_order(self.symbol, self.order_id)
        self.trades.append(
            {
                "type": self.position.type,
                "entry_price": self.position.entry_price,
                "exit_price": current_price,
                "quantity": self.position.quantity,
                "pnl": trade_pnl,
                "entry_timestamp": self.position.entry_timestamp,
                "exit_timestamp": datetime.now(tz=timezone.utc),
            }
        )
        self.order_id = None
        self.position = None

    def should_exit_position(self, candle):
        """
        Check if we should exit the current position.
        """
        current_price = candle["close"]
        if self.stop_loss and (
            (self.position.type == "long" and current_price <= self.stop_loss)
            or (self.position.type == "short" and current_price >= self.stop_loss)
        ):
            return True
        if self.take_profit and (
            (self.position.type == "long" and current_price >= self.take_profit)
            or (self.position.type == "short" and current_price <= self.take_profit)
        ):
            return True
        if self.strategy.should_cancel_entry():
            return True
        return False
