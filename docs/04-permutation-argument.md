# Lesson 04 — Permutation argument

## What you will learn

Lesson 02 checked copies with **explicit loops** (`check_wire_ids`). Lesson 03 encoded **gates** as polynomials on a domain. This lesson encodes **copy constraints** the same way.

By the end you will:

- Build a **permutation** `σ` over placement indices from `WIRE_IDS`
- Flatten trace data cells into a witness vector `w` on a **placement domain** `H_pl`
- Form a **permuted polynomial** `W^σ(X)` and a **copy constraint polynomial** `C(X) = W(X) - W^σ(X)`
- Verify `C(x) = 0` for every `x ∈ H_pl` — equivalent to `check_wire_ids`, in polynomial form
- Understand how full PLONK’s **grand-product polynomial** `Z_perm` (different from `Z_H`) compresses the same idea further

Still no quotient division, KZG, or Fiat–Shamir challenges — only `σ`, interpolation, and field arithmetic.

Reference: [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) (permutation / copy argument).

---

## Big picture (where this lesson sits)

```
Lesson 01   Trace + gates
Lesson 02   Copy constraints (explicit loops)
Lesson 03   Gate polynomials on row domain H
Lesson 04   Copy polynomials on placement domain H_pl   ← you are here
Lesson 05   Quotient polynomial
Lesson 06   KZG commitments
Lesson 07   Prove + verify
```

| Lesson | Copy check style |
|--------|------------------|
| 02 | `w_i == w_j` for cells sharing a wire ID |
| 04 | `C(X) = W(X) - W^σ(X)` vanishes on `H_pl` |

Gate checks from Lesson 03 stay separate. Today you polynomialize **only** the wiring.

---

## Two domains (do not mix them up)

| Domain | Size | Points | Used for |
|--------|------|--------|----------|
| **Row domain** `H` | `N = 4` | `{1, ω, ω², ω³}` | Gate polynomial `G(X)` (Lesson 03) |
| **Placement domain** `H_pl` | `NUM_PLACEMENTS = 12` | `{1, ω_pl, …, ω_pl^11}` | Copy polynomial `C(X)` (this lesson) |

Row `i` maps to `ω^i`. Placement `p` maps to `ω_pl^p`.

`p = 1000033` satisfies `12 | (p - 1)`, so `ω_pl = find_omega(12)` exists.

Keep both domains in `domain.py` (or split `placement_domain.py` if you prefer).

---

## From wire IDs to a permutation σ

Lesson 02 stored `WIRE_IDS[p]` — which logical wire owns placement `p`.

The **permutation** `σ` reorders placements so copies line up. For each wire ID `w ≥ 0`, collect all placements carrying `w` and **cycle** them:

```
placements(w) = [ p | WIRE_IDS[p] == w ]
σ(p0) = p1, σ(p1) = p2, …, σ(p_{k-1}) = p0   (cycle)
```

For padding (`WIRE_IDS[p] == -1`): **identity** `σ(p) = p`.

The notation `[ p | WIRE_IDS[p] == w ]` means **all placements `p` such that** `WIRE_IDS[p] == w` (like Python `[p for p in ... if WIRE_IDS[p] == w]`). The `|` here is “such that,” not divisibility.

### Why collect placements and cycle them?

**Copy constraints** say: every cell labeled wire `w` must hold the **same value**.

Wire `0` (`x`) appears twice — at placement `0` (`a`) and placement `1` (`b`). You need:

```
w[0] == w[1]
```

Lesson 02 checked that with an explicit loop over equal wire IDs. Lesson 04 needs a **uniform rule** that works for every placement and encodes cleanly as a polynomial.

#### The one-rule trick

Build σ so each placement `p` has exactly one partner `σ(p)`. Require:

```
w[p] == w[σ(p)]   for every p
```

For wire `0`, use a **2-cycle** on its placements:

```
σ(0) = 1
σ(1) = 0
```

Then `w[0] == w[σ(0)] = w[1]` and `w[1] == w[σ(1)] = w[0]` — same equality, one rule per placement.

#### k cells on one wire → k-cycle

If wire `w` appears at placements `[p0, p1, …, p_{k-1}]`, cycle them:

