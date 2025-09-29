from __future__ import annotations

import numpy as np
import pytest

from strategy.utils.circular_buffer import CircularBuffer


def test_index_error_out_of_range() -> None:
    buf = CircularBuffer((3,))
    buf.array = np.zeros((3,))
    buf.append(1)
    buf.append(2)
    # index=1, so valid range is [0,1]
    with pytest.raises(IndexError):
        _ = buf[2]
    with pytest.raises(IndexError):
        _ = buf[-3]


def test_setitem_index_error() -> None:
    buf = CircularBuffer((3,))
    buf.array = np.zeros((3,))
    buf.append(1)
    buf.append(2)
    with pytest.raises(IndexError):
        buf[2] = 99


def test_slice_with_negative_start_stop() -> None:
    buf = CircularBuffer((6,))
    buf.array = np.zeros((6,))
    for i in range(4):
        buf.append(i + 1)
    # slice with negative start/stop
    result = buf[1:-1]
    assert result.tolist() == [2, 3]


def test_slice_setitem_negative_indices() -> None:
    buf = CircularBuffer((6,))
    buf.array = np.zeros((6,))
    for i in range(4):
        buf.append(i + 1)
    # set slice with negative indices
    buf[1:-1] = np.array([99, 100])
    assert buf[1] == 99
    assert buf[2] == 100
