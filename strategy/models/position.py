from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime


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
