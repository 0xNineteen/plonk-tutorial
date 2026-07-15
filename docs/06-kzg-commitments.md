# Lesson 06 — KZG commitments

## What you will learn

Lessons 01–05 built and checked polynomials **explicitly** (coefficients, domain evals, quotients). Real PLONK sends **short commitments** instead of full polynomials.

By the end of this lesson you will:

- Understand **trusted setup** and a secret evaluation point `τ`
- **Commit** to a polynomial `f` with a single field element `C = f(τ)`
- Produce an **opening proof** at point `z`: evaluation `y = f(z)` plus proof `π`
- **Verify** openings without seeing coefficients: `C - y = π · (τ - z)`
- Commit to the polynomials you already built: trace columns and quotients

This lesson uses **toy KZG** (field arithmetic only). Real systems use elliptic-curve pairings; Lesson 07 folds openings into a full prove/verify flow.

Reference: [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) (polynomial commitments / KZG).

---

## Big picture (where this lesson sits)

```
Lesson 01   Trace + gates
Lesson 02   Copy constraints
Lesson 03   Gate polynomial G(X)
Lesson 04   Copy polynomial C(X)
Lesson 05   Quotients Q_G, Q_C
Lesson 06   KZG commitments           ← you are here
Lesson 07   Prove + verify
```

| Lesson | Prover sends | Verifier checks |
|--------|--------------|-----------------|
| 05 | All coeffs of `G`, `C`, `Q_G`, `Q_C` | `Z·Q == F` |
| 06 | Commitments `f(τ)` | Opening equations |
| 07 | Commitments + FS challenges | Full PLONK verify |

---

## Why commitments?

A column polynomial has degree `< N = 4` — small here. Real traces have `N = 2^{20}`.

Sending all coefficients is:

- **Large** — megabytes of proof data
- **Slow** — verifier work scales with degree

A **KZG commitment** is one group element (here: one field element in the toy model) per polynomial. The verifier checks identities using **openings** at random challenge points instead of full polynomials.

---

## Trusted setup (toy version)

KZG needs a secret **τ** (tau) that nobody knows after setup.

**Toy SRS** for polynomials of degree `< D`:

```
τ        — secret (field element)
τ^0 = 1
τ^1
τ^2
...
τ^{D-1}
```

**Commitment** to `f(X) = Σ c_i X^i`:

```
commit(f) = f(τ) = eval_poly(coeffs, τ)
```

In real KZG, `commit(f) = c_0·G + c_1·τG + …` in an elliptic curve group. Evaluating at `τ` is the **same algebra** in the exponent — we skip curves and use `f(τ)` directly.

### Picking `τ` and `D`

Choose `τ` randomly in `𝔽_p` (not in any small domain like `H`).

`D` must exceed max polynomial degree you commit to. For this tutorial:

| Polynomial | Max degree (approx) |
|------------|---------------------|
| Column `S, A, B, C` | `< 4` |
| `Q_G` | `< 8` |
| `Q_C` | `< 12` |

Use `D = 16` or `32` to be safe.

Store setup once:

```python
# setup.py
def trusted_setup(max_degree):
    tau = random_field_element()   # fixed seed OK for tests
    powers = [pow(tau, i, p) for i in range(max_degree)]
    return {"tau": tau, "powers": powers}
```

---

## Opening at a point `z`

Verifier (or Fiat–Shamir in L07) picks challenge `z`. Prover sends:

1. **Evaluation:** `y = f(z)`
2. **Proof:** `π = q(τ)` where

```
q(X) = (f(X) - y) / (X - z)
```

Division is exact when `y = f(z)`.

### Prover algorithm

```python
def prove_open(coeffs, z, tau):
    y = eval_poly(coeffs, z)
    divisor = [F.mod(-z), 1]          # X - z
    dividend = sub_poly(coeffs, [y])  # f(X) - y
    q, r = div_poly(dividend, divisor)
    assert r == [0]                   # y must equal f(z)
    pi = eval_poly(q, tau)
    return y, pi
```

### Verifier algorithm (toy — knows `τ` from SRS)

Given commitment `C = f(τ)`, opening `(z, y, π)`:

```
verify:  C - y == π · (τ - z)   (mod p)
```

Why it works: if `f(X) - y = q(X)(X - z)`, evaluate at `τ`:

```
f(τ) - y = q(τ) · (τ - z)
```

### Real KZG

Production verifiers **do not** know `τ`. Pairings check the same identity in a group where `τ` stays hidden. The toy equation is the algebraic core.

---

## What to commit in our circuit

Minimum set for the square tutorial:

| Polynomial | Source | Commitment |
|------------|--------|------------|
| `A(X)` | `encode.trace_polynomials` | `C_a = A(τ)` |
| `B(X)` | same | `C_b` |
| `C(X)` | same | `C_c` |
| `S(X)` | same | `C_s` |
| `Q_G(X)` | `quotient.gate_quotient_poly` | `C_qg` |
| `Q_C(X)` | `quotient.copy_quotient_poly` | `C_qc` |

Lesson 07 may add blinded openings and Fiat–Shamir challenges. This lesson: commit + single-point open + verify.

---

## Checking constraint identities via openings (preview)

Lesson 05 verified:

```
Z_H(X) · Q_G(X) == G(X)
```

At challenge `z` (not in domain — important for soundness):

```
Z_H(z) · Q_G(z) == G(z)
```

