# Lesson 01 — Execution trace, wires, and gates

## What you will learn

How PLONK turns a computation into a **table of wire values** plus **gate polynomials** that must equal zero. By the end of this lesson you will:

- Understand what a **wire** is and how it differs from a **row** or **column**
- Lay out a tiny circuit for `x * x = y`
- Assign a **witness** (private values) into the table
- Check that every **active gate** is satisfied

This is the first layer of PLONK described in [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/): before polynomials, permutations, or KZG, the prover must simply show that the arithmetic written in the table is correct.

No cryptography in this lesson — only data structures and algebra.

---

## Big picture (where this lesson sits)

A PLONK proof system has several stages. You will build them over multiple lessons:

```
Lesson 01   Trace + gates          ← you are here
Lesson 02   Copy constraints       (same wire in two cells must match)
Lesson 03   Polynomials on a domain
Lesson 04   Permutation argument
Lesson 05   Quotient polynomial
Lesson 06   KZG commitments
Lesson 07   Prove + verify
```

Today you implement the **clearest possible** version of step one: “does this table satisfy the gate equations?”

---

## Vocabulary

### Statement

The **statement** is what the verifier cares about publicly.

- **Public input:** `y` (everyone agrees on this number)
- **Private witness:** `x` (only the prover knows this; must stay hidden later)

The prover claims: “I know an `x` such that `x * x = y`.”

### Wire

A **wire** is a single value in the computation — like a variable in a program. Examples: `x`, `y`, or an intermediate result.

In PLONK, a wire is **not** the same thing as a table cell yet. One logical wire may appear in several cells once copy constraints exist (Lesson 02). For today, each important value gets its own wire index.

### Execution trace

The **execution trace** is a rectangular table:

- **Rows** = time steps (row `0`, row `1`, …)
- **Columns** = places where wire values live for that row

Following the LambdaClass article, think of a **program run** frozen into a spreadsheet. Each cell holds a field element (for now: ordinary integers mod a prime `p`).

### Gate

A **gate** is one arithmetic rule that must hold on some row(s). PLONK supports **custom gates**: each gate type is a polynomial that should equal **zero** when that gate is active.

The famous multiplication gate on one row is:

```
left * right = output
```

Written as a polynomial (must equal zero):

```
left * right - output = 0
```

### Selector

Not every row uses every gate. A **selector** is `0` or `1`:

- `0` → ignore this gate on this row (no constraint)
- `1` → enforce the gate on this row

For a single multiplication on row `0`, the selector column looks like `[1, 0, 0, …]`.

Selectors are how PLONK packs many gate types into one uniform grid.

### Witness

The **witness** is the full assignment of values to every cell in the trace (including private data). The prover knows the witness; the verifier must not learn private parts.

---

## Choose a field

All arithmetic is modulo a prime `p`.

For learning, use a small prime with room for squaring **and** a multiplicative subgroup of order `N = 4` (needed from Lesson 03 onward):

```
p = 1000033   (prime; 4 | (p - 1))
```

Lesson 03 uses `ω` with `ω^4 = 1` and domain `H = {1, ω, ω², ω³}`. Any prime with `4 | (p - 1)` works; this one stays close in size to older drafts of the tutorial.

**Your code** needs:

- `add(a, b)`, `sub(a, b)`, `mul(a, b)`, `mod(n)` — all mod `p`
- Comparison of values as integers in `[0, p)`

Do not use floating point. Every wire value lives in this field.

---

## Our circuit: `x * x = y`

We use **three logical wires**:

| Wire index | Name | Role |
|------------|------|------|
| `w0` | `x_lhs` | Left input of multiplication |
| `w1` | `x_rhs` | Right input of multiplication |
| `w2` | `y` | Output (public) |

Because we want `x * x`, the same secret `x` is placed on both `w0` and `w1`. Lesson 02 will explain how PLONK **proves** those two cells are really the same value; today you **assign** them equal by construction.

### Trace size

PLONK works on a domain whose size is a power of two. The trace has `N` rows where `N = 2^k`.

For one multiplication gate, you only need **one active row**, but pad to a power of two:

```
N = 4   (k = 2)
```

Rows `1..3` are **padding**: selectors are `0`, so gates are turned off.

### Column layout

Use one column per wire value at each row (the simplest mental model from the LambdaClass trace picture):

| Column | Holds |
|--------|--------|
| `a` | left input |
| `b` | right input |
| `c` | output |
| `s_mul` | multiplication selector |

**Table for witness `x = 7`, `y = 49`:**

| row | `s_mul` | `a` | `b` | `c` |
|-----|---------|-----|-----|-----|
| 0 | 1 | 7 | 7 | 49 |
| 1 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 |

Padding values on inactive rows can be zero. Because `s_mul = 0`, the gate polynomial is **not enforced** on those rows.

### Public input

Mark `y` as **public**: the verifier will see `49`. The value `x` appears only in columns `a` and `b` on row `0` — that stays private in your witness structure for now.

Store public inputs separately in your code, e.g. `public_inputs = [y]`.

---

## Gate equation (the heart of PLONK)

For each row `i`, let `a_i`, `b_i`, `c_i`, `s_i` be the cell values in that row.

The multiplication gate polynomial is:

```
G_i = s_i * (a_i * b_i - c_i)
```

**Requirement:** `G_i = 0` in the field for **every** row `i`.

Check by hand for row `0`:

```
G_0 = 1 * (7 * 7 - 49) = 0   ✓
```

For row `1`:

```
G_1 = 0 * (anything) = 0   ✓   (gate disabled)
```

This is the PLONK pattern: **`selector * (constraint polynomial)`**. The selector is what makes the gate **custom** and **sparse** across rows.

