# Lesson 03 — Polynomials on a domain

## What you will learn

Lessons 01 and 02 checked the trace **row by row**. PLONK’s next step treats each trace **column** as one polynomial and checks gates **on an entire domain at once**.

By the end of this lesson you will:

- Build the standard PLONK domain `H = {1, ω, ω², …, ω^{N-1}}` from a primitive `N`-th root of unity
- Turn each trace column into a polynomial `S(X), A(X), B(X), C(X)`
- Express the multiplication gate as one polynomial `G(X) = S(X) * (A(X)*B(X) - C(X))`
- Verify `G(x) = 0` for every `x ∈ H` — equivalent to `check_trace`, but in polynomial form
- Use the vanishing polynomial `Z_H(X) = X^N - 1`

Still no KZG, permutation, or quotient division — only polynomials and field arithmetic.

Reference: [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) (polynomial encoding of the trace).

---

## Big picture (where this lesson sits)

```
Lesson 01   Trace + gates
Lesson 02   Copy constraints
Lesson 03   Polynomials on a domain     ← you are here
Lesson 04   Permutation argument
Lesson 05   Quotient polynomial
Lesson 06   KZG commitments
Lesson 07   Prove + verify
```

| Lesson | What you checked |
|--------|------------------|
| 01 | `s_i * (a_i * b_i - c_i) = 0` for each row `i` |
| 02 | Wire IDs + public inputs |
| 03 | Same gate rule, as `G(X)` vanishing on all domain points |

Copy constraints stay in explicit form until Lesson 04. Today you only **re-encode gates** as polynomials.

---

## Why polynomials?

A trace with `N` rows gives `N` separate gate equations. The prover will eventually send **short commitments** to polynomials, not the full table.

The bridge is:

```
column of N values   →   one polynomial of degree < N
row-wise gate check  →   one polynomial identity on domain H
```

If `G(x) = 0` for every `x` in `H`, then `Z_H(X)` divides `G(X)` in `𝔽_p[X]`. Lesson 05 computes the quotient `Q(X) = G(X) / Z_H(X)`.

---

## Field and root of unity

You use `p = 1000033` from `field.py`. It is prime and `4 | (p - 1)`, so `𝔽_p^×` contains a **multiplicative subgroup** of order `N = 4`.

A primitive `N`-th root of unity `ω` satisfies:

```
ω^N = 1 (mod p),   ω^k ≠ 1 for 0 < k < N
```

`field.py` already provides `find_omega(n)` — brute-force search for a generator power. For this field:

```
ω = 649529
```

(Your code may find the same value; any primitive 4th root works.)

---

## Evaluation domain

PLONK maps **row `i`** to **domain point `x_i = ω^i`**:

```
H = {ω^0, ω^1, ω^2, ω^3} = {1, ω, ω², ω³}
```

| Row `i` | Domain point `x_i` | Example value (`p = 1000033`) |
|---------|-------------------|-------------------------------|
| 0 | `ω^0 = 1` | `1` |
| 1 | `ω^1` | `649529` |
| 2 | `ω^2` | `1000032` (= `p - 1`) |
| 3 | `ω^3` | `350504` |

All points are **nonzero** and closed under multiplication: `ω^i · ω^j = ω^{i+j mod N}`.

This is the same domain real PLONK provers use (with larger `N` and FFT). At `N = 4` you can still use direct Lagrange interpolation instead of an NTT.

---

## Trace column → polynomial

Extract one column from `circuit.trace` (length `N`). Example for witness `x = 7`, `y = 49`:

| Row `i` | `x_i = ω^i` | `s_mul` | `a` | `b` | `c` |
|---------|-------------|---------|-----|-----|-----|
| 0 | `1` | 1 | 7 | 7 | 49 |
| 1 | `ω` | 0 | 0 | 0 | 0 |
| 2 | `ω²` | 0 | 0 | 0 | 0 |
| 3 | `ω³` | 0 | 0 | 0 | 0 |

