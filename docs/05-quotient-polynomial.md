# Lesson 05 — Quotient polynomial

## What you will learn

Lessons 03–04 checked constraints by evaluating polynomials on domains:

```
G(x) = 0  for all x ∈ H          (gates)
C(x) = 0  for all x ∈ H_pl        (copies)
```

This lesson packages those checks as **exact polynomial division**.

By the end you will:

- Use the **vanishing polynomial** `Z_H(X) = X^n - 1` as a divisor
- Prove `F(X) = Z_H(X) · Q(X)` when `F` vanishes on `H`
- Compute **quotient polynomials** `Q_G` and `Q_C` for gate and copy constraints
- Verify quotients by re-multiplying: `Z_H(X) · Q(X) == F(X)`
- See why invalid witnesses leave a **nonzero remainder** (division fails)

Still no KZG or Fiat–Shamir — only polynomial division in `𝔽_p[X]`.

Reference: [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) (quotient / constraint folding).

---

## Big picture (where this lesson sits)

```
Lesson 01   Trace + gates
Lesson 02   Copy constraints
Lesson 03   Gate polynomial G(X) on H
Lesson 04   Copy polynomial C(X) on H_pl
Lesson 05   Quotient polynomials        ← you are here
Lesson 06   KZG commitments
Lesson 07   Prove + verify
```

| Lesson | Verifier question |
|--------|-------------------|
| 03–04 | Does `F(x) = 0` for every domain point? |
| 05 | Does `F(X) = Z_H(X) · Q(X)` as polynomials? |
| 06+ | Does a committed polynomial match that `Q`? |

Lesson 05 is the last **pure algebra** step before cryptography.

---

## From pointwise zeros to division

If `F(x) = 0` for every `x` in a domain `H` of size `n`, and

```
Z_H(X) = ∏_{x ∈ H} (X - x) = X^n - 1
```

(on our multiplicative subgroups), then in `𝔽_p[X]`:

```
Z_H(X)  divides  F(X)
```

So there exists a **quotient polynomial** `Q(X)` with

```
F(X) = Z_H(X) · Q(X)
```

**Degree bound:** if `deg(F) < kn`, then `deg(Q) < (k-1)n` after division by `X^n - 1`.

| Constraint | `F(X)` | Domain size `n` | `Z(X)` |
|------------|--------|-----------------|--------|
| Gates | `G(X)` | `N = 4` | `X^4 - 1` |
| Copies | `C(X)` | `NUM_PLACEMENTS = 12` | `X^12 - 1` |

Two different domains → two different vanishing polynomials.

---

## Vanishing polynomial as coeffs

Low-degree-first representation:

```
X^n - 1  →  coeffs [−1, 0, 0, …, 0, 1]
             c0=-1, cn=1, rest 0
```

In code:

```python
def vanishing_poly(n):
    coeffs = [0] * (n + 1)
    coeffs[0] = F.mod(-1)
    coeffs[n] = 1
    return coeffs
```

Sanity: `eval_poly(vanishing_poly(4), ω^i) == 0` for every `ω^i ∈ DOMAIN`.

---

## Polynomial division (exact)

You need `div_poly(dividend, divisor)` assuming **exact** division (remainder zero).

Standard long division in `𝔽_p[X]`, same as high-school division but with `field.inv` for leading coefficients.

API:

```python
def div_poly(dividend, divisor):
    """Return (quotient, remainder)."""
    # long division; remainder coeffs all zero when exact
```

Wrapper for our use case:

```python
def quotient_by_vanishing(F, n):
    """Return Q where F = (X^n - 1) * Q, or raise if remainder ≠ 0."""
    Z = vanishing_poly(n)
    Q, R = div_poly(F, Z)
    if any(c != 0 for c in R):
        raise ValueError("constraint does not vanish on domain")
    return trim(Q)
```

**Why raise on remainder?** A cheating witness may satisfy some but not all point checks, or numerical bugs may leave a nonzero remainder — the prover must not produce a quotient in that case.

---

## Gate quotient `Q_G`

From Lesson 03:

