"""Lesson 02 — copy constraints, wire IDs, and public input binding."""

import pytest

from circuit import N_TRACE_LENGTH, NUM_DATA_COLS
from layout import (
    NUM_PLACEMENTS,
    WIRE_IDS,
    placement_index,
    row_col_from_placement,
)
from copy_constraints import check_wire_ids, check_public_inputs, value_at_placement
from gates import check_trace
from quotient import check_copy_quotient, check_gate_quotient
from verify import check_witness
from witness import build_witness
import field as F


# --- layout ---


def test_num_placements_matches_trace_grid():
    assert NUM_PLACEMENTS == N_TRACE_LENGTH * NUM_DATA_COLS
    assert len(WIRE_IDS) == NUM_PLACEMENTS


def test_wire_id_table_covers_active_cells():
    assert WIRE_IDS[0] == 0
    assert WIRE_IDS[1] == 0
    assert WIRE_IDS[2] == 1
    assert all(w == -1 for w in WIRE_IDS[3:])


def test_placement_index_round_trip():
    for row in range(N_TRACE_LENGTH):
        for col in (1, 2, 3):
            p = placement_index(row, col)
            assert row_col_from_placement(p) == (row, col)


def test_placement_index_active_row():
    assert placement_index(0, 1) == 0
    assert placement_index(0, 2) == 1
    assert placement_index(0, 3) == 2
    assert placement_index(1, 1) == 3


def test_value_at_placement_reads_data_columns():
    trace, y = build_witness(7, 49)
    assert value_at_placement(trace, 0) == 7
    assert value_at_placement(trace, 1) == 7
    assert value_at_placement(trace, 2) == y


# --- copy checks ---


def test_valid_witness_passes_copy_checks():
    trace, pub = build_witness(7, 49)
    assert check_wire_ids(trace)
    assert check_public_inputs(trace, [pub])
    assert check_witness(trace, [pub])


def test_valid_witness_passes_copy_checks_another_square():
    trace, pub = build_witness(3, 9)
    assert check_wire_ids(trace)
    assert check_public_inputs(trace, [pub])
    assert check_witness(trace, [pub])


def test_gate_ok_but_copy_fails():
    trace, pub = build_witness(7, 49)
    trace.trace[0] = [1, 7, 8, 56]
    assert check_trace(trace)
    assert not check_wire_ids(trace)
    assert not check_witness(trace, [pub])


def test_public_input_mismatch_fails():
    trace, pub = build_witness(7, 49)
    assert pub == F.mod(49)
    assert check_public_inputs(trace, [pub])
    assert not check_public_inputs(trace, [F.mod(50)])
    assert not check_witness(trace, [F.mod(50)])


def test_padding_wire_ids_ignored():
    trace, pub = build_witness(7, 49)
    trace.trace[1] = [0, 123, 456, 789]
    trace.trace[2] = [0, 111, 222, 333]
    assert check_wire_ids(trace)
    assert check_witness(trace, [pub])


def test_check_witness_implies_gate_checks():
    trace, pub = build_witness(7, 49)
    assert check_witness(trace, [pub])
    assert check_trace(trace)

    trace.trace[0][3] = 50
    assert not check_trace(trace)
    assert not check_witness(trace, [pub])


def test_check_witness_implies_quotient_checks():
    trace, pub = build_witness(7, 49)
    assert check_witness(trace, [pub])
    assert check_gate_quotient(trace)
    assert check_copy_quotient(trace)

    trace.trace[0] = [1, 7, 8, 56]
    assert not check_witness(trace, [pub])


def test_corrupted_mul_output_fails_witness_not_just_gates():
    trace, pub = build_witness(7, 49)
    trace.trace[0][3] = 50
    assert not check_trace(trace)
    assert not check_public_inputs(trace, [pub])
    assert not check_witness(trace, [pub])


def test_invalid_witness_still_rejected_at_build():
    with pytest.raises(ValueError, match="invalid witness"):
        build_witness(7, 50)