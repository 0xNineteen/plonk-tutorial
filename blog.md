# WTF is PLONK

- were going to start with one concrete claim: prove you know `x` such that `x · x = y`, without revealing `x`

---

## Part 1 — Computation as a table (execution trace and gate constraints)

- first we want to represent our equation as a circuit, where each variable will become a wire

For `x · x = y` (`x = 7`, `y = 49`), the circuit has two logical wires and one multiplication gate:

```mermaid
flowchart LR
  x["wire x (private)"]
  x --> a["x (7)"]
  x --> b["x (7)"]
  a --> mul["mult gate"]
  b --> mul
  mul --> c["c = y (49) (public)"]
```

- `x` is private — the prover knows it, the verifier must not learn it
- `y` is public — the verifier supplies `49` and checks the proof against it

- we can also organize this circuit in a more general/flexible way, using to follow the equation: 
  - `x * x = y`
  - `<-> a * b = c`
  - `<-> a * b - c = 0`
  - `<-> s_mul * (a * b - c) = 0`

- now we have a much more general multiplication gate representation where:
  - `a` and `b` are two *cells* / *inputs* (which both carry wire `x` in our case)
  - `c` is the output (in our example `c` is `y`) 
  - and `s_mul` is the selector (think of `s_mul` as a gate that enables or disables the rest of the equation, in our example it will always be enabled.), 
  
NOTE: the full plonk uses a more sophisticated version of this to support other operations, but for learning purposes, understanding a single multiplication gate will do

our circuit now looks as follows:

```mermaid
flowchart LR
  x["wire x (private)"]
  x --> a["a"]
  x --> b["b"]
  a --> mul["mult gate"]
  b --> mul
  s["s_mul = 1"] -.-> mul
  mul --> c["c = y (public)"]
```

we can also represent our circuit as a matrix or something like a computer trace, where each row is the 'state' of the computer program, for example:

| `s_mul` | `a` | `b` | `c` | gate check `s · (a·b − c)` |
|---------|-----|-----|-----|----------------------------|
| 1 | 7 | 7 | 49 | `1 · (7·7 − 49) = 0` ✓ |
| 0 | 0 | 0 | 0 | `0 · (anything) = 0` ✓ |
| 0 | 0 | 0 | 0 | `0 · (anything) = 0` ✓ |
| 0 | 0 | 0 | 0 | `0 · (anything) = 0` ✓ |

NOTE: since we only have one gate/state, we only care about the first row (the other rows are `padded`)

- Row 0 is the only active gate: it enforces `s_mul · (a · b) = c`, i.e. `7 · 7 = 49`
- Rows 1–3 are *padding*: `s_mul = 0` turns the gate off, so those values don't matter

Using this matrix, the prover's claim is: **every row of the trace satisfies `s_mul · (a·b − c) = 0`**

## Part 2 — Identical wires must agree (copy constraints)

- notice how in our equation a and b both represent the same variable, however there are no constraints to ensure this holds.
- thats what copy constraints do
- to accomplish this we do a few things:
  - flatten the trace from N x M row/columns into a N * M x 1 vector called `Wire IDS` which label cells that must hold the same value
    - for example, in our case `WIRE_IDS = = [x, x, y, ...] = [0, 0, 1, ....]`
  - then we compute another check, that **all wire_id placements are equal inside the trace** and the public inputs (y) match too

in code, we can represent it as: 

```python
NUM_PLACEMENTS = N_TRACE_LENGTH * NUM_DATA_COLS # 4 x 3 = 12

ACTIVE_WIRE_IDS = [0, 0, 1] # flattened trace of ids: x, x, y
WIRE_IDS = ACTIVE_WIRE_IDS + [-1] * (NUM_PLACEMENTS - len(ACTIVE_WIRE_IDS))

PUBLIC_WIRES = (1,) # wire_id of y
```

- Worked example: wire 0 at placements 0 and 1 must both be `7`

| placement | cell | wire ID | trace value | copy rule |
|-----------|------|---------|---------------------------|-----------|
| 0 | row 0, `a` | 0 (`x`, private) | 7 | must equal placement 1 |
| 1 | row 0, `b` | 0 (`x`, private) | 7 | must equal placement 0 |
| 2 | row 0, `c` | 1 (`y`, public) | 49 | must equal `public_inputs[0]` |
| 3–11 | padding rows | −1 (none) | 0 | no copy checks |