For column `a`, values are `[7, 0, 0, 0]`. Define polynomial `A(X)` with **degree < N** such that:

```
A(x_i) = a_i   for every i ∈ {0, 1, 2, 3}
```

Similarly define `S(X)` from selectors, `B(X)` from `b`, `C(X)` from `c`.

**Lagrange interpolation** (direct formula; FFT optional at larger `N`):

```
A(X) = Σ_{j=0}^{N-1} a_j · L_j(X)
```

where `x_j = ω^j` and

```
L_j(X) = Π_{m≠j} (X - x_m) / (x_j - x_m)
```

All division is in `𝔽_p` — use `field.inv`.

---

## Gate polynomial

Per-row gate from Lesson 01:

```
s_i * (a_i * b_i - c_i) = 0
```

Substitute polynomials that agree with the columns on `H`:

```
G(X) = S(X) * (A(X) * B(X) - C(X))
```

**Key claim:** For honest witnesses,

```
G(x) = 0   for every x ∈ H
```

because at `x = x_i = ω^i` the values of `S, A, B, C` match row `i` and the row gate holds.

This is the polynomial form of `check_trace`.

### Degree intuition (for later)

- `A, B, C, S` each degree `< N`
- `A * B` degree `< 2N`
- `G` degree `< 3N`

You do not need to compute quotient yet — only evaluate `G` on `H`.

---

## Vanishing polynomial

On a multiplicative subgroup of order `N`:

```
Z_H(X) = Π_{i=0}^{N-1} (X - ω^i) = X^N - 1
```

For `N = 4`:

```
Z_H(X) = X^4 - 1
```

Check at a point:

```
vanishing_eval(x) = x^N - 1 (mod p)
```

Properties:

```
Z_H(x) = 0   for every x ∈ H
Z_H(x) ≠ 0   for typical x ∉ H
```

If `G(x) = 0` for all `x ∈ H`, then `Z_H(X)` divides `G(X)` in `𝔽_p[X]`. Lesson 05 computes `Q(X) = G(X) / Z_H(X)`.

---

## Field helpers (`field.py`)

Already updated in the repo:

| Function | Purpose |
|----------|---------|
| `inv(a)` | Modular inverse via Fermat (`a^{p-2}`) |
| `div(a, b)` | `mul(a, inv(b))` |
| `find_omega(n)` | Primitive `n`-th root; requires `n \| (p - 1)` |

`find_omega` is used once in `domain.py` to set `OMEGA` and `DOMAIN`.

---

## Polynomial representation

Represent a polynomial by coefficients **low degree first**:

```
f(X) = c_0 + c_1*X + c_2*X^2 + ...
coeffs = [c_0, c_1, c_2, ...]
```

Suggested API in `poly.py`:

| Function | Purpose |
|----------|---------|
| `eval_poly(coeffs, x)` | Horner evaluation mod `p` |
| `add_poly`, `sub_poly`, `mul_poly` | Polynomial arithmetic mod `p` |
| `interpolate(values, domain)` | Lagrange → coeffs for degree `< N` |

Keep coefficients trimmed (no trailing zeros) so degree is obvious.

### Horner evaluation

```
eval([c0, c1, c2], x):
    acc = 0
    for c in reversed(coeffs):
        acc = add(mul(acc, x), c)
    return acc
```

### Interpolate sanity check

After interpolating column `a` from a valid witness:

```
for i, x in enumerate(DOMAIN):
    assert eval_poly(coeffs, x) == circuit.trace[i][1]
```

---

## Encoding the trace

New module `encode.py`:

```
trace_column_values(circuit, col) -> list[N]
    col 0 = s_mul, 1 = a, 2 = b, 3 = c

trace_polynomials(circuit) -> dict
    returns {"s": coeffs, "a": coeffs, "b": coeffs, "c": coeffs}
```

Use `DOMAIN` from `domain.py` everywhere — do not hardcode `ω` or domain points in multiple files.

