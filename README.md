# FRE-GY-9743-Assignments-2026fall
Assignments for NYU, FRE-GY 9743, Fall 2026.

## HW6 — implementation notes

The six `#TODO` blocks (RFR swap and overnight basis swap legs, their factory
builders, and their valuation engines) are implemented. Documentation lives in
[`docs/`](docs/):

- [docs/hw6-implementation.md](docs/hw6-implementation.md) — the maths, each design
  decision and why, the results on the notebook inputs, and the verification.
- [docs/product-architecture.md](docs/product-architecture.md) — how products,
  streams, engines, conventions and the factory fit together, plus a recipe for
  adding the next product.
- [docs/code-reuse.md](docs/code-reuse.md) — audit of earlier work: nothing needed
  copying, and how equivalence with the shipped solutions was verified.

Theoretical background: [`docs/stochastic_calculus_and_yield_curve_calibration.md`](../../docs/stochastic_calculus_and_yield_curve_calibration.md) (§7).

Run the regression tests with:

```bash
python tests/test_interest_rate_products.py
```