```
σ(p0) = p1,  σ(p1) = p2,  …,  σ(p_{k-1}) = p0
```

Then `w[p0] == w[p1] == … == w[p_{k-1}]` — all values in the ring must match.

#### One cell → fixed point

If wire `w` has only one placement `p`, set `σ(p) = p`. Then `w[p] == w[p]` is always true — no extra constraint, which is correct (nothing to copy).

#### Why not just compare pairs (like Lesson 02)?

You can! Lesson 02’s `check_wire_ids` already does. The permutation view exists because PLONK wants:

| Lesson 02 | Lesson 04 |
|-----------|-----------|
| Loop: “all vals with same wire ID equal?” | One rule: `w[p] == w[σ(p)]` for all `p` |
| Hard to polynomialize | Define `W^σ` and `C(X) = W - W^σ` |
| Pairwise within wire groups | σ is a **bijection** on all placements — what grand-product machinery expects |

**Collect placements** = find everyone sharing a wire.  
**Cycle them** = wire them into a ring so “value at `p` must equal value at partner `σ(p)`.”

That is the bridge from Lesson 02’s semantics to Lesson 04’s `W(X) = W^σ(X)` on the domain.

### Square circuit `σ`

| Placement | row | col | wire | `σ(p)` |
|-----------|-----|-----|------|--------|
| 0 | 0 | a | 0 (`x`) | 1 |
| 1 | 0 | b | 0 (`x`) | 0 |
| 2 | 0 | c | 1 (`y`) | 2 |
| 3..11 | pad | * | -1 | self |

`σ` is a bijection on `{0, …, 11}`.

### Semantic copy check (bridge from Lesson 02)

Extract placement values from the trace:

```
w[p] = value_at_placement(circuit, p)
```

**Copy correctness** is equivalent to:

```
w[p] == w[σ(p)]   for every p
```

For wire `0`, `w[0] == w[1]`. For a fixed point, always true. Padding copies `0 == 0` if cells are zero.

This is exactly what `check_wire_ids` enforces for cycle wires.

---

## Witness vector and `W(X)`

Flatten the trace into `w` (length 12):

```
w[p] = circuit.trace[row][col]   at placement p
```

Example for `x = 7`, `y = 49`:

```
w = [7, 7, 49, 0, 0, 0, 0, 0, 0, 0, 0, 0]
```

Interpolate on `H_pl`:

```
W(X) such that  W(ω_pl^p) = w[p]   for p = 0..11
```

Use `poly.interpolate(PLACEMENT_DOMAIN, w)` from Lesson 03.

---

## Permuted witness and `W^σ(X)`

Apply `σ` to **values**, not to domain points:

```
w^σ[p] = w[σ(p)]
```

Example: `w[0]=7, w[1]=7` → `w^σ[0]=w[1]=7, w^σ[1]=w[0]=7`.

Interpolate:

```
W^σ(X) such that  W^σ(ω_pl^p) = w[σ(p)]
```

---

## Copy constraint polynomial

```
C(X) = W(X) - W^σ(X)
```

**Claim:** Honest witnesses satisfy

```
C(x) = 0   for every x ∈ H_pl
```

because at `x = ω_pl^p`:

```
W(x) - W^σ(x) = w[p] - w[σ(p)] = 0
```

This is the polynomial form of `check_wire_ids` (for wires realized as cycles).

### Degree

`W` and `W^σ` each have degree `< 12`, so `deg(C) < 12`.

---

## Public inputs (still separate)

Permutation checks **internal** wiring. **Public binding** (`y` matches `public_inputs[0]`) stays the Lesson 02 check:

```
check_public_inputs(circuit, public_inputs)
```

Full witness validity:

```
check_witness = gates + copies (poly) + public inputs
```

Do not drop `check_public_inputs` — `σ` does not encode publicity by itself.

---

## Grand product `Z_perm` (concept — full PLONK)

Real PLONK does not stop at `W(X) - W^σ(X)`. It uses random challenges `β, γ` (Fiat–Shamir in production) and a running-product polynomial `Z_perm` with:

```
Z(ω_pl^0) = 1
Z(ω_pl^{i+1}) = Z(ω_pl^i) · (w_i + β·k_i + γ) / (w_{σ(i)} + β·k_{σ(i)} + γ)
Z(ω_pl^{11}) = 1
```

