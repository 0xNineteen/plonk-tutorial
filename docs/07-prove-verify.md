# Lesson 07 — Prove + verify

## What you will learn

Lessons 01–06 built constraints, quotients, and KZG opening machinery. This lesson wires them into an end-to-end **prove / verify** protocol.

By the end you will:

- Build a **`Proof`** object: commitments, Fiat–Shamir challenge `z`, and KZG openings
- Derive **`z`** from a transcript hash (no interactive verifier)
- Check **gate** and **copy** constraints at `z` via opened quotient identities
- Bind **public inputs** into the transcript
- Keep **private `x`** out of the proof

Still **toy KZG** (field arithmetic, not elliptic curves). Same algebra as production PLONK.

Reference: [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) (proof object and verifier).

---

## Big picture (where this lesson sits)

```
Lesson 01   Trace + gates
Lesson 02   Copy constraints
Lesson 03   Gate polynomial G(X)
Lesson 04   Copy polynomial C(X)
Lesson 05   Quotients Q_G, Q_C
Lesson 06   KZG commitments
Lesson 07   Prove + verify            ← you are here
```

| Lesson | Prover sends | Verifier checks |
|--------|--------------|-----------------|
| 05 | All polynomial coeffs | `Z·Q == F` |
| 06 | Commitments `f(τ)` | Single opening equation |
| 07 | Commitments + openings + FS `z` | Full constraint check at `z` |

---

## Protocol overview

```
Prover                                    Verifier
──────                                    ────────
1. Build witness circuit
2. check_witness (local)
3. Commit polynomials at τ
4. Hash transcript → challenge z
5. Open each poly at z (y, π)
6. Send Proof ──────────────────────────► 7. Recompute z from transcript
                                           8. Verify each KZG opening
                                           9. Check Z_H(z)·Q_G(z) == G(z)
                                          10. Check Z_pl(z)·Q_C(z) == C(z)
                                          11. Cross-check G(z) from trace openings
```

The verifier never sees polynomial coefficients or private `x`.

---

## What gets committed

| Key | Polynomial | Source |
|-----|------------|--------|
| `C_s`, `C_a`, `C_b`, `C_c` | Trace columns | `encode.trace_polynomials` |
| `C_qg`, `C_qc` | Quotients | `quotient.constraint_bundle` |
| `C_g` | Gate constraint `G(X)` | `gates_poly.gate_constraint_poly` |
| `C_cp` | Copy constraint `C(X)` | `copy_poly.copy_constraint_poly` |

`C_cp` avoids clashing with column `C_c`.

---

## Fiat–Shamir challenge

Interactive PLONK: verifier sends random `z` after seeing commitments.

**Fiat–Shamir:** hash the transcript so anyone can recompute `z`:

```
transcript = commitments (sorted keys) || public_inputs
z = SHA256(transcript || attempt) mod p   (retry until z ∉ H and z ∉ H_pl)
```

`z` must lie **outside** both domains:

- Row domain `H` (`N = 4`): if `z ∈ H`, then `Z_H(z) = 0` and the gate identity is trivial
- Placement domain `H_pl` (`12` points): same problem for copy checks

---

## Proof object

```python
@dataclass
class Opening:
    y: int   # f(z)
    pi: int  # q(τ) where q(X) = (f(X) - y) / (X - z)

@dataclass
class Proof:
    commitments: dict   # C_s, C_a, …, C_cp
    public_inputs: list
    z: int
    openings: dict      # s, a, b, c, qg, qc, g, cp → Opening
```

---

## Prover: `prove(circuit, public_inputs, srs)`

1. **`check_witness`** — abort if gates, copies, or public binding fail
2. **`commit_all`** — commitments for trace, quotients, and constraint polys
3. **`challenge_z`** — Fiat–Shamir from commitments + public inputs
4. **`prove_open`** — for each polynomial, compute `(y, π)` at `z`

```python
def prove(circuit, public_inputs, srs) -> Proof:
    if not check_witness(circuit, public_inputs):
        raise ValueError("invalid witness")
    commitments = kzg.commit_all(circuit, srs)
    z = fiat_shamir.challenge_z(commitments, public_inputs)
    # ... open every committed polynomial at z
    return Proof(...)
```

---

## Verifier: `verify(proof, public_inputs, srs)`

