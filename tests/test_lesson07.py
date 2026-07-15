"""Lesson 07 — prove + verify protocol."""

import pytest

import field as F
import fiat_shamir
import prove
import setup
from domain import DOMAIN, PLACEMENT_DOMAIN, placement_vanishing_eval, vanishing_eval
from prove import Opening, Proof
from witness import build_witness


@pytest.fixture
def srs():
    return setup.trusted_setup()


def test_fiat_shamir_deterministic():
    commitments = {key: i + 1 for i, key in enumerate(fiat_shamir.POLY_COMMIT_KEYS)}
    public_inputs = [49]
    z1 = fiat_shamir.challenge_z(commitments, public_inputs)
    z2 = fiat_shamir.challenge_z(commitments, public_inputs)
    assert z1 == z2
    assert vanishing_eval(z1) != 0
    assert placement_vanishing_eval(z1) != 0
    assert z1 not in DOMAIN
    assert z1 not in PLACEMENT_DOMAIN


def test_prove_verify_valid_witness(srs):
    circuit, y = build_witness(7, 49)
    proof = prove.prove(circuit, [y], srs)
    assert prove.verify(proof, [y], srs)


def test_prove_verify_second_valid_square(srs):
    circuit, y = build_witness(3, 9)
    proof = prove.prove(circuit, [y], srs)
    assert prove.verify(proof, [y], srs)


def test_prove_fails_invalid_witness(srs):
    circuit, y = build_witness(7, 49)
    circuit.trace[0][3] = 50
    with pytest.raises(ValueError, match="invalid witness"):
        prove.prove(circuit, [y], srs)


def test_verify_rejects_wrong_public_input(srs):
    circuit, y = build_witness(7, 49)
    proof = prove.prove(circuit, [y], srs)
    assert not prove.verify(proof, [F.add(y, 1)], srs)


def test_verify_rejects_tampered_commitment(srs):
    circuit, y = build_witness(7, 49)
    proof = prove.prove(circuit, [y], srs)
    proof.commitments["C_a"] = F.add(proof.commitments["C_a"], 1)
    assert not prove.verify(proof, [y], srs)


def test_verify_rejects_tampered_opening(srs):
    circuit, y = build_witness(7, 49)
    proof = prove.prove(circuit, [y], srs)
    proof.openings["qg"] = Opening(y=proof.openings["qg"].y, pi=F.add(proof.openings["qg"].pi, 1))
    assert not prove.verify(proof, [y], srs)


def test_verify_rejects_wrong_challenge_z(srs):
    circuit, y = build_witness(7, 49)
    proof = prove.prove(circuit, [y], srs)
    proof.z = F.add(proof.z, 1)
    assert not prove.verify(proof, [y], srs)


def test_verify_rejects_broken_quotient_identity(srs):
    circuit, y = build_witness(7, 49)
    proof = prove.prove(circuit, [y], srs)
    proof.openings["g"] = Opening(y=F.add(proof.openings["g"].y, 1), pi=proof.openings["g"].pi)
    assert not prove.verify(proof, [y], srs)


def test_proof_hides_private_input(srs):
    circuit, y = build_witness(7, 49)
    proof = prove.prove(circuit, [y], srs)

    assert proof.public_inputs == [y]
    assert 7 not in proof.public_inputs
    assert all(7 != opening.y for opening in proof.openings.values())


def test_proof_has_expected_shape(srs):
    circuit, y = build_witness(7, 49)
    proof = prove.prove(circuit, [y], srs)

    assert set(proof.commitments) == set(fiat_shamir.POLY_COMMIT_KEYS)
    assert set(proof.openings) == set(prove.POLY_NAMES)
    for opening in proof.openings.values():
        assert isinstance(opening.y, int)
        assert isinstance(opening.pi, int)


def test_commit_all_includes_constraint_polys(srs):
    circuit, _ = build_witness(7, 49)
    commits = __import__("kzg").commit_all(circuit, srs)
    assert "C_g" in commits
    assert "C_cp" in commits
    assert len(commits) == 8