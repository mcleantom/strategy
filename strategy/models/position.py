import datetime
from dataclasses import dataclass
from enum import Enum


class PositionType(str, Enum):
    long = "long"
    short = "short"


@dataclass
class Position:
    exchange_name: str
    symbol: str
    entry_price: float
    exit_price: float
    quantity: float
    opened_at: datetime.datetime
    closed_at: datetime.datetime
    type: PositionType

