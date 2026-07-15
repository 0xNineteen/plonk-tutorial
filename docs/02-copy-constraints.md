# Lesson 02 — Copy constraints

## What you will learn

In Lesson 01, you checked **gate polynomials**. That is only half the story.

A cheating prover could set `a = 7` and `b = 8` on the multiplication row and still satisfy `a * b = c` if `c = 56`. The gate would pass, but that is **not** our circuit `x * x = y`.

PLONK fixes this with **copy constraints**: cells that represent the **same logical wire** must hold the **same value**. The LambdaClass article describes this as wiring the program together — gates do arithmetic, copies connect variables.

By the end of this lesson you will:

- Understand why gates alone are not enough
- Assign each trace cell a **wire ID** (which logical variable it carries)
- Check **local copy equalities** before any cryptography
- Bind **public inputs** to the correct trace cells

Still no polynomials or KZG — only bookkeeping and equality checks.

Reference: [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) (copy constraints / permutation section).

---

## The cheating problem (why this lesson exists)

Lesson 01 gate on row `0`:

```
s * (a * b - c) = 0
```

| `a` | `b` | `c` | Gate OK? | Valid `x² = y`? |
|-----|-----|-----|----------|-----------------|
| 7 | 7 | 49 | yes | yes |
| 7 | 8 | 56 | yes | **no** |
| 3 | 3 | 9 | yes | yes |

The gate only enforces **one multiplication**. It does **not** say “`a` and `b` are the same secret `x`.”

**Copy constraints** enforce that.

---

## Wires vs cells (review + precision)

| Concept | Meaning |
|---------|---------|
| **Wire** | One logical value in the program (`x`, `y`) |
| **Cell** | One entry in the trace table (a specific row + column) |
| **Copy constraint** | Two cells must store the same field element because they are the same wire |

One wire → many cells. All those cells must match.

In our square circuit:

```
wire X  →  cell (row 0, column a)  and  cell (row 0, column b)
wire Y  →  cell (row 0, column c)  and  public input y
```

---

## Which columns participate in copies?

Selectors (`s_mul`) are **not** wires. They are gate machinery (0 or 1).

Only **data columns** participate in copy constraints:

| Column index | Name | Copy participant? |
|--------------|------|-------------------|
| 0 | `s_mul` | No |
| 1 | `a` | Yes |
| 2 | `b` | Yes |
| 3 | `c` | Yes |

Padding rows still have `a,b,c` cells, but with no active gates and no meaningful wires — wire ID `NONE` or a dedicated “padding” id.

---

## Placement index (flattening the grid)

PLONK eventually permutes a long list of all wire-carrying cells. You need a consistent **address** for each cell.

Define **placement index** in row-major order over `(row, data_column)`:

```
data columns order: a (=1), b (=2), c (=3)

placement_index(row, col) = row * 3 + (col - 1)
```

For `N = 4` rows:

| placement | row | col | name |
|-----------|-----|-----|------|
| 0 | 0 | a | mul left |
| 1 | 0 | b | mul right |
| 2 | 0 | c | mul output |
| 3 | 1 | a | padding |
| 4 | 1 | b | padding |
| 5 | 1 | c | padding |
| … | … | … | … |
| 11 | 3 | c | padding |

Helper to read a value:

```
value_at(circuit, row, col) = circuit.trace[row][col]
```

(Using your `Circuit.trace` numpy layout: `trace[row, 0]` is `s_mul`, `trace[row, 1]` is `a`, etc.)

---

## Wire IDs

Assign each **placement** an integer **wire ID**:

| Wire ID | Logical meaning | Public? |
|---------|-----------------|---------|
| `0` | secret `x` | no |
| `1` | public `y` | yes |
| `-1` | unused / padding (no copy checks) | — |

**Copy specification for the square circuit:**

| placement | row | col | wire ID |
|-----------|-----|-----|---------|
| 0 | 0 | a | 0 (`x`) |
| 1 | 0 | b | 0 (`x`) |
| 2 | 0 | c | 1 (`y`) |
| 3..11 | 1..3 | * | -1 (padding) |

**Copy groups** (cells that must be equal):

```
Group wire 0:  { placement 0, placement 1 }     →  a and b on row 0
Group wire 1:  { placement 2 }                  →  c on row 0 (plus public bind)
```

