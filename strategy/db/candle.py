from sqlalchemy import UUID, BigInteger, Column, Float, String

from strategy.db import Base


class Candle(Base):
    __tablename__ = "candles"

    id = Column(UUID, primary_key=True)
    timestamp = Column(BigInteger, index=True)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    exchange = Column(String(), index=True)
    symbol = Column(String(), index=True)
    timeframe = Column(String(), index=True)
