from __future__ import annotations

import numpy as np

from strategy.utils.circular_buffer import CircularBuffer


def test_negative_index_and_bounds():
    buf = CircularBuffer((4,))
    buf.array = np.zeros((4,))
    for i in range(4):
        buf.append(i + 1)
    assert buf[-1] == 4
    assert buf[-2] == 3


def test_slice_set_and_get():
    buf = CircularBuffer((6,))
    buf.array = np.zeros((6,))
    for i in range(6):
        buf.append(i)
    buf[2:4] = np.array([99, 100])
    out = buf[1:5]
    assert out.tolist() == [1, 99, 100, 4]


def test_drop_at_shifts_and_preserves_recent_half():
    buf = CircularBuffer((6,), drop_at=4)
    buf.array = np.zeros((6,))
    for i in range(6):
        buf.append(i + 1)
    assert buf[buf.index] == 6
    assert buf[buf.index - 1] == 5