1. **Public inputs** — `proof.public_inputs` must match argument
2. **Challenge** — recompute `z`; reject if mismatch or `z` lies on a domain
3. **KZG openings** — for each poly: `C - y == π · (τ - z)`
4. **Gate identity** at `z`:

```
Z_H(z) · Q_G(z) == G(z)
```

5. **Copy identity** at `z`:

```
Z_pl(z) · Q_C(z) == C(z)
```

6. **Cross-check** — recompute `G(z)` from trace openings:

```
G(z) == s(z) · (a(z)·b(z) - c(z))
```

This ties the committed gate polynomial to the committed trace columns.

---

## Module layout

### 1. `fiat_shamir.py`

```python
def challenge_z(commitments, public_inputs) -> int
```

### 2. `kzg.py` (extend)

```python
def commit_constraint_polys(circuit, setup) -> dict
def commit_all(circuit, setup) -> dict
```

### 3. `prove.py`

```python
def prove(circuit, public_inputs, srs) -> Proof
def verify(proof, public_inputs, srs) -> bool
```

---

## Your task

Implement the full protocol:

1. **`fiat_shamir.py`** — `challenge_z`
2. **`kzg.py`** — `commit_constraint_polys`, `commit_all`
3. **`prove.py`** — `prove`, `verify`, `Proof`, `Opening`
4. **Tests** in `tests/test_lesson07.py`

### Correctness properties

| Scenario | Expected |
|----------|----------|
| Valid `x² = y` witness | `prove` then `verify` → `True` |
| Invalid witness | `prove` raises |
| Wrong public input to `verify` | `False` |
| Tampered commitment or opening | `False` |
| Fiat–Shamir | Same transcript → same `z` |
| Privacy | Proof does not contain private `x` |

---

## Run it

```bash
pytest tests/test_lesson01.py … tests/test_lesson06.py -v
pytest tests/test_lesson07.py -v
```

Suggested tests:

- `test_fiat_shamir_deterministic`
- `test_prove_verify_valid_witness`
- `test_prove_fails_invalid_witness`
- `test_verify_rejects_wrong_public_input`
- `test_verify_rejects_tampered_commitment`
- `test_verify_rejects_tampered_opening`
- `test_proof_hides_private_input`

---

## Checkpoint

You should be able to:

- [ ] List what the `Proof` struct contains
- [ ] Explain why `z` is hashed from commitments + public inputs
- [ ] State the gate and copy identities checked at `z`
- [ ] Explain why `z ∉ H` and `z ∉ H_pl` matter
- [ ] Describe what remains hidden vs public in the proof

---

## Common mistakes

**Proving before `check_witness`.**  
Dishonest quotients must not reach the proof path.

**Forgetting constraint commitments `C_g`, `C_cp`.**  
The verifier needs opened `G(z)` and `C(z)` to check quotient identities.

**Letting `z` fall on a domain.**  
`Z(z) = 0` makes quotient checks vacuous.

**Mixing up `C_c` (column) and `C_cp` (copy constraint).**  
Use distinct commitment keys.

**Including private `x` in `public_inputs`.**  
Only `y` is public for this circuit.

---

## How this compares to production PLONK

| Piece | This tutorial | Production |
|-------|---------------|------------|
| KZG | `f(τ)` in `𝔽_p` | `f(τ)·G` on curve |
| Openings | field equation | pairings |
| Challenges | SHA-256 FS | transcript hash (often Poseidon) |
| Copy argument | explicit `C(X)` | grand product + `β, γ` |
| Proof size | 8 commitments + 8 openings | compressed curve points |

The **shape** is the same: commit → challenge → open → verify identities.

---

## Notation summary

| Symbol | Meaning |
|--------|---------|
| `Proof` | Full proof object |
| `z` | Fiat–Shamir evaluation challenge |
| `Z_H(z)` | Row vanishing eval `z^4 - 1` |
| `Z_pl(z)` | Placement vanishing eval `z^12 - 1` |
| `public_inputs` | `[y]` for the square circuit |

---

## Further reading

- [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) — end-to-end protocol
- [PLONK paper](https://eprint.iacr.org/2019/953) — verifier algorithm
- [KZG10](https://arxiv.org/abs/1006.0561) — polynomial commitments