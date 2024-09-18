import uuid

import arrow


def generate_unique_id():
    return str(uuid.uuid4())


def arrow_to_timestamp(arrow_time: arrow.arrow.Arrow) -> int:
    return arrow_time.int_timestamp * 1000


def timestamp_to_arrow(timestamp: int) -> arrow.arrow.Arrow:
    return arrow.get(timestamp / 1000)


def timestamp_to_time(timestamp: int) -> str:
    return str(arrow.get(timestamp / 1000))


def date_diff_in_days(date1: arrow.arrow.Arrow, date2: arrow.arrow.Arrow) -> int:
    dif = date2 - date1
    return abs(dif.days)


def now_to_timestamp() -> int:
    return arrow.utcnow().int_timestamp * 1000
