import time
from typing import Any, Dict, List, Union

import arrow
import pydash
from sqlalchemy import asc, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from strategy.db import SessionLocal
from strategy.db.candle import Candle
from strategy.helpers import (
    arrow_to_timestamp,
    date_diff_in_days,
    generate_unique_id,
    now_to_timestamp,
    timestamp_to_arrow,
    timestamp_to_time,
)
from strategy.modes.import_candles_mode.drivers.alpaca import AlpacaExchange
from strategy.modes.import_candles_mode.drivers.base_candles_exchange import CandleExchange

drivers: dict[str, type(CandleExchange)] = {"alpaca": AlpacaExchange}


def run(client_id: str, exchange: str, symbol: str, start_date_str: str, mode: str = "candles"):
    today = arrow_to_timestamp(arrow.utcnow().floor("day"))
    start_timestamp = arrow_to_timestamp(arrow.get(start_date_str, "YYYY-MM-DD"))
    if start_timestamp == today or start_timestamp > today:
        raise ValueError("start date must be before today")

    symbol = symbol.upper()

    until_date = arrow.utcnow().floor("day")
    start_date = timestamp_to_arrow(start_timestamp)
    days_count = date_diff_in_days(start_date, until_date)
    candles_count = days_count * 1440
    driver = drivers[exchange]()

    session = SessionLocal()

    for _i in range(candles_count):
        temp_start_timestamp = arrow_to_timestamp(start_date)
        temp_end_timestamp = temp_start_timestamp + (driver.count - 1) * 60_000

        if temp_start_timestamp > now_to_timestamp():
            break

        count = (
            session.query(Candle)
            .filter(
                Candle.exchange == exchange,
                Candle.symbol == symbol,
                or_(Candle.timeframe == "1m", Candle.timeframe.is_(None)),
                Candle.timestamp.between(temp_start_timestamp, temp_end_timestamp),
            )
            .count()
        )
        already_exists = count == driver.count

        if not already_exists:
            if temp_end_timestamp > now_to_timestamp():
                temp_end_timestamp = arrow.utcnow().floor("minute").int_timestamp * 1000 - 60_000

            candles = driver.fetch(symbol, temp_start_timestamp, "1m")

            time_diff = int((candles[0]["timestamp"] - temp_start_timestamp) / 1000) if len(candles) else 0
            if not len(candles) or time_diff < 0 or time_diff > 60 * 100:
                first_existing_timestamp = driver.get_starting_time(symbol)

                if first_existing_timestamp is None:
                    raise ValueError(f"No candles exist for the market for time {first_existing_timestamp}")

                if temp_end_timestamp > first_existing_timestamp:
                    if driver.backup_exchange is not None:
                        candles = _get_candles_from_backup_exchange(
                            exchange, driver.backup_exchange, symbol, temp_start_timestamp, temp_end_timestamp
                        )
                else:
                    run(client_id, exchange, symbol, timestamp_to_time(first_existing_timestamp)[:10], mode)
                    return

            candles = _fill_absent_candles(candles, temp_start_timestamp, temp_end_timestamp)
            store_candles_list(candles)

        start_date = start_date.shift(minutes=driver.count)

        if not already_exists:
            time.sleep(driver.sleep_time)


def _get_candles_from_backup_exchange(
    exchange: str, backup_driver: CandleExchange, symbol: str, start_timestamp: int, end_timestamp: int
) -> list[dict[str, Union[str, Any]]]:
    timeframe = "1m"
    total_candles = []
    session = SessionLocal()
    statement = (
        select(Candle.timestamp, Candle.open, Candle.close, Candle.high, Candle.low, Candle.volume)
        .where(
            Candle.exchange == backup_driver.name,
            Candle.symbol == symbol,
            Candle.timeframe == timeframe,
            Candle.timestamp.between(start_timestamp, end_timestamp),
        )
        .order_by(asc(Candle.timestamp))
    )
    backup_candles = session.execute(statement)
    already_exists = len(backup_candles) == (end_timestamp - start_timestamp) / 60_000 + 1
    if already_exists:
        for c in backup_candles:
            total_candles.append(
                {
                    "id": generate_unique_id(),
                    "exchange": exchange,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": c[0],
                    "open": c[1],
                    "close": c[2],
                    "high": c[3],
                    "low": c[4],
                    "volume": c[5],
                }
            )

        return total_candles

    raise NotImplementedError()


def _fill_absent_candles(
    temp_candles: List[Dict[str, Union[str, Any]]], start_timestamp: int, end_timestamp: int
) -> List[Dict[str, Union[str, Any]]]:
    symbol = temp_candles[0]["symbol"]
    exchange = temp_candles[0]["exchange"]
    candles = []
    first_candle = temp_candles[0]
    started = False
    loop_length = ((end_timestamp - start_timestamp) / 60_000) + 1

    for _ in range(int(loop_length)):
        candle_for_timestamp = pydash.find(temp_candles, lambda c: c["timestamp"] == start_timestamp)

        if candle_for_timestamp is None:
            if started:
                last_close = candles[-1]["close"]
                candles.append(
                    {
                        "id": generate_unique_id(),
                        "exchange": exchange,
                        "symbol": symbol,
                        "timeframe": "1m",
                        "timestamp": start_timestamp,
                        "open": last_close,
                        "high": last_close,
                        "low": last_close,
                        "close": last_close,
                        "volume": 0,
                    }
                )
            else:
                candles.append(
                    {
                        "id": generate_unique_id(),
                        "exchange": exchange,
                        "symbol": symbol,
                        "timeframe": "1m",
                        "timestamp": start_timestamp,
                        "open": first_candle["open"],
                        "high": first_candle["open"],
                        "low": first_candle["open"],
                        "close": first_candle["open"],
                        "volume": 0,
                    }
                )
        else:
            started = True
            candles.append(candle_for_timestamp)

        start_timestamp += 60_000
    return candles


def store_candles_list(candles: list[dict]) -> None:
    for c in candles:
        if "timeframe" not in c:
            raise ValueError("Candle has no timeframe")

    stmt = insert(Candle).values(candles)
    stmt = stmt.on_conflict_do_nothing(index_elements=["exchange", "symbol", "timeframe", "timestamp"])
    db = SessionLocal()
    db.execute(stmt)
    db.commit()


if __name__ == "__main__":
    run(client_id="some_client_id", exchange="alpaca", symbol="AAPL", start_date_str="2023-01-01")
