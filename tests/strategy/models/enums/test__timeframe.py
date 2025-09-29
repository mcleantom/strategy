from __future__ import annotations

from strategy.models.enums import ETimeframe


def test_all_enum_values() -> None:
    """Tests enum to minutes."""
    assert ETimeframe.MINUTE_1.to_minutes() == 1
    assert ETimeframe.MINUTE_3.to_minutes() == 3
    assert ETimeframe.MINUTE_5.to_minutes() == 5
    assert ETimeframe.MINUTE_15.to_minutes() == 15
    assert ETimeframe.MINUTE_30.to_minutes() == 30
    assert ETimeframe.MINUTE_45.to_minutes() == 45
    assert ETimeframe.HOUR_1.to_minutes() == 60
    assert ETimeframe.HOUR_2.to_minutes() == 120
    assert ETimeframe.HOUR_3.to_minutes() == 180
    assert ETimeframe.HOUR_4.to_minutes() == 240
    assert ETimeframe.HOUR_6.to_minutes() == 360
    assert ETimeframe.HOUR_8.to_minutes() == 480
    assert ETimeframe.HOUR_12.to_minutes() == 720
    assert ETimeframe.DAY_1.to_minutes() == 60 * 24
    assert ETimeframe.DAY_3.to_minutes() == 4320
    assert ETimeframe.WEEK_1.to_minutes() == 60 * 24 * 7
    assert ETimeframe.MONTH_1.to_minutes() == 43200