```
G(X) = S(X) · (A(X)·B(X) - C(X))
```

Row domain `H`, `|H| = N = 4`.

```
Q_G(X) = G(X) / (X^N - 1)
```

On honest witnesses, `G` vanishes on `H`, so division is exact.

**Verify:**

```python
Z = vanishing_poly(N)
assert mul_poly(Z, Q_G) == trim(G)   # coefficient-wise equality
```

---

## Copy quotient `Q_C`

From Lesson 04:

```
C(X) = W(X) - W^σ(X)
```

Placement domain `H_pl`, `|H_pl| = 12`.

```
Q_C(X) = C(X) / (X^12 - 1)
```

### Honest witness often gives `C(X) = 0`

For valid `x² = y`, copies hold, so `w[p] = w[σ(p)]` everywhere. Then `W = W^σ` as polynomials on 12 points, and

```
C(X) = 0   (the zero polynomial)
Q_C(X) = 0
```

That is correct — the copy constraint polynomial is **identically zero**, and the quotient is zero too.

### Broken copies → division fails

If `a ≠ b` but the gate still passes, `C` is nonzero on `H_pl` but may not vanish on **all** 12 points (it will fail at placements `0` and `1`). Then `C` is not divisible by `X^12 - 1`, and `quotient_by_vanishing` should raise.

---

## Module layout

### 1. Extend `poly.py`

Add:

| Function | Purpose |
|----------|---------|
| `vanishing_poly(n)` | Coeffs of `X^n - 1` |
| `div_poly(dividend, divisor)` | Long division → `(Q, R)` |
| `quotient_by_vanishing(F, n)` | Exact quotient by `X^n - 1` |

Keep using `trim` on results.

### 2. New `quotient.py`

```python
from circuit import N_TRACE_LENGTH
from layout import NUM_PLACEMENTS
from gates_poly import gate_constraint_poly
from copy_poly import copy_constraint_poly
import poly

def gate_quotient_poly(circuit):
    G = gate_constraint_poly(circuit)
    return poly.quotient_by_vanishing(G, N_TRACE_LENGTH)

def copy_quotient_poly(circuit):
    C = copy_constraint_poly(circuit)
    return poly.quotient_by_vanishing(C, NUM_PLACEMENTS)

def check_gate_quotient(circuit) -> bool:
    """Z_H · Q_G == G"""

def check_copy_quotient(circuit) -> bool:
    """Z_{H_pl} · Q_C == C"""

def constraint_quotients(circuit) -> dict:
    return {"gate": ..., "copy": ...}
```

### 3. Update `verify.py` (optional)

Add quotient checks alongside domain checks, or replace domain loops with quotient identity checks (they are equivalent when division succeeds):

```python
def check_witness(circuit, public_inputs):
    return (
        check_gate_quotient(circuit)
        and check_copy_quotient(circuit)
        and check_public_inputs(circuit, public_inputs)
    )
```

Domain checks and quotient checks should agree on honest witnesses — keep both during development if helpful.

---

## Long division sketch

Divide `F` by `D` (monic or scale leading coeff):

```
deg(F) ≥ deg(D)
lead(F) / lead(D) → term t
F := F - t * D  (aligned at same degree)
repeat until deg(F) < deg(D)  → remainder
```

All ops mod `p`. If remainder is identically zero, quotient is exact.

At tutorial sizes (`n = 4`, `12`), naive long division is fast enough.

---

## Your task

Implement quotient computation and verification:

1. **`poly.py`** — `vanishing_poly`, `div_poly`, `quotient_by_vanishing`
2. **`quotient.py`** — `gate_quotient_poly`, `copy_quotient_poly`, `check_gate_quotient`, `check_copy_quotient`, `constraint_quotients`
3. **Tests** in `tests/test_lesson05.py`

Do **not** implement KZG yet.

### Correctness properties