---

## Polynomial gate check

New module `gates_poly.py` (or extend `gates.py` if you prefer one file):

```
gate_constraint_poly(circuit) -> coeffs of G(X)

eval_gate_constraint_at(circuit, x) -> G(x)

check_gates_on_domain(circuit) -> bool
    for each x in DOMAIN:
        if eval_gate_constraint_at(circuit, x) != 0:
            return False
    return True
```

Build `G` by polynomial arithmetic:

```
S, A, B, C = trace polynomials
G = mul_poly(S, sub_poly(mul_poly(A, B), C))
```

**Equivalence:** On valid witnesses, `check_gates_on_domain(circuit)` should agree with `check_trace(circuit)` from Lesson 01.

---

## Data structures to implement

### 1. `domain.py`

```python
import field as F
from circuit import N_TRACE_LENGTH

OMEGA = F.find_omega(N_TRACE_LENGTH)
DOMAIN = [pow(OMEGA, i, F.p) for i in range(N_TRACE_LENGTH)]

def lagrange_basis(j, x):
    """L_j(x) — j-th Lagrange basis polynomial evaluated at x."""

def vanishing_eval(x):
    """Z_H(x) = x^N - 1 (mod p)."""
```

Sanity checks you can run after implementing:

```
assert DOMAIN[0] == 1
assert pow(OMEGA, N_TRACE_LENGTH, F.p) == 1
assert pow(OMEGA, N_TRACE_LENGTH // 2, F.p) != 1
for x in DOMAIN:
    assert vanishing_eval(x) == 0
```

### 2. `poly.py`

Polynomial coeffs + `eval_poly`, `add_poly`, `sub_poly`, `mul_poly`, `interpolate`.

### 3. `encode.py`

`trace_column_values`, `trace_polynomials`.

### 4. `gates_poly.py`

`gate_constraint_poly`, `check_gates_on_domain`.

---

## Your task

Implement polynomial encoding and domain gate checks:

1. **`domain.py`** — `OMEGA`, `DOMAIN`, `lagrange_basis`, `vanishing_eval`
2. **`poly.py`** — polynomial arithmetic + `interpolate`
3. **`encode.py`** — `trace_polynomials(circuit)`
4. **`gates_poly.py`** — `gate_constraint_poly`, `check_gates_on_domain`
5. **Tests** in `tests/test_lesson03.py`

(`field.py` already has `inv`, `div`, and `find_omega`.)

Do **not** implement quotient division, permutation, or KZG yet.

### Correctness properties

| Scenario | Expected |
|----------|----------|
| `DOMAIN[0] == 1` and `ω^4 == 1` | `True` |
| Interpolate column `a` from valid witness | `eval` at each `x ∈ DOMAIN` matches trace |
| `check_gates_on_domain` on valid `x=7, y=49` | `True` |
| Same as `check_trace` on valid witness | both `True` |
| Corrupt `c[0]` after build | both `False` |
| `vanishing_eval(x)` for `x ∈ DOMAIN` | `0` |
| `vanishing_eval(2)` (off-domain) | `≠ 0` |
| Padding row garbage with selectors `0` | polynomial gate check still `True` |

### Suggested extra test

Compare `gate_constraint_poly` evaluated on domain vs row-wise `gate_mul`:

```
for i, x in enumerate(DOMAIN):
    row = circuit.trace[i]
    assert eval_gate_constraint_at(circuit, x) == gate_mul(row[1], row[2], row[3], row[0])
```

---

## Run it

```bash
pytest tests/test_lesson01.py tests/test_lesson02.py -v   # still pass
pytest tests/test_lesson03.py -v
```

Suggested tests (you write the file):