Here `k_i` are **distinct cell identifiers** (in full PLONK: row/column tags for `a`, `b`, `c` separately — not just placement index).

Why the extra machinery?

- A single polynomial equation `C(X) = 0` on `H_pl` is enough at our scale.
- Full PLONK folds **all** copy checks into one recurrence so the verifier checks one polynomial identity after quotient + KZG.
- Distinct `k_i` per `(row, column)` stop algebraic cancellation cheats that naive products might miss in larger circuits.

**This lesson:** implement `C(X) = W - W^σ`.  
**Stretch goal:** fixed `β = 2`, `γ = 3`, compute `Z_perm` evaluations by recurrence, require `Z(ω_pl^{11}) = 1`, interpolate `Z(X)`.

Lesson 07 replaces fixed challenges with Fiat–Shamir.

---

## Data structures to implement

### 1. Extend `domain.py`

```python
from layout import NUM_PLACEMENTS

OMEGA_PL = F.find_omega(NUM_PLACEMENTS)
PLACEMENT_DOMAIN = [pow(OMEGA_PL, i, F.p) for i in range(NUM_PLACEMENTS)]

def placement_vanishing_eval(x):
    """Z_{H_pl}(x) = x^12 - 1"""
    return F.sub(pow(x, NUM_PLACEMENTS, F.p), 1)
```

Keep row-domain `OMEGA`, `DOMAIN` from Lesson 03.

### 2. `permutation.py`

```python
from layout import WIRE_IDS, NUM_PLACEMENTS

def build_sigma() -> list[int]:
    """σ[p] = image of placement p under copy permutation."""

def permute_values(values, sigma) -> list:
    """out[p] = values[sigma[p]]"""
```

`build_sigma` algorithm:

```
sigma = [0, 1, ..., n-1]  # identity default
for each wire_id w >= 0:
    ps = [p for p in range(n) if WIRE_IDS[p] == w]
    if len(ps) >= 2:
        for i, p in enumerate(ps):
            sigma[p] = ps[(i + 1) % len(ps)]
return sigma
```

### 3. `copy_poly.py`

```python
def placement_values(circuit) -> list[F.p elements]

def witness_poly(circuit) -> coeffs      # W(X)
def permuted_witness_poly(circuit) -> coeffs   # W^σ(X)
def copy_constraint_poly(circuit) -> coeffs      # C(X) = W - W^σ

def check_copies_on_domain(circuit) -> bool
def check_copies_match_lesson02(circuit) -> bool  # optional cross-check
```

### 4. Update `copy_constraints.py` (optional integration)

```python
def check_witness(circuit, public_inputs):
    return (
        check_trace(circuit)
        and check_copies_on_domain(circuit)   # replaces check_wire_ids
        and check_public_inputs(circuit, public_inputs)
    )
```

Or keep both checks during development.

---

## Your task

Implement the permutation copy argument:

1. **Extend `domain.py`** — `OMEGA_PL`, `PLACEMENT_DOMAIN`, `placement_vanishing_eval`
2. **`permutation.py`** — `build_sigma`, `permute_values`
3. **`copy_poly.py`** — `placement_values`, `witness_poly`, `permuted_witness_poly`, `copy_constraint_poly`, `check_copies_on_domain`
4. **Tests** in `tests/test_lesson04.py`

Do **not** implement quotient, KZG, or Fiat–Shamir yet.

### Correctness properties

| Scenario | Expected |
|----------|----------|
| `build_sigma()` on square circuit | 2-cycle on `{0,1}`, fixed point at `2`, identity on padding |
| Valid `x=7, y=49` | `check_copies_on_domain` → `True` |
| Same witness | `check_copies_on_domain` agrees with `check_wire_ids` |
| Gate OK, `a≠b` on row 0 (`7, 8, 56`) | `check_copies_on_domain` → `False` |
| `C(x) = 0` for all `x ∈ PLACEMENT_DOMAIN` on valid witness | `True` |
| `placement_vanishing_eval(x)` on `H_pl` | `0` |
| Public input mismatch | `check_public_inputs` → `False` (unchanged) |

### Simulating a copy failure

