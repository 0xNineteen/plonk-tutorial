"""Lesson 07 — full prove / verify protocol (toy KZG + Fiat–Shamir)."""

from dataclasses import dataclass

import field as F
import encode
import fiat_shamir
import kzg
import setup
from domain import placement_vanishing_eval, vanishing_eval
from quotient import constraint_bundle
from verify import check_witness

POLY_NAMES = ("s", "a", "b", "c", "qg", "qc", "g", "cp")
COMMIT_KEYS = {
    "s": "C_s",
    "a": "C_a",
    "b": "C_b",
    "c": "C_c",
    "qg": "C_qg",
    "qc": "C_qc",
    "g": "C_g",
    "cp": "C_cp",
}


@dataclass
class Opening:
    y: int
    pi: int


@dataclass
class Proof:
    commitments: dict
    public_inputs: list
    z: int
    openings: dict


def _polynomials(circuit):
    trace = encode.trace_polynomials(circuit)
    bundle = constraint_bundle(circuit)
    return {
        "s": trace["s"],
        "a": trace["a"],
        "b": trace["b"],
        "c": trace["c"],
        "qg": bundle["gate_quotient"],
        "qc": bundle["copy_quotient"],
        "g": bundle["gate"],
        "cp": bundle["copy"],
    }


def prove(circuit, public_inputs, srs) -> Proof:
    """Build a proof that the witness satisfies gates + copies for public_inputs."""
    if not check_witness(circuit, public_inputs):
        raise ValueError("invalid witness")

    commitments = kzg.commit_all(circuit, srs)
    z = fiat_shamir.challenge_z(commitments, public_inputs)

    openings = {}
    for name, coeffs in _polynomials(circuit).items():
        y, pi = setup.prove_open(coeffs, z, srs)
        openings[name] = Opening(y=y, pi=pi)

    return Proof(
        commitments=commitments,
        public_inputs=[F.mod(v) for v in public_inputs],
        z=z,
        openings=openings,
    )


def _gate_eval_from_trace(openings: dict) -> int:
    s = openings["s"].y
    a = openings["a"].y
    b = openings["b"].y
    c = openings["c"].y
    return F.mul(s, F.sub(F.mul(a, b), c))


def verify(proof: Proof, public_inputs, srs) -> bool:
    """Verify a proof against public inputs and the SRS."""
    if proof.public_inputs != [F.mod(v) for v in public_inputs]:
        return False

    z = fiat_shamir.challenge_z(proof.commitments, public_inputs)
    if z != proof.z:
        return False

    if vanishing_eval(z) == 0 or placement_vanishing_eval(z) == 0:
        return False

    for name in POLY_NAMES:
        opening = proof.openings[name]
        commitment = proof.commitments[COMMIT_KEYS[name]]
        if not setup.verify_open(commitment, z, opening.y, opening.pi, srs):
            return False

    qg = proof.openings["qg"].y
    g = proof.openings["g"].y
    qc = proof.openings["qc"].y
    cp = proof.openings["cp"].y

    if F.mul(vanishing_eval(z), qg) != g:
        return False
    if F.mul(placement_vanishing_eval(z), qc) != cp:
        return False
    if g != _gate_eval_from_trace(proof.openings):
        return False

    return True