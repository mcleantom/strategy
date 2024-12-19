from unittest import TestCase
from strategy.circular_buffer import CircularBuffer
import numpy as np


class TestCircularBuffer(TestCase):

    def testAppend(self):
        a = CircularBuffer((10, 6))
        a.append(np.arange(6))
        self.assertEquals(a.index, 0)
        self.assertEquals(a[0][0], 0)
        self.assertEquals(a[0][-1], 5)
        a.append(np.arange(5, 11))
        self.assertEquals(a.index, 1)
        self.assertEquals(a[1][0], 5)
        self.assertEquals(a[1][-1], 10)

    def testSizeIncreases(self):
        a = CircularBuffer((3, 6))
        self.assertEquals(a.array.shape, (3, 6))
        a.append(np.arange(1, 7))
        a.append(np.arange(7, 13))
        a.append(np.arange(13, 19))
        self.assertEquals(a.array.shape, (6, 6))
        self.assertEquals(a.index, 2)

        a.append(np.arange(1, 7))
        a.append(np.arange(7, 13))
        a.append(np.arange(13, 19))
        self.assertEquals(a.array.shape, (9, 6))
        self.assertEquals(a.index, 5)

    def test_drop_at(self):
        a = CircularBuffer((100, 5), drop_at=6)
        a.append(np.array([0, 1, 2, 3, 4]))
        a.append(np.array([5, 6, 7, 8, 9]))
        a.append(np.array([10, 11, 12, 13, 14]))
        a.append(np.array([15, 16, 17, 18, 19]))
        a.append(np.array([20, 21, 22, 23, 24]))
        self.assertEquals(a[4][0], 20)
        self.assertEquals(a[0][0], 0)
        # Drops the first half, array is now:
        # [[15, 16, 17, 18, 19],
        #  [20, 21, 22, 23, 24],
        #  [25, 26, 27, 28, 29]]
        a.append(np.array([25, 26, 27, 28, 29]))
        self.assertEquals(a[0][0], 15)
        self.assertEquals(a[2][0], 25)