---

## What “Plonkish” means at this stage

In the LambdaClass article, PLONK’s power is **custom gates**: you are not locked into only `ADD` and `MUL` chips from an old constraint system. You write a polynomial (here `a*b - c`) and a selector bitmap that says where it applies.

Our entire “circuit” is one custom multiplication gate on row `0`. That is enough for `x * x = y`.

---

## Data structures to implement

Create a small Python package (or language of your choice) with the following pieces. **You choose file names**; suggested roles:

### 1. `field.py` — modular arithmetic

Functions mod `p`, as above.

### 2. `trace.py` — the execution trace

Represent the table as arrays of length `N`:

```text
a:       list of N field elements
b:       list of N field elements
c:       list of N field elements
s_mul:   list of N field elements (0 or 1)
```

Provide:

- `Trace.new_empty(n_rows)` — zeroed padding
- `Trace.set_mul_row(row, x, y)` — set `s_mul[row]=1`, `a[row]=x`, `b[row]=x`, `c[row]=y`

### 3. `circuit.py` — circuit parameters

Immutable description of the **shape** (not the secret numbers):

- `n_rows` (must be power of 2)
- which gate types exist (for now: only `mul`)
- which row the multiplication is on (row `0`)

### 4. `witness.py` — build a trace from secrets

```text
build_witness(x: int, y: int) -> (Trace, public_inputs)
```

Steps:

1. Check `y == x * x` (mod `p`). If not, raise an error — invalid witness.
2. Fill row `0` with the multiplication.
3. Leave other rows padded with selector `0`.
4. Return `public_inputs = [y]`.

### 5. `gates.py` — local constraint checker

```text
gate_mul(a, b, c, s) -> field element
    return s * (a*b - c)   (all mod p)

check_trace(trace) -> bool
    for each row i:
        if gate_mul(a[i], b[i], c[i], s_mul[i]) != 0:
            return False
    return True
```

This function is your **Lesson 01 verifier**. It does not prove knowledge yet; it only tests whether the table satisfies the gate polynomials.

---

## Your task

Implement the modules above from scratch:

1. **Field arithmetic** mod `p`
2. **Trace** data structure with `N = 4` rows
3. **`build_witness(x, y)`** for the square circuit
4. **`check_trace(trace)`** using `s * (a*b - c)` per row
5. **Tests** (see below)

Do **not** implement polynomials, KZG, or hashes in this lesson.

### Correctness properties to enforce in code

| Check | Expected |
|-------|----------|
| Valid `x=7`, `y=49` | `check_trace` → `True` |
| Valid `x=3`, `y=9` | `check_trace` → `True` |
| Wrong `y` for same trace build | `build_witness` should reject before building |
| Manually corrupt `c[0]` after build | `check_trace` → `False` |
| Padding rows with `s_mul=0` | still `True` even if `a,b,c` garbage on those rows |

### Optional stretch

Add a second gate type stub in comments only: `s_add * (a + b - c)` on another row, to see how PLONK stacks multiple custom gates. Do not require it for tests.

---

## Run it

From your project root (after you add `pytest` or similar):

```bash
pytest tests/test_lesson01.py -v
```

Suggested tests (you write the file):

- `test_valid_square_7_49`
- `test_valid_square_3_9`
- `test_invalid_witness_wrong_y`
- `test_corrupted_output_fails`
- `test_padding_rows_do_not_matter`

---

## Checkpoint

Before Lesson 02, you should be able to:

- [ ] Draw the `N = 4` table on paper and label `a`, `b`, `c`, `s_mul`
- [ ] Explain why inactive rows do not constrain the witness
- [ ] Write the gate polynomial for row `i` from memory
- [ ] Explain the difference between **wire**, **witness**, and **public input**
- [ ] Run `check_trace` successfully on `x = 7`, `y = 49`

---

## Common mistakes

**Using the same column for both inputs without planning copy constraints.**  
Today you manually set `a` and `b` to the same `x`. In a real PLONK prover, those may be different cells linked in Lesson 02.

**Forgetting selectors on padding rows.**  
If `s_mul` is `1` on padding rows, garbage values must satisfy the multiplication — usually impossible. Padding rows must have `s_mul = 0`.

**Checking only row 0.**  
`check_trace` must loop **all** `N` rows. PLONK’s verifier will eventually enforce every row via polynomials.

**Treating `y` as private in the data model.**  
Keep `public_inputs` explicit even if `y` also appears in column `c`. Later lessons wire public inputs into the protocol.

---

## How this connects to the full PLONK protocol

The LambdaClass article’s pipeline is:

1. **Compile** program → gates + trace layout (this lesson)
2. **Prove** wires are consistent (copy constraints / permutation — Lesson 02+)
3. **Encode** trace columns as polynomials on a multiplicative subgroup
4. **Commit** with KZG and prove openings

You built step 1 in concrete code. Steps 2–4 turn “the table is correct” into a short cryptographic proof.

---

## Notation for later lessons

| Symbol | Meaning |
|--------|---------|
| `N` | Number of trace rows (`2^k`) |
| `a_i, b_i, c_i` | Cell values on row `i` |
| `s_i` | Selector on row `i` |
| `w0, w1, w2` | Logical wire indices |
| `p` | Field modulus |
| `G_i` | Gate evaluation on row `i` |

---

## Next lesson (preview)

**Lesson 02 — Copy constraints:** PLONK proves two cells hold the **same wire value** without copying the secret everywhere by hand. You will assign `x` once and reference it twice using wire IDs and a **permutation** (the next piece from the LambdaClass article).

---

## Further reading

- [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) — trace, custom gates, and the full protocol roadmap