- Wire 0 copy group: placements 0 and 1 both carry `x` → forces `a = b`
- Wire 1: placement 2 carries `y` → verifier checks `public_inputs[0] == 49`
- Without wire 0, a dishonest prover could set `a = 7`, `b = 8`, `c = 56` and still pass the gate

NOTE: a simple helper function going from a flat vector index to an output `(row column)` helps index inside the trace

## Proof and Verification of Gate and Copy Constraints

while theres no zk yet, we can prove everything holds by checking the trace's gates and copy constraints directly:

**1. Gate check** — loop over every row:

```python
def gate_mul(a, b, c, s):
    return s * (a * b - c)   # must be 0 mod p

def check_trace(circuit):
    for row in circuit.trace:
        if gate_mul(row[1], row[2], row[3], row[0]) != 0:
            return False
    return True
```

For our example, only row 0 matters: `1 · (7·7 − 49) = 0`. Padding rows pass because `s_mul = 0`.

**2. Copy check** — for each wire ID, all placements with that ID must agree:

```python
def check_wire_ids(circuit):
    for wire_id in {0, 1}:          # skip -1 (padding)
        placements = [p for p, wid in enumerate(WIRE_IDS) if wid == wire_id]
        if len(placements) < 2:
            continue                # wire 1 only appears once — no internal copy
        vals = [value_at_placement(circuit, p) for p in placements]
        if any(v != vals[0] for v in vals): # check all have the same value
            return False
    return True
```

Wire 0: placements 0 and 1 must both be `7`. Wire 1: only placement 2 — nothing to compare internally.

**3. Public input check** — bind what the verifier knows to the trace:

```python
def check_public_inputs(circuit, public_inputs):
    for k, wire_id in enumerate(PUBLIC_WIRES):   # PUBLIC_WIRES = (1,) → wire y
        placement = WIRE_IDS.index(wire_id)       # wire 1 lives at placement 2
        if value_at_placement(circuit, placement) != public_inputs[k]:
            return False
    return True
```

NOTE: the Verifier supplies `public_inputs = [49]`.

**Combined witness check:**

the full 'witness check' would be as follows: 

```python
def check_witness(circuit, public_inputs):
    return (
        check_trace(circuit)
        and check_wire_ids(circuit)
        and check_public_inputs(circuit, public_inputs)
    )
```

NOTE: the witness is another word for the prover's solution, which we eventually want to make private

| Check | What it catches |
|-------|-----------------|
| `check_trace` | wrong multiplication (`7·8 ≠ 56` would fail if `c` were wrong) |
| `check_wire_ids` | `a ≠ b` cheat (`7` vs `8`) |
| `check_public_inputs` | prover claims `y = 50` but trace says `49` |

This is an **honest verifier with full trace access** — the prover sends the whole table, verifier runs the three checks. 

---

## Part 3 — One polynomial per column

- now we want a faster way to evaluate the gates and copy constraints instead of just loops 
- for example, we can define `S(X), A(X), B(X), C(X)` from trace columns s_mul, a, b, and c as polynomials we want
  - we would interpolate on using x values w^i
  - and the column_i (s_i, a_i, ...) for the y values:

| Row `i` | `x_i = ω^i` | `s_mul` | `a` | `b` | `c` |
|---------|-------------|---------|-----|-----|-----|
| 0 | `1` | 1 | 7 | 7 | 49 |
| 1 | `ω` | 0 | 0 | 0 | 0 |
| 2 | `ω²` | 0 | 0 | 0 | 0 |
| 3 | `ω³` | 0 | 0 | 0 | 0 |

Note: we can use any x_i values to interpolate on (ie, {1, 2, 3, 4}), however we get some nice properties when using the roots of unity `ω^i` which we will cover later.

ie, For column `a`, values are `xs = [1, ω, ω², ω³]` and `ys = [7, 0, 0, 0]`, so we define polynomial `A(X)` with **degree < N** such that:

```
A(x_i) = a_i   for every i ∈ {0, 1, 2, 3}
```