If two placements share a wire ID `≥ 0`, their values must be equal.

---

## Public input binding

Public inputs are not magic — they must equal the trace cell wired to that public wire.

For us:

```
public_inputs[0]  ==  value at (row 0, column c)
```

If the prover sets `c = 49` but claims public `y = 50`, the witness must fail **before** proof generation.

This is a **copy** between:

- the **public input bus** (what verifier sees)
- the **trace cell** carrying wire `y`

---

## Local copy checker (Lesson 02 verifier)

Combine Lesson 01 gate check with new checks:

```
is_valid_witness(circuit, public_inputs):
    1. check_trace(circuit)              # gates
    2. check_wire_ids(circuit)           # copies inside trace
    3. check_public_inputs(circuit, public_inputs)
```

### `check_wire_ids`

Precompute a static table `WIRE_ID[placement]` from the circuit **shape** (square circuit spec).

Algorithm:

```
For each wire_id w >= 0:
    Collect all placement indices with that wire_id.
    If there are 2+ placements:
        All their values must be equal.
    If there is 1 placement:
        No internal copy needed for that wire.
```

Pseudocode:

```
def value_at_placement(circuit, placement):
    row = placement // 3
    col = (placement % 3) + 1   # map 0→a, 1→b, 2→c
    return circuit.trace[row][col]

def check_wire_ids(circuit, wire_ids):
    for w in unique(wire_ids where w >= 0):
        positions = [i for i, wid in enumerate(wire_ids) if wid == w]
        vals = [value_at_placement(circuit, i) for i in positions]
        if any(v != vals[0] for v in vals):
            return False
    return True
```

### `check_public_inputs`

```
def check_public_inputs(circuit, public_inputs, public_wire_map):
    # public_wire_map: wire_id -> placement index
    # For us: wire 1 (y) lives at placement 2
    for each (wire_id, placement) in public_wire_map:
        if value_at_placement(circuit, placement) != public_inputs[...]:
            return False
    return True
```

---

## Refactor witness construction

Lesson 01 set `a` and `b` manually to the same `x`. Lesson 02 makes the **wire table** the source of truth.

### Wire value table

```
wire_values: dict[wire_id, field element]
    0 → x   (private)
    1 → y   (public)
```

### Scatter into trace

```
build_witness(x, y):
    1. Validate y == x * x (mod p)
    2. wire_values = {0: x, 1: y}
    3. circuit = empty Circuit()
    4. For each placement with wire_id >= 0:
           write wire_values[wire_id] into that cell
    5. Set s_mul[0] = 1, other selectors 0
    6. return circuit, public_inputs = [y]
```

**Important:** placements 0 and 1 both read from `wire_values[0]` — copies are satisfied **by construction**, but `check_wire_ids` still validates them.

### Optional: deliberate copy API

Add `Circuit.scatter_wire(wire_id, value, placements)` to make intent obvious in code.

---

## Permutation (concept only — implementation in Lesson 04)

The LambdaClass article’s full copy argument uses a **permutation polynomial** `Z` over a domain. Intuition:

1. List all wire-carrying cells in two orders: **original** and **sorted by wire ID**.
2. A permutation `σ` maps positions so equal wires line up.
3. A polynomial identity proves the same multiset of values appears in both orders.

Lesson 02 implements the **same meaning** with explicit equality loops. Lesson 04 replaces the loop with one polynomial equation.

---

## Data structures to implement

Add new modules (names are suggestions):

### 1. `layout.py` — static circuit geometry

Constants:

- `N = 4`
- `NUM_DATA_COLS = 3`  (a, b, c)
- `NUM_PLACEMENTS = N * NUM_DATA_COLS`  (= 12)

Functions:

- `placement_index(row, col) -> int`
- `row_col_from_placement(p) -> (row, col)`
- `WIRE_IDS: list[int]` length 12 — table from the lesson (`[0,0,1,-1,-1,...]`)

### 2. `copy.py` — copy + public checks

- `value_at_placement(circuit, placement) -> field element`
- `check_wire_ids(circuit) -> bool`
- `check_public_inputs(circuit, public_inputs) -> bool`
- `check_witness(circuit, public_inputs) -> bool` — gates + both copy checks

