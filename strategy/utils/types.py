from __future__ import annotations

import numpy as np
import numpy.typing as npt

type CandleChunk = npt.NDArray[np.void]
CandleDType = np.dtype(
    [
        ("timestamp", "i8"),
        ("open", "f8"),
        ("close", "f8"),
        ("high", "f8"),
        ("low", "f8"),
        ("volume", "f8"),
    ],
)
Candles = np.ndarray[CandleDType]
