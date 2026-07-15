"""Fiat–Shamir challenge derivation (toy SHA-256 transcript)."""

import hashlib

import field as F
from domain import DOMAIN, PLACEMENT_DOMAIN

POLY_COMMIT_KEYS = (
    "C_s",
    "C_a",
    "C_b",
    "C_c",
    "C_qg",
    "C_qc",
    "C_g",
    "C_cp",
)


def _transcript_bytes(commitments: dict, public_inputs: list) -> bytes:
    parts = [f"plonk-square-v1"]
    for key in POLY_COMMIT_KEYS:
        parts.append(f"{key}={commitments[key]}")
    for i, value in enumerate(public_inputs):
        parts.append(f"pub{i}={F.mod(value)}")
    return "|".join(parts).encode()


def _z_from_seed(seed: bytes) -> int:
    digest = hashlib.sha256(seed).digest()
    return (int.from_bytes(digest, "big") % (F.p - 1)) + 1


def _outside_domains(z: int) -> bool:
    return z not in DOMAIN and z not in PLACEMENT_DOMAIN


def challenge_z(commitments: dict, public_inputs: list) -> int:
    """Derive evaluation challenge z from commitments + public inputs.

    Re-hash with a counter until z lies outside both row and placement domains.
    """
    base = _transcript_bytes(commitments, public_inputs)
    for attempt in range(256):
        z = _z_from_seed(base + f"|attempt={attempt}".encode())
        if _outside_domains(z):
            return z
    raise RuntimeError("could not sample challenge outside domains")