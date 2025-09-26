from __future__ import annotations

import pytest

from strategy.utils import floor_with_precision, risk_to_qty, risk_to_size, size_to_qty


def test_floor_with_precision():
    assert floor_with_precision(1.2399, 2) == 1.23
    assert floor_with_precision(123.999, 0) == 123.0


def test_size_to_qty_basic():
    assert size_to_qty(100.0, 50.0, precision=3) == 2.0


def test_size_to_qty_with_fee():
    qty = size_to_qty(100.0, 50.0, precision=3, fee_rate=0.001)
    # fee reduces position_size by 0.3%
    assert qty == floor_with_precision((100.0 * (1 - 0.003)) / 50.0, 3)


def test_size_to_qty_invalid_inputs():
    with pytest.raises(TypeError):
        size_to_qty(100.0, float("nan"))
    with pytest.raises(TypeError):
        size_to_qty(float("nan"), 50.0)


def test_risk_to_size_basic():
    # 1% risk on 10_000, risk per qty 0.7, entry 8.6
    result = risk_to_size(10_000, 1, 0.7, 8.6)
    assert result == min(((0.01 * 10_000) / 0.7) * 8.6, 10_000)


def test_risk_to_size_zero_risk_per_qty_raises():
    with pytest.raises(ValueError):
        risk_to_size(10_000, 1, 0.0, 10.0)


def test_risk_to_qty_integration():
    qty = risk_to_qty(
        capital=10_000,
        risk_per_capital=1.0,
        entry_price=10.0,
        stop_loss_price=9.0,
        precision=2,
    )
    # risk per qty = 1, size = ((0.01 * 10000)/1)*10 = 1000 -> qty = 1000/10 = 100
    assert qty == 100.0


def test_risk_to_qty_with_fee():
    qty = risk_to_qty(
        capital=10_000,
        risk_per_capital=1.0,
        entry_price=10.0,
        stop_loss_price=9.0,
        precision=4,
        fee_rate=0.001,
    )
    # fees applied once in risk_to_qty (size *= 1 - 3*fee) and again inside size_to_qty
    expected_size = ((0.01 * 10_000) / 1.0) * 10.0 * (1 - 0.003)
    expected_qty = floor_with_precision((expected_size * (1 - 0.003)) / 10.0, 4)
    assert qty == expected_qty
