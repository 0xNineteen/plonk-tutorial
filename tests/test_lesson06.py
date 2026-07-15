"""Lesson 06 — KZG commitments (toy field model)."""

import field as F
import encode
import kzg
import poly
import setup
from domain import DOMAIN, vanishing_eval
from gates_poly import gate_constraint_poly
from quotient import constraint_bundle, gate_quotient_poly
from witness import build_witness

# Challenge outside row domain H (see docs/06-kzg-commitments.md)
Z_OUTSIDE_DOMAIN = 99


# --- setup primitives ---


def test_trusted_setup_powers():
    s = setup.trusted_setup(max_degree=8)
    tau = s["tau"]
    assert len(s["powers"]) == setup.MAX_DEGREE
    assert s["powers"][0] == 1
    for i in range(1, 8):
        assert s["powers"][i] == pow(tau, i, F.p)


def test_commit_eval_matches_eval_poly():
    s = setup.trusted_setup()
    coeffs = [3, 5, 7]  # 3 + 5X + 7X^2
    assert setup.commit(coeffs, s) == poly.eval_poly(coeffs, s["tau"])


def test_prove_open_valid():
    s = setup.trusted_setup()
    coeffs = [1, 2, 3, 4]
    z = Z_OUTSIDE_DOMAIN
    C = setup.commit(coeffs, s)
    y, pi = setup.prove_open(coeffs, z, s)
    assert y == poly.eval_poly(coeffs, z)
    assert setup.verify_open(C, z, y, pi, s)


def test_verify_open_fails_on_wrong_y():
    s = setup.trusted_setup()
    coeffs = [1, 2, 3, 4]
    z = Z_OUTSIDE_DOMAIN
    C = setup.commit(coeffs, s)
    y, pi = setup.prove_open(coeffs, z, s)
    assert not setup.verify_open(C, z, F.add(y, 1), pi, s)


def test_verify_open_fails_on_tampered_pi():
    s = setup.trusted_setup()
    coeffs = [1, 2, 3, 4]
    z = Z_OUTSIDE_DOMAIN
    C = setup.commit(coeffs, s)
    y, pi = setup.prove_open(coeffs, z, s)
    assert not setup.verify_open(C, z, y, F.add(pi, 1), s)


# --- circuit commitments ---


def test_commit_trace_columns_valid_witness():
    circuit, _ = build_witness(7, 49)
    s = setup.trusted_setup()
    commits = kzg.commit_trace_columns(circuit, s)
    polys = encode.trace_polynomials(circuit)

    assert set(commits) == {"C_s", "C_a", "C_b", "C_c"}
    for k, coeffs in polys.items():
        C = commits["C_" + k]
        assert C == setup.commit(coeffs, s)
        y, pi = setup.prove_open(coeffs, Z_OUTSIDE_DOMAIN, s)
        assert setup.verify_open(C, Z_OUTSIDE_DOMAIN, y, pi, s)


def test_commit_quotients_valid_witness():
    circuit, _ = build_witness(7, 49)
    s = setup.trusted_setup()
    commits = kzg.commit_quotients(circuit, s)
    bundle = constraint_bundle(circuit)

    assert set(commits) == {"C_qg", "C_qc"}
    for k, key in [("qg", "gate_quotient"), ("qc", "copy_quotient")]:
        coeffs = bundle[key]
        C = commits["C_" + k]
        assert C == setup.commit(coeffs, s)
        y, pi = setup.prove_open(coeffs, Z_OUTSIDE_DOMAIN, s)
        assert setup.verify_open(C, Z_OUTSIDE_DOMAIN, y, pi, s)


def test_commit_witness_bundle_merges_trace_and_quotients():
    circuit, _ = build_witness(7, 49)
    s = setup.trusted_setup()
    bundle = kzg.commit_witness_bundle(circuit, s)
    trace = kzg.commit_trace_columns(circuit, s)
    quotients = kzg.commit_quotients(circuit, s)

    assert set(bundle) == {"C_s", "C_a", "C_b", "C_c", "C_qg", "C_qc"}
    for k, v in trace.items():
        assert bundle[k] == v
    for k, v in quotients.items():
        assert bundle[k] == v


def test_open_quotient_gate_at_challenge_point():
    """Z_H(z)·Q_G(z) == G(z) at z outside H; opening verifies C - y = π(τ - z)."""
    circuit, _ = build_witness(7, 49)
    s = setup.trusted_setup()
    z = Z_OUTSIDE_DOMAIN

    G = gate_constraint_poly(circuit)
    Qg = gate_quotient_poly(circuit)
    assert vanishing_eval(z) != 0
    assert F.mul(vanishing_eval(z), poly.eval_poly(Qg, z)) == poly.eval_poly(G, z)

    C = setup.commit(Qg, s)
    y, pi = setup.prove_open(Qg, z, s)
    assert y == poly.eval_poly(Qg, z)
    assert setup.verify_open(C, z, y, pi, s)


def test_z_outside_domain_for_soundness_example():
    """z ∈ H makes Z_H(z) = 0, so gate identity at z is trivial — use z ∉ H in production."""
    circuit, _ = build_witness(7, 49)
    s = setup.trusted_setup()
    G = gate_constraint_poly(circuit)
    Qg = gate_quotient_poly(circuit)

    z_in_domain = DOMAIN[1]
    assert vanishing_eval(z_in_domain) == 0
    # LHS is always 0 on H regardless of Q_G
    assert F.mul(vanishing_eval(z_in_domain), poly.eval_poly(Qg, z_in_domain)) == 0
    assert poly.eval_poly(G, z_in_domain) == 0

    # Opening at domain points still works algebraically (not a soundness challenge)
    C = setup.commit(Qg, s)
    y, pi = setup.prove_open(Qg, z_in_domain, s)
    assert setup.verify_open(C, z_in_domain, y, pi, s)

    z_out = Z_OUTSIDE_DOMAIN
    assert vanishing_eval(z_out) != 0
    assert F.mul(vanishing_eval(z_out), poly.eval_poly(Qg, z_out)) == poly.eval_poly(G, z_out)