- `test_omega_is_primitive_4th_root`
- `test_domain_starts_at_one`
- `test_lagrange_basis_is_one_at_j`
- `test_interpolate_column_a`
- `test_trace_polynomials_match_trace`
- `test_vanishing_equals_xn_minus_one`
- `test_vanishing_zero_on_domain`
- `test_vanishing_nonzero_off_domain`
- `test_check_gates_on_domain_valid_witness`
- `test_check_gates_matches_check_trace`
- `test_corrupted_witness_fails_polynomial_gate_check`
- `test_padding_rows_do_not_break_polynomial_check`

---

## Checkpoint

Before Lesson 04, you should be able to:

- [ ] Explain why row `i` maps to `ω^i`, not the integer `i`
- [ ] Write the Lagrange basis formula for `L_j(X)` from memory
- [ ] State `G(X) = S(X) * (A(X)*B(X) - C(X))` and why `G(ω^i) = 0` on honest traces
- [ ] State `Z_H(X) = X^N - 1` and why it vanishes on `H`
- [ ] Describe what Lesson 05 will do with `G` and `Z_H`

---

## Common mistakes

**Using `H = {0, 1, 2, 3}` with this field.**  
That was a workaround for the old prime. With `p = 1000033`, use the subgroup `{1, ω, ω², ω³}`.

**Hardcoding domain points in every file.**  
Export `OMEGA` and `DOMAIN` from `domain.py` only.

**Forgetting modular inverses in Lagrange.**  
`(x_j - x_m)` is mod `p`; use `inv`, not integer division.

**Coefficient order reversed.**  
Use `[c_0, c_1, …]` = low to high. High-to-low breaks `eval` and `mul`.

**Evaluating `G` only at `x = 1`.**  
Must check **all** `N` domain points — same pitfall as checking only row `0` in Lesson 01.

**Building `G` by interpolating row gate results.**  
Correct approach: interpolate **columns** to `S, A, B, C`, then form `S * (A*B - C)` algebraically.

**Confusing `vanishing_eval` with `find_omega`.**  
`ω` is a domain **point**. `Z_H(X) = X^N - 1` is a **polynomial** that vanishes at every domain point.

---

## How this connects to the full protocol

| Step | This lesson | Later |
|------|-------------|-------|
| Domain | `H = ⟨ω⟩` | Same; larger `N` + FFT in production |
| Columns → polys | `trace_polynomials` | Committed via KZG (Lesson 06) |
| Gate check | `G(x) = 0` on `H` | Quotient `Q = G / Z_H` (Lesson 05) |
| Copy check | Still explicit (Lesson 02) | Permutation polynomial (Lesson 04) |

After Lessons 04–05, the prover sends a handful of polynomial commitments instead of the trace. Lesson 03 is where the trace becomes **algebra**.

---

## Optional stretch: FFT / NTT

At `N = 4`, Lagrange is enough. For curiosity: the same subgroup enables **Number Theoretic Transform** in `O(N log N)` for multiply/interpolate at large `N`. Same `ω`, same `H` — just a faster implementation path.

---

## Notation summary

| Symbol | Meaning |
|--------|---------|
| `ω` | Primitive `N`-th root of unity |
| `H` / `DOMAIN` | `{1, ω, ω², …, ω^{N-1}}` |
| `x_i` | `ω^i` — domain point for row `i` |
| `S(X), A(X), B(X), C(X)` | Column polynomials |
| `G(X)` | Gate constraint polynomial |
| `Z_H(X)` | `X^N - 1` — vanishing polynomial on `H` |
| `L_j(X)` | Lagrange basis polynomial |
| `deg(f)` | degree; here `< N` for column polys |

---

## Next lesson (preview)

**Lesson 04 — Permutation argument:** Copy constraints become a polynomial equation over `H` using a permutation `σ` that sorts cells by wire ID. The prover builds a grand product polynomial `Z_perm(X)` (not to be confused with `Z_H`) that enforces “same wire → same value” in one shot.

---

## Further reading

- [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) — encoding the trace and gate polynomials
- [PLONK paper](https://eprint.iacr.org/2019/953) — Section on custom gates and polynomial identities on multiplicative subgroups