| Scenario | Expected |
|----------|----------|
| `vanishing_poly(4)` evaluates to `0` on `DOMAIN` | `True` |
| `vanishing_poly(12)` evaluates to `0` on `PLACEMENT_DOMAIN` | `True` |
| Valid `x=7, y=49` | `gate_quotient` succeeds; `Z·Q_G == G` |
| Valid witness | `copy_quotient` succeeds; `Z_pl·Q_C == C` (often `Q_C = [0]`) |
| `quotient_by_vanishing(G, 4)` after corrupting `c[0]` | raises or remainder ≠ 0 |
| Broken copy `a≠b` | `copy_quotient` raises |
| `check_gate_quotient` equivalent to `check_gates_on_domain` on valid witness | both `True` |

### Suggested extra test

```python
Z = poly.vanishing_poly(4)
Q = gate_quotient_poly(circuit)
G = gate_constraint_poly(circuit)
assert poly.mul_poly(Z, Q) == poly.trim(G)
```

---

## Run it

```bash
pytest tests/test_lesson01.py tests/test_lesson02.py tests/test_lesson03.py tests/test_lesson04.py -v
pytest tests/test_lesson05.py -v
```

Suggested tests (you write the file):

- `test_vanishing_poly_eval_zero_on_row_domain`
- `test_vanishing_poly_eval_zero_on_placement_domain`
- `test_div_poly_x_squared_minus_one`
- `test_gate_quotient_reconstructs_g`
- `test_copy_quotient_reconstructs_c`
- `test_copy_quotient_is_zero_on_valid_witness`
- `test_gate_quotient_matches_domain_check`
- `test_corrupted_gate_fails_quotient`
- `test_broken_copy_fails_quotient`
- `test_constraint_quotients_keys`

---

## Checkpoint

Before Lesson 06, you should be able to:

- [ ] State `F(X) = Z_H(X) · Q(X)` when `F` vanishes on `H`
- [ ] Write `vanishing_poly(n)` coeffs for `X^n - 1`
- [ ] Explain why honest copies often give `C(X) = 0`
- [ ] Explain why invalid witnesses should fail exact division
- [ ] Describe what KZG will commit to next (the quotient polynomials)

---

## Common mistakes

**Dividing by the wrong `n`.**  
`G` uses `N = 4`; `C` uses `NUM_PLACEMENTS = 12`. Mixing them up gives wrong quotients.

**Forgetting `trim` before comparing polys.**  
Trailing zeros make `==` fail even when polynomials match.

**Assuming remainder zero without checking.**  
Always verify `R(X) = 0` or compare `Z·Q == F`.

**Using integer division in `div_poly`.**  
Leading coeff ratios need `field.div`.

**Expecting nonzero `Q_C` on valid witness.**  
`C = 0` is normal for this tiny circuit when copies hold.

**Skipping public input checks.**  
Quotients cover gates + copies only; `y` binding stays separate until folded into a larger constraint later.

---

## How this connects to the full protocol

| Step | This lesson | Lesson 06 |
|------|-------------|-----------|
| Constraints | `G`, `C` | same |
| Fold pointwise zeros | `Q_G`, `Q_C` | same |
| Proof object | explicit coeffs | KZG commitments to `Q_G`, `Q_C`, witness columns |
| Verifier | multiply out `Z·Q` | single pairing check per commitment |

Real PLONK combines many constraint types into one grand quotient with random linear combination (α challenges). This tutorial keeps **gate** and **copy** quotients separate for clarity.

---

## Notation summary

| Symbol | Meaning |
|--------|---------|
| `F(X)` | Constraint polynomial (`G` or `C`) |
| `Z_H(X)` | `X^n - 1` vanishing on domain of size `n` |
| `Q(X)` | Quotient: `F = Z · Q` |
| `Q_G` | Gate quotient (divide by `X^4 - 1`) |
| `Q_C` | Copy quotient (divide by `X^12 - 1`) |

---

## Next lesson (preview)

**Lesson 06 — KZG commitments:** The prover commits to polynomials (witness columns, quotients) with a trusted setup. The verifier checks polynomial identities via pairings without seeing full coefficient vectors.

---

## Further reading

- [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) — quotient and constraint bundling
- [PLONK paper](https://eprint.iacr.org/2019/953) — Section on the quotient polynomial