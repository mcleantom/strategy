from __future__ import annotations

from datetime import UTC, datetime, timedelta

from strategy.modes.import_candles_mode import run

start_date = datetime.now(tz=UTC) - timedelta(days=365 * 10)

run(
    client_id="strategy",
    exchange="alpaca",
    symbol="AAPL",
    start_date_str=start_date.strftime("%Y-%m-%d"),
)