```python
circuit, pub = build_witness(7, 49)
circuit.trace[0] = [1, 7, 8, 56]   # gate OK, copies broken
assert check_trace(circuit)
assert not check_wire_ids(circuit)
assert not check_copies_on_domain(circuit)
```

---

## Run it

```bash
pytest tests/test_lesson01.py tests/test_lesson02.py tests/test_lesson03.py -v
pytest tests/test_lesson04.py -v
```

Suggested tests (you write the file):

- `test_sigma_is_bijection`
- `test_sigma_cycles_wire_zero`
- `test_sigma_fixed_point_wire_one`
- `test_sigma_identity_on_padding`
- `test_placement_values_match_trace`
- `test_witness_poly_eval_on_placement_domain`
- `test_permuted_witness_swaps_wire_zero_cells`
- `test_copy_constraint_zero_on_valid_witness`
- `test_copy_check_matches_check_wire_ids`
- `test_gate_ok_copy_fails_polynomial_check`
- `test_placement_vanishing_zero_on_domain`
- `test_gates_and_copies_both_pass_valid_witness`

---

## Checkpoint

Before Lesson 05, you should be able to:

- [ ] Draw `σ` for the square circuit on placements `0..11`
- [ ] Explain `w^σ[p] = w[σ(p)]` vs permuting domain points
- [ ] Write `C(X) = W(X) - W^σ(X)` and why it vanishes on `H_pl`
- [ ] State the difference between row domain `H` and placement domain `H_pl`
- [ ] Explain what `Z_perm` adds in full PLONK (grand product + challenges)

---

## Common mistakes

**Permuting domain points instead of values.**  
`W^σ(ω_pl^p) = w[σ(p)]`, not `w[p]` evaluated at `ω_pl^{σ(p)}`.

**Using row domain `H` for copy polynomials.**  
`G(X)` lives on 4 points; `C(X)` lives on 12. Sizes differ.

**Dropping public-input checks.**  
`σ` only ties cells with the same wire ID. Public binding is separate.

**Expecting `σ` to fix `a≠b` at the gate level.**  
Gates and copies are independent until you require both.

**Confusing `Z_H` and `Z_perm`.**  
`Z_H(X) = X^N - 1` vanishes on row domain (Lesson 03). `Z_perm` is the grand-product wiring polynomial (concept / stretch here).

**Forgetting padding.**  
Identity `σ(p)=p` on wire `-1` keeps ratios well-defined; zero padding cells are fine.

---

## How this connects to the full protocol

| Piece | This lesson | Lesson 05+ |
|-------|-------------|------------|
| Gate check | `G(X)` on `H` | `Q_G(X) = G(X) / Z_H(X)` |
| Copy check | `C(X)` on `H_pl` | `Q_C(X) = C(X) / Z_{H_pl}(X)` |
| Challenges | — | `β, γ` via Fiat–Shamir (Lesson 07) |
| Proof object | — | KZG commitments (Lesson 06) |

Lesson 05 combines gate + copy (and later public) constraint polynomials into quotients that the verifier checks via polynomial identities.

---

## Notation summary

| Symbol | Meaning |
|--------|---------|
| `σ` | Permutation on placement indices |
| `w[p]` | Trace value at placement `p` |
| `ω_pl` | Primitive 12th root of unity |
| `H_pl` / `PLACEMENT_DOMAIN` | `{1, ω_pl, …, ω_pl^11}` |
| `W(X)` | Witness polynomial on `H_pl` |
| `W^σ(X)` | Permuted witness polynomial |
| `C(X)` | `W(X) - W^σ(X)` — copy constraint polynomial |
| `Z_{H_pl}(X)` | `X^12 - 1` — placement vanishing polynomial |
| `Z_perm(X)` | Grand-product wiring polynomial (full PLONK) |

---

## Next lesson (preview)

**Lesson 05 — Quotient polynomial:** When `F(X)` vanishes on every point of a domain `H`, `F(X) = Z_H(X) · Q(X)`. You will divide `G(X)` and `C(X)` by their vanishing polynomials and obtain explicit quotient polynomials the verifier checks.

---

## Further reading

- [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) — permutation argument and copy constraints
- [PLONK paper](https://eprint.iacr.org/2019/953) — permutation polynomial and grand product