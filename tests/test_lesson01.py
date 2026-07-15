"""Lesson 01 — execution trace, wires, and gates."""

import numpy as np
import pytest

from circuit import Circuit, N_TRACE_LENGTH as N
from gates import check_trace, gate_mul
from witness import build_witness
import field as F


def test_valid_square_7_49():
    circuit, y = build_witness(7, 49)
    assert y == F.mod(49)
    assert check_trace(circuit)


def test_valid_square_3_9():
    circuit, y = build_witness(3, 9)
    assert y == F.mod(9)
    assert check_trace(circuit)


def test_invalid_witness_wrong_y():
    with pytest.raises(ValueError, match="invalid witness"):
        build_witness(7, 50)


def test_corrupted_output_fails():
    circuit, _ = build_witness(7, 49)
    circuit.trace[0][3] = 50
    assert not check_trace(circuit)


def test_padding_rows_do_not_matter():
    circuit, _ = build_witness(7, 49)
    # s_mul = 0 on row 1 — gate disabled, garbage should not matter
    circuit.trace[1] = [0, 999_999, 888_888, 777_777]
    assert check_trace(circuit)


def test_trace_shape_and_active_row():
    circuit, y = build_witness(7, 49)
    assert circuit.trace.shape == (N, 4)
    assert circuit.trace[0].tolist() == [1, 7, 7, y]
    # padding rows: selector off
    assert np.all(circuit.trace[1:, 0] == 0)


def test_gate_mul_active_row():
    assert gate_mul(7, 7, 49, 1) == 0


def test_gate_mul_inactive_row():
    # selector 0 → entire gate value is 0 regardless of operands
    assert gate_mul(123, 456, 789, 0) == 0


def test_active_row_wrong_mul_fails():
    circuit = Circuit()
    circuit.set_row(0, 7, 50)  # 7 * 7 != 50
    assert not check_trace(circuit)
