from strategy.strategy import Strategy, Order
import strategy.indicators as ta
from strategy import utils


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
        stop = entry - ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(self.available_margin, 5, entry, stop, fee_rate=self.fee_rate)
        return Order(
            quantity=qty,
            price=entry
        )

    def should_short(self) -> bool:
        return self.trend == 1 and self.adx

    def go_short(self):
        entry = self.price
        stop = entry + ta.atr(self.candles) * 2
        qty = utils.risk_to_qty(self.available_margin, 5, entry, stop, fee_rate=self.fee_rate) * 2
        return Order(
            quantity=qty,
            price=entry
        )

    def should_cancel_entry(self) -> bool:
        return True
