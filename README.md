# PLONK x^2 tutorial (from scratch)

Build a toy PLONK prover and verifier by hand, starting from the simplest useful statement:

> Prove knowledge of a private `x` such that `x * x = y`, where `y` is public.

Working from the initial commit 2f1a3ed03af155a2a919e62577f8c487c2b9df08, the repository contains **lesson documents only**. You write all code yourself.

## Lessons

| # | Topic | Doc |
|---|-------|-----|
| 01 | Execution trace, wires, and gates | [docs/01-execution-trace-and-gates.md](docs/01-execution-trace-and-gates.md) |
| 02 | Copy constraints | [docs/02-copy-constraints.md](docs/02-copy-constraints.md) |
| 03 | Polynomials on a domain | [docs/03-polynomials-on-a-domain.md](docs/03-polynomials-on-a-domain.md) |
| 04 | Permutation argument | [docs/04-permutation-argument.md](docs/04-permutation-argument.md) |
| 05 | Quotient polynomial | [docs/05-quotient-polynomial.md](docs/05-quotient-polynomial.md) |
| 06 | KZG commitments | [docs/06-kzg-commitments.md](docs/06-kzg-commitments.md) |
| 07 | Prove + verify | [docs/07-prove-verify.md](docs/07-prove-verify.md) |

## Module layout

```
plonk-square-tutorial/
├── field.py            # 𝔽_p arithmetic
├── poly.py             # polynomial ops
├── circuit.py          # Circuit trace table
├── layout.py           # WIRE_IDS, placement helpers
├── domain.py           # row + placement domains
├── permutation.py      # copy permutation σ
├── witness.py          # build_witness
├── gates.py            # row-wise gate check (L01)
├── copy_constraints.py # row-wise copy + public (L02)
├── encode.py           # trace → column polynomials (L03)
├── gates_poly.py       # gate polynomial G(X) (L03)
├── copy_poly.py        # copy polynomial C(X) (L04)
├── quotient.py         # constraints, quotients, constraint_bundle (L05)
├── setup.py            # trusted setup τ, commit, open, verify (L06)
├── kzg.py              # commit trace columns + quotients (L06)
├── fiat_shamir.py      # transcript hash → challenge z (L07)
├── prove.py            # prove() + verify() + Proof (L07)
├── verify.py           # check_witness (quotient path default)
├── docs/
└── tests/
```

## How I used with AI with the tutorial

- have AI write the lessons in `docs/` and write all the code yourself to ensure you understand each lesson
- ask AI follow up/clarifying questions as you go through each lesson
- ask AI to write the tests for you too to confirm your implementation is correct after each lesson
- ask for adivce on the code organization/layout after each lesson (since it understands the full scope of the tutorial)

## How to use each lesson

1. Read the background until the concepts feel concrete.
2. Implement the **Your task** section in your own modules.
3. Run the tests described in **Run it**.
4. onward! next lesson!

Lesson 07 completes the tutorial with `prove()` and `verify()`.

Pedagogy follows the trace-and-gates viewpoint in [All you wanted to know about Plonk](https://blog.lambdaclass.com/all-you-wanted-to-know-about-plonk/) by LambdaClass.
