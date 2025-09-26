from __future__ import annotations

import numpy as np

import strategy.utils.helpers as sh


def test_slice_candles_sequential_true():
    # Test sequential=True path (no slicing)
    arr = np.zeros(
        500,
        dtype=[
            ("timestamp", "i8"),
            ("open", "f8"),
            ("close", "f8"),
            ("high", "f8"),
            ("low", "f8"),
            ("volume", "f8"),
        ],
    )
    sliced = sh.slice_candles(arr, sequential=True)
    assert len(sliced) == 500  # no slicing when sequential=True
