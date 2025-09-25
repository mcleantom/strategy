import strategy.indicators as ta
from strategy import utils
from strategy.strategy import Order, Strategy


class TrendSwingTrader(Strategy):
    @property
    def adx(self):
        return ta.adx(self.candles) > 25

    @property
    def trend(self):
        e1 = ta.ema(self.candles, 21)
        e2 = ta.ema(self.candles, 50)
        e3 = ta.ema(self.candles, 100)
        if e3 < e2 < e1 < self.price:
            return 1
        elif e3 > e2 > e1 > self.price:
            return -1
        else:
            return 0

    def should_long(self) -> bool:
        return self.trend == 1 and self.adx

    def go_long(self) -> Order:
        entry = self.price
        stop_loss = entry - ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(self.available_margin, 5, entry, stop_loss, fee_rate=0)
        take_profit = self.price + ta.atr(self.candles) * 3
        return Order(quantity=qty, price=entry, stop_loss=stop_loss, take_profit=take_profit)

    def should_short(self) -> bool:
        return self.trend == -1 and self.adx

    def go_short(self):
        entry = self.price
        qty = (self.available_margin / entry) * 0.2
        stop_loss = entry + ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(self.available_margin, 5, entry, stop_loss, fee_rate=0) * 2
        take_profit = self.price - ta.ad(self.candles) * 3
        return Order(quantity=qty, price=entry, stop_loss=stop_loss, take_profit=take_profit)

    def should_cancel_entry(self) -> bool:
        return False
