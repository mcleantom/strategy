from __future__ import annotations

from datetime import UTC, datetime, timedelta

from strategy.modes.import_candles_mode import run

one_month = timedelta(days=30)
one_year_ago = datetime.now(tz=UTC) - (12 * one_month)

run(
    client_id="strategy",
    exchange="alpaca",
    symbol="AAPL",
    start_date_str=one_year_ago.strftime("%Y-%m-%d"),
)
