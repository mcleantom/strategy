from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    from collections.abc import Sequence


class CircularBuffer:
    """Circular buffer."""

    def __init__(self, shape: Sequence[int], drop_at: int | None = None):
        self.index = -1
        self.array = np.zeros(shape)
        self.shape = shape
        self.drop_at = drop_at

    @property
    def bucket_size(self) -> int:
        return int(self.array.shape[0])

    def __str__(self) -> str:
        return str(self.array[: self.index + 1])

    def __len__(self) -> int:
        return self.index + 1

    def __getitem__(self, i: int | slice | str) -> npt.NDArray:
        if isinstance(i, str):
            return self.array[i][: self.index + 1]
        if isinstance(i, slice):
            start, stop, _ = i.indices(self.index + 1)
            return self.array[start:stop]

        if i < 0:
            i = (self.index + 1) - abs(i)
        if self.index == -1 or i > self.index or i < 0:
            raise IndexError(
                f"list assignment index out of range. self.index={self.index}, i={i}",
            )
        return self.array[i]

    def __setitem__(self, i: slice | int, item: npt.ArrayLike) -> None:
        if isinstance(i, slice):
            start = i.start
            stop = i.stop
            step = i.step
            if start is not None and start < 0:
                start = (self.index + 1) - abs(start)
            if stop is None:
                stop = start + len(item)
            if stop < 0:
                stop = (self.index + 1) - abs(stop)
            self.array[slice(start, stop, step)] = item
            return

        if i < 0:
            i = (self.index + 1) - abs(i)

        # validation
        if i > self.index or i < 0:
            raise IndexError("list assignment index out of range")

        self.array[i] = item

    def append(self, item: npt.ArrayLike) -> None:
        self.index += 1

        if self.index != 0 and (self.index + 1) % self.bucket_size == 0:
            self.array = np.concatenate((self.array, np.zeros_like(self.array)), axis=0)

        if (
            self.drop_at is not None
            and self.index != 0
            and (self.index + 1) % self.drop_at == 0
        ):
            shift_num = int(self.drop_at / 2)
            self.index -= shift_num
            self.array = self.np_shift(self.array, -shift_num)

        self.array[self.index] = item

    @staticmethod
    def np_shift(arr: npt.NDArray, num: int, fill_value: int = 0) -> npt.NDArray:
        result = np.empty_like(arr)

        if num > 0:
            result[:num] = fill_value
            result[num:] = arr[:-num]
        elif num < 0:
            result[num:] = fill_value
            result[:num] = arr[-num:]
        else:
            result[:] = arr

        return result