We define the polynomial using **lagrange interpolation**: 
```
A(X) = Σ_{j=0}^{N-1} a_j · L_j(X)
```

where `x_j = ω^j` and

```
L_j(X) = Π_{m≠j} (X - x_m) / (x_j - x_m)
```

Notice how L_j(x_j) = 1 and L_j(x_m) = 0 (for m != j), so A(x_j) = a_j for all j.

Similarly define `S(X)` from selectors, `B(X)` from `b`, `C(X)` from `c`.

Now we can **redefine the constraints as one polynomial: `G(X) = S(X)·(A(X)·B(X) − C(X))`**. 

To confirm the constraints hold we just need to ensure `G(X) = 0 for all x in the domain H`. The easiest way to check this is again by loop for each x value. 

```python 
# equivalent to check_trace in previous chapter
def check_poly_trace(circuit, public_inputs):
    # compute
    S, A, B, C = interpolate_polynomials(circuit, DOMAIN)
    # verify
    for x in DOMAIN:
        if S(x) * (A(x) * B(x) - C(x)) != 0:
            return False
    return True
```

With a little more work and introducing a few more concepts, *we can actually do it with a single evaluation*.

## Vanishing polynomial

First we need to understand the vanishing polynomial `Z_H`.

On a multiplicative subgroup of order `N` we can define the vanishing polynomial as `Z_H`:

```
Z_H(X) = Π_{i=0}^{N-1} (X - ω^i) = X^N - 1
```

**Notice how `Z_H(x) = 0` for every `x ∈ H` and `Z_H(x) ≠ 0` for typical `x ∉ H`.** This will come in handy.

NOTE: the Vanishing polynomial factors to `Z_H(X) = X^N − 1` is zero exactly on `H` when using the roots of unity `ω^i`, which is why we chose them instead of a simpler `{0, 1, 2, 3}`.

In our example, `N = 4`, so:
```
Z_H(X) = X^4 - 1
```

## The Factor Theorem and The Quotient Polynomial

The main thing we need to understand is that for polynomials, the factor theorem states: 
- **for a polynomial f(x): f(a) = 0 if and only if (x−a) is a factor of f(x)**
- Another way of saying this is: **if f(a) = 0, then there exists a quotient q(x) such that, f(X) = (X − a) · q(X) for some polynomial q(X) = f(X) / (X − a)**
- Since we want to prove a polynomail `G(X) = 0` for all `x ∈ H` AND since `Z_H(X) = Π_{i=0}^{N-1} (X - ω^i)` i.e, the multiplication of `N` terms which are zero across all `x ∈ H`
  - *then* if we find a `Q(X)` such that `G(X) = Z_H(X) · Q(X)` as polynomials, then G(x) = 0 for all x ∈ H — so every gate constraint in G is satisfied at once.

- checking the polynomial equality can be done as follows:

```python 
G = compute_gate_poly(circuit)
Z = poly.vanishing_poly(n)
Qg, Rg = poly.div_poly(G, Z)

constraint_holds = ( # If true, G(x) = 0 for all x ∈ H
    not any(c != 0 for c in Rg)  # exact division
    and poly.eql(poly.mul_poly(Z, Qg), G) # poly equality
)
```

---

## Part 4 — Copies as a permutation polynomial
- Placement domain `H_pl`: one point per trace cell (row × column), not just per row
- Witness polynomial `W(X)`: values at all placements
- Permutation `σ`: where each placement's value must also appear
- Permuted witness `W^σ(X)`: values after applying `σ`
- Copy constraint polynomial: `C(X) = W(X) − W^σ(X)`
- Valid copies ⟺ `C(x) = 0` for all `x ∈ H_pl`
- Placement vanishing poly: `Z_pl(X) = X^{|H_pl|} − 1`
- Contrast: gate lives on 4 points; copies live on 12 — different domains

---

## Part 5 — From pointwise zeros to exact division (quotients)
- If `F` is zero on every domain point, then `Z(X)` divides `F(X)` in `𝔽_p[X]`
- Quotient: `Q(X) = F(X) / Z(X)` (exact division, remainder zero)
- Gate quotient: `Q_G(X) = G(X) / Z_H(X)`
- Copy quotient: `Q_C(X) = C(X) / Z_pl(X)`
- Verifier identity (algebraic): `Z(X)·Q(X) == F(X)` as polynomials
- Honest witness → division succeeds; broken witness → nonzero remainder
- On valid square circuit, copy constraint is often identically zero → `Q_C = 0`

