"""Lesson 03 — polynomials on a domain."""

import field as F
import poly
from circuit import N_TRACE_LENGTH
from domain import DOMAIN, OMEGA, lagrange_basis, vanishing_eval
from encode import trace_column_poly, trace_column_values, trace_polynomials
from gates import check_trace, gate_mul
from gates_poly import (
    check_gates_on_domain,
    eval_gate_constraint_at,
    gate_constraint_poly,
)
from witness import build_witness


# --- domain ---


def test_omega_is_primitive_4th_root():
    assert pow(OMEGA, N_TRACE_LENGTH, F.p) == 1
    assert pow(OMEGA, N_TRACE_LENGTH // 2, F.p) != 1


def test_domain_starts_at_one():
    assert len(DOMAIN) == N_TRACE_LENGTH
    assert DOMAIN[0] == 1
    for i in range(N_TRACE_LENGTH):
        assert DOMAIN[i] == pow(OMEGA, i, F.p)


def test_lagrange_basis_is_one_at_j():
    for j in range(N_TRACE_LENGTH):
        assert lagrange_basis(j, DOMAIN[j]) == 1


def test_lagrange_basis_zero_off_diagonal():
    for j in range(N_TRACE_LENGTH):
        for m in range(N_TRACE_LENGTH):
            if m != j:
                assert lagrange_basis(j, DOMAIN[m]) == 0


def test_vanishing_equals_xn_minus_one():
    x = 12345
    assert vanishing_eval(x) == F.sub(pow(x, N_TRACE_LENGTH, F.p), 1)


def test_vanishing_zero_on_domain():
    for x in DOMAIN:
        assert vanishing_eval(x) == 0


def test_vanishing_nonzero_off_domain():
    assert vanishing_eval(2) != 0


# --- poly / encode ---


def test_interpolate_column_a():
    circuit, _ = build_witness(7, 49)
    ys = trace_column_values(circuit, 1)
    coeffs = poly.interpolate(DOMAIN, ys)
    for i, x in enumerate(DOMAIN):
        assert poly.eval_poly(coeffs, x) == ys[i]


def test_trace_column_values_match_trace():
    circuit, _ = build_witness(7, 49)
    for col in range(4):
        vals = trace_column_values(circuit, col)
        for i in range(N_TRACE_LENGTH):
            assert vals[i] == circuit.cell(i, col)


def test_trace_polynomials_match_trace():
    circuit, _ = build_witness(7, 49)
    polys = trace_polynomials(circuit)
    for col, key in enumerate("sabc"):
        coeffs = polys[key]
        ys = trace_column_values(circuit, col)
        for i, x in enumerate(DOMAIN):
            assert poly.eval_poly(coeffs, x) == ys[i]


# --- gate polynomial ---


def test_check_gates_on_domain_valid_witness():
    circuit, _ = build_witness(7, 49)
    assert check_gates_on_domain(circuit)


def test_check_gates_matches_check_trace():
    circuit, _ = build_witness(7, 49)
    assert check_gates_on_domain(circuit)
    assert check_trace(circuit)

    circuit, _ = build_witness(3, 9)
    assert check_gates_on_domain(circuit)
    assert check_trace(circuit)


def test_gate_constraint_matches_row_gate_mul_on_domain():
    circuit, _ = build_witness(7, 49)
    g = gate_constraint_poly(circuit)
    for i, x in enumerate(DOMAIN):
        row = circuit.trace[i]
        assert eval_gate_constraint_at(circuit, x, g) == gate_mul(
            int(row[1]), int(row[2]), int(row[3]), int(row[0])
        )


def test_gate_constraint_poly_zero_on_domain():
    circuit, _ = build_witness(7, 49)
    g = gate_constraint_poly(circuit)
    assert poly.poly_zero_on_domain(g, DOMAIN)


def test_corrupted_witness_fails_polynomial_gate_check():
    circuit, _ = build_witness(7, 49)
    circuit.trace[0][3] = 50
    assert not check_trace(circuit)
    assert not check_gates_on_domain(circuit)


def test_padding_rows_do_not_break_polynomial_check():
    circuit, _ = build_witness(7, 49)
    circuit.trace[1] = [0, 999_999, 888_888, 777_777]
    circuit.trace[2] = [0, 111, 222, 333]
    assert check_trace(circuit)
    assert check_gates_on_domain(circuit)


def test_trace_column_poly_agrees_with_interpolate():
    circuit, _ = build_witness(7, 49)
    for col in range(4):
        assert trace_column_poly(circuit, col) == poly.interpolate(
            DOMAIN, trace_column_values(circuit, col)
        )