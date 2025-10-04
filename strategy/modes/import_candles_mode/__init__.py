from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import arrow
import numpy as np
import numpy.typing as npt
from loguru import logger
from sqlalchemy import asc, or_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.future import select

from strategy.db.base import SessionLocal
from strategy.db.candle import CandleModel
from strategy.modes.import_candles_mode.drivers.alpaca_importer import AlpacaImporter
from strategy.utils.helpers import (
    arrow_to_timestamp,
    date_diff_in_days,
    generate_unique_id,
    now_to_timestamp,
    timestamp_to_arrow,
    timestamp_to_time,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from strategy.models.enums import ETimeframe
    from strategy.modes.import_candles_mode.drivers.base_candles_importer import (
        CandlesImporter,
    )

CANDLE_DRIVERS: dict[str, Callable[[], CandlesImporter]] = {
    "alpaca": lambda: AlpacaImporter(),
}


def run(  # noqa: C901
    client_id: str,
    exchange: str,
    symbol: str,
    start_date_str: str,
    mode: str = "candles",
) -> None:
    today = arrow_to_timestamp(arrow.utcnow().floor("day"))
    start_timestamp = arrow_to_timestamp(arrow.get(start_date_str, "YYYY-MM-DD"))
    if start_timestamp == today or start_timestamp > today:
        raise ValueError("start date must be before today")

    symbol = symbol.upper()

    until_date = arrow.utcnow().floor("day")
    start_date = timestamp_to_arrow(start_timestamp)
    days_count = date_diff_in_days(start_date, until_date)
    candles_count = days_count * 1440
    driver = CANDLE_DRIVERS[exchange]()

    session = SessionLocal()

    for _i in range(candles_count):
        temp_start_timestamp = arrow_to_timestamp(start_date)
        temp_end_timestamp = temp_start_timestamp + (driver.count - 1) * 60_000

        if temp_start_timestamp > now_to_timestamp():
            break

        count = (
            session.query(CandleModel)
            .filter(
                CandleModel.exchange == exchange,
                CandleModel.symbol == symbol,
                or_(CandleModel.timeframe == "1m", CandleModel.timeframe.is_(None)),
                CandleModel.timestamp.between(temp_start_timestamp, temp_end_timestamp),
            )
            .count()
        )
        already_exists = count == driver.count

        if not already_exists:
            if temp_end_timestamp > now_to_timestamp():
                temp_end_timestamp = (
                    arrow.utcnow().floor("minute").int_timestamp * 1000 - 60_000
                )

            candles = driver.fetch(symbol, temp_start_timestamp, "1m")

            time_diff = (
                int((int(candles[0]["timestamp"]) - temp_start_timestamp) / 1000)
                if len(candles)
                else 0
            )
            if not len(candles) or time_diff < 0 or time_diff > 60 * 100:
                first_existing_timestamp = driver.get_starting_time(symbol)

                if first_existing_timestamp is None:
                    raise ValueError(
                        f"No candles exist for the market for time {first_existing_timestamp}",
                    )

                if temp_end_timestamp > first_existing_timestamp:
                    if driver.backup_exchange is not None:
                        candles = _get_candles_from_backup_exchange(
                            exchange,
                            driver.backup_exchange,
                            symbol,
                            temp_start_timestamp,
                            temp_end_timestamp,
                        )
                else:
                    run(
                        client_id,
                        exchange,
                        symbol,
                        timestamp_to_time(first_existing_timestamp)[:10],
                        mode,
                    )
                    return

            candles = _fill_absent_candles(
                candles,
                temp_start_timestamp,
                temp_end_timestamp,
            )
            store_candles_list(candles)

        start_date = start_date.shift(minutes=driver.count)

        if not already_exists:
            time.sleep(driver.sleep_time)


def _get_candles_from_backup_exchange(
    exchange: str,
    backup_driver: CandlesImporter,
    symbol: str,
    start_timestamp: int,
    end_timestamp: int,
) -> list[dict[str, str | Any]]:
    timeframe = "1m"
    total_candles: list[dict[str, str | Any]] = []
    session = SessionLocal()
    statement = (
        select(
            CandleModel.timestamp,
            CandleModel.open,
            CandleModel.close,
            CandleModel.high,
            CandleModel.low,
            CandleModel.volume,
        )
        .where(
            CandleModel.exchange == backup_driver.name,
            CandleModel.symbol == symbol,
            CandleModel.timeframe == timeframe,
            CandleModel.timestamp.between(start_timestamp, end_timestamp),
        )
        .order_by(asc(CandleModel.timestamp))
    )
    backup_candles = session.execute(statement).all()
    already_exists = len(backup_candles) == (end_timestamp - start_timestamp) / 60_000 + 1
    if already_exists:
        total_candles.extend(
            [
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
                for c in backup_candles
            ],
        )
        return total_candles

    raise NotImplementedError


def _fill_absent_candles(
    temp_candles: list[dict[str, str | Any]],
    start_timestamp: int,
    end_timestamp: int,
) -> list[dict[str, str | Any]]:
    logger.info(
        f"Filling absent candles for {temp_candles[0]['symbol']} from {timestamp_to_time(start_timestamp)} "
        f"to {timestamp_to_time(end_timestamp)}",
    )
    ts_to_candle = {int(c["timestamp"]): c for c in temp_candles}
    first_candle = temp_candles[0]
    symbol = first_candle["symbol"]
    exchange = first_candle["exchange"]

    step = 60_000
    last_ts = end_timestamp
    count = ((last_ts - start_timestamp) // step) + 1

    candles: list[dict[str, str | float]] = []
    started = False
    last_close: float | None = None
    first_open = float(first_candle["open"])

    ts = start_timestamp
    for _ in range(count):
        c = ts_to_candle.get(ts)
        if c is None:
            oc = last_close if started and last_close is not None else first_open
            c = {
                "id": generate_unique_id(),
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": "1m",
                "timestamp": ts,
                "open": oc,
                "high": oc,
                "low": oc,
                "close": oc,
                "volume": 0,
            }
        else:
            started = True
        candles.append(c)
        last_close = float(c["close"])
        ts += step

    return candles


def store_candles_list(candles: list[dict[str, float | str]]) -> None:
    logger.info(
        f"Saving candles from {timestamp_to_time(int(candles[0]['timestamp']))} "
        f"to {timestamp_to_time(int(candles[-1]['timestamp']))}",
    )

    stmt = insert(CandleModel).values(candles)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["exchange", "symbol", "timeframe", "timestamp"],
    )
    db = SessionLocal()
    db.execute(stmt)
    db.commit()


type CandleTuple = tuple[float, float, float, float, float, float]


def generate_candles_from_one_minute_candles(
    candles: npt.NDArray,
    timeframe: ETimeframe,
) -> npt.NDArray:
    generated_candles: list[CandleTuple] = []
    num = timeframe.to_minutes()
    for i in range(len(candles)):
        if (i + 1) % num == 0:
            tmp_candles = candles[i - (num - 1) : (i + 1)]
            aggregated_candle: CandleTuple = (
                float(tmp_candles["timestamp"][0]),
                float(tmp_candles["open"][0]),
                float(tmp_candles["close"][-1]),
                float(tmp_candles["high"].max()),
                float(tmp_candles["low"].min()),
                float(tmp_candles["volume"].sum()),
            )
            generated_candles.append(aggregated_candle)
    return np.array(generated_candles, dtype=candles.dtype)


if __name__ == "__main__":
    run(
        client_id="some_client_id",
        exchange="alpaca",
        symbol="AAPL",
        start_date_str="2016-08-01",
    )