---

## Part 6 — Hiding polynomials with commitments (KZG intuition)
- Problem: sending all polynomial coefficients is huge for real traces
- Trusted setup: secret `τ`, publish powers `1, τ, τ², …`
- Commitment: `C = f(τ)` — one value hides full polynomial (toy model)
- Production: same idea in an elliptic curve group (`f(τ)·G`)
- Verifier never sees coefficients; checks equations via openings

---

## Part 7 — Opening at a random point
- Verifier challenges evaluation point `z`
- Prover sends `y = f(z)` and proof `π = q(τ)` where `q(X) = (f(X) − y)/(X − z)`
- Factor theorem: exact division iff `f(z) = y`
- Verifier check: `C − y = π · (τ − z)` (toy); pairings in production
- Why hidden `τ` matters: can't fake `π` without knowing the polynomial
- Cheater with wrong `y` fails except with negligible probability

---

## Part 8 — Fiat–Shamir: who picks `z`?
- Interactive version: verifier sends random `z` after commitments
- Non-interactive: hash commitments + public inputs → `z`
- Transcript binding: changing any commitment changes `z`
- Soundness requirement: `z` should lie **outside** trace/placement domains
- Why: if `Z(z) = 0`, quotient identity `Z(z)·Q(z) = F(z)` becomes trivial

---

## Part 9 — Full prove / verify protocol (put it together)
- **Prover**
  - Build witness table
  - Check gates, copies, public inputs locally
  - Commit to trace columns + quotients + constraint polys
  - Hash transcript → `z`
  - Open every committed polynomial at `z`
  - Send `Proof = {commitments, openings, public inputs, z}`
- **Verifier**
  - Recompute `z` from transcript
  - Verify each KZG opening
  - Check gate: `Z_H(z)·Q_G(z) == G(z)`
  - Check copy: `Z_pl(z)·Q_C(z) == C(z)`
  - Cross-check: `G(z) == S(z)·(A(z)·B(z) − C(z))`
  - Confirm public inputs match
- What stays private: `x` (and full trace)
- What stays public: `y`, commitments, openings

---

## Part 10 — How this differs from "real" PLONK (honest map)
- General gate gadget: `q_L·A + q_R·B + q_M·AB + q_O·C + q_C` (five selector polys in VK)
- Tutorial shortcut: one mul gate → `S·(A·B − C)`
- Real copy argument: grand product polynomial + challenges `β, γ` (not explicit `W − W^σ`)
- Constraint folding: random `α` combines many constraints into one grand quotient
- Curves + pairings instead of field-element `f(τ)`
- FFT/NTT for `N = 2^{20}`, not `N = 4`
- Same skeleton everywhere: **trace → constraints → quotients → commit → challenge → open → verify**

---

## Part 11 — Mental model cheatsheet (one screen)
- Trace = computation written as a table
- Polynomials = columns interpolated on a domain
- Constraints = polynomials that must vanish on that domain
- Quotients = divide by vanishing poly when constraints hold
- Commitments = hide polynomials, keep algebraic structure
- Openings = prove one evaluation without revealing coeffs
- Fiat–Shamir = make challenges non-interactive
- Proof = commitments + openings + public inputs, not the witness

---

## Part 12 — What to build next (optional CTA)
- Implement the toy version in Python (link to tutorial repo structure)
- Swap toy KZG for Halo2 / arkworks / gnark
- Add a second gate type (addition) → need full `q_L…q_C`
- Scale `N` and add FFT
- Same statement in Noir → Barretenberg for a real proof

---

## Appendix bullets (sidebar / footnotes)
- Notation table: `H, ω, Z_H, τ, C, π, z, σ, Q_G, Q_C`
- Common mistakes: wrong vanishing domain, forgetting selectors on padding, `z ∈ H`, mixing up quotient vs selector `Q`
- Further reading: PLONK paper, KZG10, LambdaClass post, Halo2 book
- Diagram list to commission: trace table, wire IDs, domain map, commit/open flow, verifier equation
