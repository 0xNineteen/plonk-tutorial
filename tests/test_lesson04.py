"""Lesson 04 — permutation argument and copy polynomials."""

import field as F
import poly
from circuit import N_TRACE_LENGTH
from copy_constraints import check_public_inputs, check_wire_ids, placement_values, value_at_placement
from copy_poly import (
    check_copies_on_domain,
    copy_constraint_poly,
    permuted_witness_poly,
    witness_poly,
)
from domain import DOMAIN, NUM_PLACEMENTS, OMEGA_PL, PLACEMENT_DOMAIN, placement_vanishing_eval
from gates import check_trace
from gates_poly import check_gates_on_domain
from layout import WIRE_IDS
from permutation import SIGMA, build_sigma, permute_values
from quotient import constraint_polys
from verify import check_witness
from witness import build_witness


# --- permutation ---


def test_sigma_is_bijection():
    sigma = build_sigma()
    assert len(sigma) == NUM_PLACEMENTS
    assert sorted(sigma) == list(range(NUM_PLACEMENTS))


def test_sigma_cached_matches_build():
    assert SIGMA == build_sigma()


def test_sigma_cycles_wire_zero():
    assert SIGMA[0] == 1
    assert SIGMA[1] == 0


def test_sigma_fixed_point_wire_one():
    assert SIGMA[2] == 2


def test_sigma_identity_on_padding():
    for p in range(3, NUM_PLACEMENTS):
        assert SIGMA[p] == p


# --- placement domain ---


def test_placement_omega_is_primitive_12th_root():
    assert pow(OMEGA_PL, NUM_PLACEMENTS, F.p) == 1
    assert pow(OMEGA_PL, NUM_PLACEMENTS // 2, F.p) != 1


def test_placement_domain_starts_at_one():
    assert len(PLACEMENT_DOMAIN) == NUM_PLACEMENTS
    assert PLACEMENT_DOMAIN[0] == 1
    for p in range(NUM_PLACEMENTS):
        assert PLACEMENT_DOMAIN[p] == pow(OMEGA_PL, p, F.p)


def test_placement_vanishing_zero_on_domain():
    for x in PLACEMENT_DOMAIN:
        assert placement_vanishing_eval(x) == 0


def test_placement_vanishing_nonzero_off_domain():
    assert placement_vanishing_eval(2) != 0


# --- placement values / witness polynomials ---


def test_placement_values_match_trace():
    circuit, _ = build_witness(7, 49)
    w = placement_values(circuit)
    assert len(w) == NUM_PLACEMENTS
    assert w[0] == 7
    assert w[1] == 7
    assert w[2] == F.mod(49)
    assert all(v == 0 for v in w[3:])


def test_placement_values_use_value_at_placement():
    circuit, _ = build_witness(7, 49)
    w = placement_values(circuit)
    for p, wire_id in enumerate(WIRE_IDS):
        if wire_id >= 0:
            assert w[p] == value_at_placement(circuit, p)


def test_witness_poly_eval_on_placement_domain():
    circuit, _ = build_witness(7, 49)
    w = placement_values(circuit)
    coeffs = witness_poly(circuit)
    for p, x in enumerate(PLACEMENT_DOMAIN):
        assert poly.eval_poly(coeffs, x) == w[p]


def test_permuted_witness_swaps_wire_zero_cells():
    circuit, _ = build_witness(7, 49)
    w = placement_values(circuit)
    w_sigma = permute_values(w, SIGMA)
    assert w_sigma[0] == w[1]
    assert w_sigma[1] == w[0]

    coeffs = permuted_witness_poly(circuit)
    for p, x in enumerate(PLACEMENT_DOMAIN):
        assert poly.eval_poly(coeffs, x) == w_sigma[p]


def test_permuted_witness_matches_witness_on_valid_circuit():
    circuit, _ = build_witness(7, 49)
    W = witness_poly(circuit)
    Ws = permuted_witness_poly(circuit)
    for x in PLACEMENT_DOMAIN:
        assert poly.eval_poly(W, x) == poly.eval_poly(Ws, x)


# --- copy constraint polynomial ---


def test_copy_constraint_zero_on_valid_witness():
    circuit, _ = build_witness(7, 49)
    C = copy_constraint_poly(circuit)
    assert poly.poly_zero_on_domain(C, PLACEMENT_DOMAIN)


def test_check_copies_on_domain_valid_witness():
    circuit, pub = build_witness(7, 49)
    assert check_copies_on_domain(circuit)
    assert check_wire_ids(circuit)
    assert check_public_inputs(circuit, [pub])


def test_copy_check_matches_check_wire_ids():
    for x, y in ((7, 49), (3, 9)):
        circuit, _ = build_witness(x, y)
        assert check_copies_on_domain(circuit) == check_wire_ids(circuit)

    circuit, _ = build_witness(7, 49)
    circuit.trace[0] = [1, 7, 8, 56]
    assert not check_wire_ids(circuit)
    assert not check_copies_on_domain(circuit)


def test_gate_ok_copy_fails_polynomial_check():
    circuit, _ = build_witness(7, 49)
    circuit.trace[0] = [1, 7, 8, 56]
    assert check_trace(circuit)
    assert not check_copies_on_domain(circuit)


def test_gates_and_copies_both_pass_valid_witness():
    circuit, _ = build_witness(7, 49)
    assert check_gates_on_domain(circuit)
    assert check_copies_on_domain(circuit)


def test_check_witness_uses_polynomial_checks():
    circuit, pub = build_witness(7, 49)
    assert check_witness(circuit, [pub])


def test_constraint_polys_returns_gate_and_copy():
    circuit, _ = build_witness(7, 49)
    polys = constraint_polys(circuit)
    assert set(polys) == {"gate", "copy"}
    assert poly.poly_zero_on_domain(polys["gate"], DOMAIN)
    assert poly.poly_zero_on_domain(polys["copy"], PLACEMENT_DOMAIN)