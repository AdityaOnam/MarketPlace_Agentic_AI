# Test-retest log (EVALS.md SS1)

Worksheet emitted: **2026-09-10 17:42 UTC**
Selection: seeded (`SELECTION_SEED = 20260910`), 8 of 24 dev sites, fixed and
recorded here so the subset cannot be re-drawn until it flatters the result.

## The 8 sites

1. `bookshop.org`
2. `docs.djangoproject.com`
3. `docs.python.org`
4. `gohugo.io`
5. `overreacted.io`
6. `shop.fsf.org`
7. `www.pizzeriabianco.com`
8. `www.tartinebakery.com`

## Protocol

1. Wait **at least 48 h** from the first pass before starting.
2. Fill `docs/evals/retest-worksheet.csv` **without opening
   `docs/evals/gold-labels-dev.csv`**. The worksheet ships blank on purpose; the blinding is
   the measurement.
3. Label from the frozen snapshots in `dist/gold-labelling-kit/snapshots/<site>/`, the same
   source as pass 1.
4. Run `python harness/retest.py --score`.

## Result

_Not yet run._ Fill in after `--score`: per-check alpha, checks below 0.67, and the
date of the second pass.