### 3. Update `witness.py`

Build trace via wire table + `WIRE_IDS` scatter (not only `set_row`).

Keep `set_row` if you like, but `build_witness` must go through the wire-id path so copies are meaningful.

### 4. Update `circuit.py` (optional helpers)

- `set_selector(row, s_mul)`
- `set_data_cell(row, col, value)` where `col in {1,2,3}`

---

## Your task

Implement copy constraint checking on top of Lesson 01:

1. **`layout.py`** with placement indexing and `WIRE_IDS` for the square circuit
2. **`copy.py`** with `check_wire_ids`, `check_public_inputs`, `check_witness`
3. **Refactor `build_witness`** to scatter from `{wire 0: x, wire 1: y}`
4. **Tests** in `tests/test_lesson02.py`

Do **not** implement permutation polynomials yet.

### Correctness properties

| Scenario | Expected |
|----------|----------|
| Valid `x=7, y=49` via `build_witness` | `check_witness` → `True` |
| Gate OK but `a≠b` on row 0 | `check_wire_ids` → `False` |
| `c` correct but `public_inputs[0] ≠ y` | `check_public_inputs` → `False` |
| Padding placements with wire ID `-1` | ignored by copy checker |
| `build_witness` with wrong `y` | still raises before scatter |

### How to simulate a copy failure in tests

Build a valid witness, then manually break equality:

```
circuit, pub = build_witness(7, 49)
circuit.trace[0][1] = 7   # a
circuit.trace[0][2] = 8   # b  ← same wire id, different value
assert check_trace(circuit)      # may still True (56≠49 would fail gate anyway)
# use a=7,b=8,c=56 to show gate passes but copy fails:
circuit.trace[0] = [1, 7, 8, 56]
assert check_trace(circuit)        # True
assert not check_wire_ids(circuit) # False — the lesson's point
```

---

## Run it

```bash
pytest tests/test_lesson01.py -v   # should still pass
pytest tests/test_lesson02.py -v
```

Suggested tests (you write the file):

- `test_valid_witness_passes_copy_checks`
- `test_gate_ok_but_copy_fails`
- `test_public_input_mismatch_fails`
- `test_wire_id_table_covers_active_cells`
- `test_check_witness_implies_check_trace`

---

## Checkpoint

Before Lesson 03, you should be able to:

- [ ] Explain why `a * b = c` does not imply `a = b`
- [ ] Map any `(row, col)` data cell to a placement index `0..11`
- [ ] Write the wire ID table for the square circuit from memory
- [ ] Describe the difference between `check_trace` and `check_witness`
- [ ] Explain what a permutation will replace in Lesson 04

---

## Common mistakes

**Including `s_mul` in copy placements.**  
Selectors are not program wires. Only `a`, `b`, `c`.

**Checking copies on wire ID `-1`.**  
Padding cells should be skipped; otherwise zero-equality chains break.

**Forgetting public input bind.**  
`y` must match both `public_inputs` and the `c` cell on row `0`.

**Hardcoding only `set_row` without wire IDs.**  
Tests can pass Lesson 01 while Lesson 02 never exercises the copy machinery.

---

## How this connects to the full protocol

| Lesson | Meaning |
|--------|---------|
| 01 | Gates hold locally |
| 02 | Wires are consistently wired |
| 03 | Trace columns → polynomials |
| 04 | Permutation polynomial proves copies in one equation |
| 05+ | Quotient, KZG, prove/verify |

You now have the **semantic** copy checks. Lesson 04 will prove the same thing **succinctly**.

---

## Notation summary

| Symbol | Meaning |
|--------|---------|
| `placement` | Flat index `0 .. N*3-1` over data cells |
| `wire_id` | Logical wire label; `-1` = unused |
| `WIRE_IDS[i]` | Which wire owns placement `i` |
| `public_inputs[k]` | Verifier-visible values |

---

## Next lesson (preview)

**Lesson 03 — Polynomials on a domain:** Each trace column becomes a polynomial `A(X), B(X), C(X)` over a multiplicative subgroup of size `N`. Gate equations become a single polynomial identity over all rows at once.

---

## Further reading

- [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) — copy constraints and the permutation argument roadmap