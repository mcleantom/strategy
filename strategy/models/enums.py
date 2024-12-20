from enum import Enum


class ETimeframe(str, Enum):
    MINUTE_1 = "1m"
    MINUTE_3 = "2m"
    MINUTE_5 = "3m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    MINUTE_45 = "45m"
    HOUR_1 = "1h"
    HOUR_2 = "2h"
    HOUR_3 = "3h"
    HOUR_4 = "4h"
    HOUR_6 = "6h"
    HOUR_8 = "8h"
    HOUR_12 = "12h"
    DAY_1 = "1D"
    DAY_3 = "3D"
    WEEK_1 = "1W"
    MONTH_1 = "1M"

    def to_minutes(self) -> int:
        match self:
            case ETimeframe.MINUTE_1:
                return 1
            case ETimeframe.MINUTE_3:
                return 3
            case ETimeframe.MINUTE_5:
                return 5
            case ETimeframe.MINUTE_15:
                return 15
            case ETimeframe.MINUTE_30:
                return 30
            case ETimeframe.MINUTE_45:
                return 45
            case ETimeframe.HOUR_1:
                return 60
            case ETimeframe.HOUR_2:
                return 60 * 2
            case ETimeframe.HOUR_3:
                return 60 * 3
            case ETimeframe.HOUR_4:
                return 60 * 4
            case ETimeframe.HOUR_6:
                return 60 * 6
            case ETimeframe.HOUR_8:
                return 60 * 8
            case ETimeframe.HOUR_12:
                return 60 * 12
            case ETimeframe.DAY_1:
                return 60 * 24
            case ETimeframe.DAY_3:
                return 60 * 24 * 3
            case ETimeframe.WEEK_1:
                return 60 * 24 * 7
            case ETimeframe.MONTH_1:
                return 60 * 24 * 30
