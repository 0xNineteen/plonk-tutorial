"""Lesson 05 — quotient polynomials."""

import pytest

import field as F
import poly
from circuit import N_TRACE_LENGTH
from copy_poly import copy_constraint_poly
from domain import DOMAIN, PLACEMENT_DOMAIN
from gates_poly import check_gates_on_domain, gate_constraint_poly
from layout import NUM_PLACEMENTS
from quotient import (
    check_copy_quotient,
    check_gate_quotient,
    constraint_quotients,
    copy_quotient_poly,
    gate_quotient_poly,
)
from verify import check_witness
from witness import build_witness


# --- vanishing + division ---


def test_vanishing_poly_eval_zero_on_row_domain():
    Z = poly.vanishing_poly(N_TRACE_LENGTH)
    for x in DOMAIN:
        assert poly.eval_poly(Z, x) == 0


def test_vanishing_poly_eval_zero_on_placement_domain():
    Z = poly.vanishing_poly(NUM_PLACEMENTS)
    for x in PLACEMENT_DOMAIN:
        assert poly.eval_poly(Z, x) == 0


def test_vanishing_poly_is_xn_minus_one():
    n = 4
    Z = poly.vanishing_poly(n)
    assert Z[0] == F.mod(-1)
    assert Z[n] == 1
    assert all(c == 0 for c in Z[1:n])
    x = 123
    assert poly.eval_poly(Z, x) == F.sub(pow(x, n, F.p), 1)


def test_div_poly_x_squared_minus_one():
    # (X^2 - 1) / (X - 1) = X + 1
    Q, R = poly.div_poly([F.mod(-1), 0, 1], [F.mod(-1), 1])
    assert R == [0]
    assert Q == [1, 1]
    assert poly.eval_poly(Q, 5) == F.add(1, 5)


def test_div_poly_remainder_when_not_exact():
    # X / (X - 1) has nonzero remainder
    Q, R = poly.div_poly([0, 1], [F.mod(-1), 1])
    assert R != [0]


def test_quotient_by_vanishing_rejects_nonzero_remainder():
    with pytest.raises(ValueError, match="constraint does not vanish on domain"):
        poly.quotient_by_vanishing([0, 1], N_TRACE_LENGTH)


# --- gate quotient ---


def test_gate_quotient_reconstructs_g():
    circuit, _ = build_witness(7, 49)
    G = gate_constraint_poly(circuit)
    Qg = gate_quotient_poly(circuit)
    Z = poly.vanishing_poly(N_TRACE_LENGTH)
    assert poly.eql(poly.mul_poly(Z, Qg), G)


def test_gate_quotient_matches_domain_check():
    circuit, _ = build_witness(7, 49)
    assert check_gates_on_domain(circuit)
    assert check_gate_quotient(circuit)


def test_corrupted_gate_fails_quotient():
    circuit, _ = build_witness(7, 49)
    circuit.trace[0][3] = 50
    assert not check_gates_on_domain(circuit)
    with pytest.raises(ValueError, match="constraint does not vanish on domain"):
        gate_quotient_poly(circuit)


# --- copy quotient ---


def test_copy_quotient_reconstructs_c():
    circuit, _ = build_witness(7, 49)
    C = copy_constraint_poly(circuit)
    Qc = copy_quotient_poly(circuit)
    Z = poly.vanishing_poly(NUM_PLACEMENTS)
    assert poly.eql(poly.mul_poly(Z, Qc), C)


def test_copy_quotient_is_zero_on_valid_witness():
    circuit, _ = build_witness(7, 49)
    C = copy_constraint_poly(circuit)
    assert poly.trim(C) == [0]
    assert poly.trim(copy_quotient_poly(circuit)) == [0]
    assert check_copy_quotient(circuit)


def test_broken_copy_fails_quotient():
    circuit, _ = build_witness(7, 49)
    circuit.trace[0] = [1, 7, 8, 56]
    with pytest.raises(ValueError, match="constraint does not vanish on domain"):
        copy_quotient_poly(circuit)


# --- integration ---


def test_constraint_quotients_keys():
    circuit, _ = build_witness(7, 49)
    quotients = constraint_quotients(circuit)
    assert set(quotients) == {"gate", "copy"}
    assert isinstance(quotients["gate"], list)
    assert isinstance(quotients["copy"], list)


def test_gate_and_copy_quotients_pass_valid_witness():
    circuit, _ = build_witness(7, 49)
    assert check_gate_quotient(circuit)
    assert check_copy_quotient(circuit)


def test_check_witness_quotient_and_domain_equivalent_on_valid():
    circuit, pub = build_witness(7, 49)
    assert check_witness(circuit, [pub], use_quotient=True)
    assert check_witness(circuit, [pub], use_quotient=False)