Prover opens `Q_G` and `G` at `z`; verifier combines evaluations. With commitments, verifier checks a relation between `C_qg`, `C_g`, and opened values.

This lesson implements **opening machinery**. Lesson 07 wires challenges and bundles gate + copy + public input.

---

## Data structures to implement

### 1. `setup.py`

```python
MAX_DEGREE = 32

def trusted_setup(max_degree=MAX_DEGREE) -> dict:
    """Return {tau, powers} with powers[i] = τ^i."""

def commit(coeffs, setup) -> int:
    """C = f(τ)."""

def prove_open(coeffs, z, setup) -> tuple[int, int]:
    """Return (y, pi) with y = f(z), pi = q(τ)."""

def verify_open(commitment, z, y, pi, setup) -> bool:
    """Check C - y == pi * (tau - z)."""
```

### 2. `kzg.py` — commit circuit polynomials

```python
def commit_trace_columns(circuit, setup) -> dict
def commit_quotients(circuit, setup) -> dict
def commit_witness_bundle(circuit, setup) -> dict
```

Return maps like `{"a": C_a, "b": C_b, …, "qg": C_qg, "qc": C_qc}`.

### 3. Helper in `poly.py` (optional)

```python
def quotient_by_linear(coeffs, z, y):
    """Return q(X) = (f(X) - y) / (X - z); raise if remainder ≠ 0."""
```

---

## Your task

Implement toy KZG commit + open + verify:

1. **`setup.py`** — `trusted_setup`, `commit`, `prove_open`, `verify_open`
2. **`kzg.py`** — `commit_trace_columns`, `commit_quotients`, `commit_witness_bundle`
3. **Tests** in `tests/test_lesson06.py`

Do **not** implement Fiat–Shamir, full `prove()`, or elliptic curves yet.

### Correctness properties

| Scenario | Expected |
|----------|----------|
| `commit(f)` then `prove_open(f, z)` | `verify_open` → `True` |
| Wrong `y` in verify | `False` |
| `commit` + open for each column on valid witness | all verify |
| `commit` + open for `Q_G`, `Q_C` on valid witness | verify |
| Opening at `z` in domain point for soundness demo | prover can; note why L07 avoids `z ∈ H` |

### Soundness note (read, don’t fully implement)

If `z ∈ H` (row domain), `Z_H(z) = 0` and quotient identity at `z` is trivial. Production PLONK samples `z` outside `H`. For tests, use `z = 2` or `z = 99`.

---

## Run it

```bash
pytest tests/test_lesson01.py … tests/test_lesson05.py -v
pytest tests/test_lesson06.py -v
```

Suggested tests (you write the file):

- `test_commit_eval_matches_eval_poly`
- `test_prove_open_valid`
- `test_prove_open_rejects_wrong_y`
- `test_verify_open_fails_on_tampered_pi`
- `test_commit_trace_columns_valid_witness`
- `test_commit_quotients_valid_witness`
- `test_open_quotient_gate_at_challenge_point`
- `test_z_outside_domain_for_soundness_example`

---

## Checkpoint

Before Lesson 07, you should be able to:

- [ ] Explain why `commit(f) = f(τ)` hides coefficients
- [ ] Write the opening quotient `q(X) = (f(X) - y) / (X - z)`
- [ ] State the verifier equation `C - y = π(τ - z)`
- [ ] List which polynomials this circuit commits
- [ ] Explain why challenge `z` should lie outside `H`

---

## Common mistakes

**Letting verifier pick `τ` after seeing commitments.**  
`τ` must come from trusted setup before proofs.

**Forgetting to subtract `y` before dividing by `(X - z)`.**  
`(f(X) - y) / (X - z)` must be exact.

**Using `z` on the trace domain for “random” challenges.**  
`Z_H(z) = 0` breaks soundness intuition.

**Committing before quotient check passes.**  
Dishonest prover might commit invalid `Q` — Lesson 07 enforces order; here only commit after valid `constraint_bundle`.

**Mixing row and placement degrees for `D`.**  
`Q_C` has higher degree than column polys — size `D` for max degree.

---

## How this connects to the full protocol

| Piece | This lesson | Lesson 07 |
|-------|-------------|-----------|
| Commit | `f(τ)` | same (+ curve form in production) |
| Challenge `z` | fixed in tests | Fiat–Shamir hash |
| Constraint check | manual open | verify pairing / toy equation |
| Public input `y` | separate | bound in transcript |
| Proof object | commitments + openings | full `Proof` struct |

---

## Notation summary

| Symbol | Meaning |
|--------|---------|
| `τ` | Secret setup point |
| `C` | Commitment `f(τ)` |
| `y` | Opening evaluation `f(z)` |
| `π` | Opening proof `q(τ)` |
| `q(X)` | `(f(X) - y) / (X - z)` |
| SRS | `{1, τ, τ², …}` |

---

## Next lesson (preview)

**Lesson 07 — Prove + verify:** Build `prove(circuit, public_inputs)` and `verify(proof, public_inputs)`. Hash transcript for challenge `z`. Check gate and copy constraints via opened quotient identities. Hide private `x`; reveal only commitments and openings.

---

## Further reading

- [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) — KZG and the proof object
- [PLONK paper](https://eprint.iacr.org/2019/953) — polynomial commitments
- [KZG10](https://arxiv.org/abs/1006.0561) — original polynomial commitment paper