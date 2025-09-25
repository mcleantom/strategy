import numpy as np

from strategy.utils.circular_buffer import CircularBuffer


def test_append():
    a = CircularBuffer((10, 6))
    a.append(np.arange(6))
    assert a.index == 0
    assert a[0][0] == 0
    assert a[0][-1] == 5
    a.append(np.arange(5, 11))
    assert a.index == 1
    assert a[1][0] == 5
    assert a[1][-1] == 10


def test_size_increases():
    a = CircularBuffer((3, 6))
    assert a.array.shape == (3, 6)
    a.append(np.arange(1, 7))
    a.append(np.arange(7, 13))
    a.append(np.arange(13, 19))
    # After 3 appends, buffer should have doubled to 6 rows
    assert a.array.shape == (6, 6)
    assert a.index == 2

    a.append(np.arange(1, 7))
    a.append(np.arange(7, 13))
    a.append(np.arange(13, 19))
    # After 6 total appends, capacity doubled again to 12 rows
    assert a.array.shape == (12, 6)
    assert a.index == 5


def test_drop_at():
    a = CircularBuffer((100, 5), drop_at=6)
    a.append(np.array([0, 1, 2, 3, 4]))
    a.append(np.array([5, 6, 7, 8, 9]))
    a.append(np.array([10, 11, 12, 13, 14]))
    a.append(np.array([15, 16, 17, 18, 19]))
    a.append(np.array([20, 21, 22, 23, 24]))
    assert a[4][0] == 20
    assert a[0][0] == 0
    # Drops the first half, array is now:
    # [[15, 16, 17, 18, 19],
    #  [20, 21, 22, 23, 24],
    #  [25, 26, 27, 28, 29]]
    a.append(np.array([25, 26, 27, 28, 29]))
    assert a[0][0] == 15
    assert a[2][0] == 25


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
    # set middle slice
    buf[2:4] = np.array([99, 100])
    out = buf[1:5]
    assert out.tolist() == [1, 99, 100, 4]


def test_drop_at_shifts_and_preserves_recent_half():
    buf = CircularBuffer((6,), drop_at=4)
    buf.array = np.zeros((6,))
    # After 4 appends, drop_at triggers, shifting left by drop_at/2=2
    for i in range(6):
        buf.append(i + 1)
    # index should have shifted back by 2 during append 4, then continued to 6
    # Ensure latest elements are present at the end
    assert buf[buf.index] == 6
    assert buf[buf.index - 1] == 5
