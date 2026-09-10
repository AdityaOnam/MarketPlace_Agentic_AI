# Stage E — the first measured precision/recall, and what it is worth

Run date: **2026-09-10** (re-scored the same day after D-029 fixed two false-positive
mechanisms; the pre-fix numbers are in D-029's result table). Gold file: `docs/evals/gold-labels-dev.csv`, 624 rows,
24 sites × 26 checks, **100% labelled**. Predictions: `harness/out/dev/*.report.json`.
Scorer: `harness/score_dev.py`.

**What may be concluded from these numbers:** that a check, as implemented, fires where a
labeller working from the same frozen snapshots also saw a defect — and how often it fires
where they saw none. **What may not:** that it fires *for the same reason* they did. The
matching rule no longer tests that (see §3). Nor that any of this reproduces — the
reproducibility pass has not run (§5).

## 1. Headline

| Check | Precision | Recall | Clean-site FP | Graded |
| --- | --- | --- | --- | --- |
| CHK-D-001 | 1.00 | 1.00 | 0.00 | 21/24 |
| CHK-D-002 | 0.67 ‡ | 1.00 | 0.06 | 19/24 |
| CHK-D-003 | — | — | — | 6/24 † |
| CHK-D-004 | 0.75 | 1.00 | **0.33** ‡ | 18/24 |
| CHK-D-005 | 1.00 | 1.00 | 0.00 | 17/24 |
| CHK-D-006 | 1.00 | 0.55 | 0.00 | 17/24 |
| CHK-D-007 | 0.94 | 0.94 | **0.50** | 18/24 |
| CHK-D-008 | 1.00 | 0.86 | 0.00 | 18/24 |
| CHK-D-009 | 0.75 | 1.00 | 0.12 | 11/24 |
| CHK-D-010 | 0.50 ‡ | 0.25 ‡ | 0.08 | 17/24 |
| CHK-D-011 | undefined | undefined | 0.00 | 18/24 |
| CHK-D-012 | undefined | undefined | 0.00 | 10/24 |
| CHK-D-013 | 1.00 | 1.00 | 0.00 | 18/24 |
| CHK-D-025 | 1.00 | 0.67 | 0.00 | 19/24 |
| CHK-D-026 | — | — | — | 9/24 † |
| CHK-D-027 | — | — | — | 7/24 † |
| CHK-E-014 | 1.00 | 1.00 | 0.00 | 16/24 |
| CHK-E-015 | undefined | 0.00 ‡ | 0.00 | 19/24 |
| CHK-E-016 | — | — | — | 9/24 † |
| CHK-E-017 | undefined | undefined | 0.00 | 19/24 |
| CHK-E-018 | undefined | undefined | 0.00 | 10/24 |
| CHK-E-019 | — | — | — | 7/24 † |
| CHK-E-020 | undefined | undefined | 0.00 | 19/24 |
| CHK-E-021 | 0.94 | 1.00 | **0.25** ‡ | 19/24 |
| CHK-E-022 | 0.93 | 1.00 | **0.20** | 19/24 |
| CHK-E-024 | 1.00 | 0.50 | 0.00 | 12/24 |

† below the 10-site floor (`EVALS.md` §0) — counts only, never a rate.
`undefined` = no gradable site had that outcome (e.g. no `PRESENT` gold row, so recall has
no denominator). 95% site-level cluster-bootstrap CIs are in the scorer output; several are
wide enough to span the cut line, which is the honest state at n≈20.

**Cut-rule trips (not acted on — see §5):**

- precision < 0.75: `CHK-D-002` ‡, `CHK-D-010` ‡
- recall < 0.40: `CHK-D-010` ‡, `CHK-E-015` ‡
- clean-site FP rate > 0.15: `CHK-D-004` ‡, `CHK-D-007`, `CHK-E-021` ‡, `CHK-E-022`

**Six of the eight trips are marked ‡ — they point at the gold data or the worksheet schema,
not at check code** (D-030, D-031, D-032), and each is written up in
`docs/evals/adjudication-queue.md` with a suggested resolution and no label written. Only
`CHK-D-007` (a measured base-rate effect, deliberately untouched) and `CHK-E-022` are
unexplained trips against code.

‡ **These trips point at the gold data, not the code** (D-031). `CHK-D-002`'s single FP is a
row whose own notes contradict its label; `CHK-D-010`'s recall rests on two German-site rows
that a model labelled by running the same English-only regexes the check has just stopped
using — the measurement was scoring a detector against a copy of itself. All are in
`docs/evals/adjudication-queue.md`, unchanged.

**Three sites are voided** and contribute nothing (D-029): `tailscale.com` and
`www.thalia.de` were audited with zero pages collected; `vitejs.dev` ships 1 frozen snapshot
against 11 audited pages. Grading needs both sides to have seen the same evidence. This is
why `graded` counts are lower than in the first run — the corpus gap is disclosed, not
repaired.

## 2. The first run returned 0.00 for all 26 checks

It was not measuring the tool. The matching rule (`EVALS.md` §2) had three conditions, two
of which compared evidence *text*, and both were unsatisfiable in practice:

- **Verbatim-in-snapshot** rejected **129/129** `PRESENT` rows. No check quotes its source;
  all 26 emit constructed prose (`"robots.txt line 120: Disallow: / applies to Applebot
  (retrieval-time AI crawler)"`). Confirmed by hand on `www.heise.de`: the finding is
  correct and that sentence appears nowhere in the robots.txt, because it describes the file
  rather than quoting it.
- **Evidence Jaccard ≥ 0.6** then rejected **73/129**. Gold records what the labeller read
  (often a quotation, sometimes blank); the check records what it concluded. Two registers,
  no overlap, same claim.

Two locus bugs were found underneath, both previously masked:

- 61 rows failed on **unstripped gold cells** — `canonical_url("https://x/ ")` ≠
  `canonical_url("https://x/")`.
- 60 rows failed because **D-019 rollups are unmatchable by construction**: a defect on 3+
  pages collapses to `locus: {url: null, scope: "site"}` while the labeller records a page.

Full analysis and the decision in **D-028** (`docs/DECISIONS.md`).

## 3. What the loosening cost, measured

Matching is now `check_id` + locus, rollup-aware. Both evidence-text conditions survive as
reported diagnostics, printed under every precision figure:

```
match quality: verbatim-grounded 0/14, evidence-agrees 0/14
```

**Those rates are at or near zero for every check in the corpus.** That is the most
important sentence in this report. The detections land on the right check and the right
page; essentially none of them corroborate against the labeller's own words. Precision here
means *"fired where a defect was flagged"*, not *"and for the same reason"*.

This runs in the direction `PLAN.md` §5 warns about — we author both the checks and the gold
labels, and SWE-Bench+ measured a 3× headline inflation from grader leniency alone. The
mitigation is disclosure, not restoration. Anyone quoting a precision number from this
report is obliged to quote the grounding rate beside it.

## 4. What the numbers suggest (pending §5)

- **Clean-site FP rate is still the weak axis, not recall** — five checks exceed 0.15 after
  D-029, down from seven. The two worst (`CHK-D-006`, `CHK-E-014`, both at 0.67) turned out
  to be defects rather than bad thresholds and are now at 0.00; see §4b.
- **`CHK-D-007`'s FP rate of 0.50 is the base-rate problem already predicted.** Web Data
  Commons measured 44.1% of domains carrying any structured data; "no JSON-LD" is the
  majority condition of the open web. D-022 already capped its severity at `low` for this
  reason; these numbers are that argument arriving as a measurement.
- **`CHK-D-010` was diagnosed in D-031.** Its three evidence-shape detectors are English-only,
  so on qonto.com's German pages it was reporting "no definition, numeric fact or comparison"
  about text carrying `Ab 9 €/Monat` and `2.000+ Integrationen` — a claim about the detector,
  not the page. It now returns `not_determinable` for a declared non-English `lang`; FP
  0.23 → 0.08. It remains recommendation-only and was not tuned further.
- **`CHK-D-001` is fixed and clean** (0.67 → 1.00 precision, D-031): the robots.txt parser did
  pure prefix matching and had no RFC 9309 metacharacter support, so `Allow: /$` — *permit the
  root and nothing else* — was not even collected as a candidate rule, and a `critical`-severity
  check reported bookshop.org as blocking retrieval crawlers it explicitly allows.
- **`CHK-D-004` (0.75 precision / 0.33 FP) was diagnosed in D-030 and is a different animal.**
  One of its four false positives was a real defect (a contact page misfiled as `product`,
  defeating the page-type exclusion — now fixed with a URL fallback). The other three are
  **index/listing pages**, and on inspection the disagreement is with the *gold labels*, not
  the check: the django case turns on whether link-label text counts as content (52 words in
  `<main>`, 577 in `<body>`, labeller recorded 387), and the Smashing rows spot-check two long
  articles that are not among the three 66-word author archives that fired. Those three are in
  `docs/evals/adjudication-queue.md` rather than in a code change. A link-density detector for
  index pages was measured and **rejected** — `page.links` counts site chrome, so the ratio
  just restates thinness and would have suppressed a genuinely thin page.
- **`CHK-E-015` shows recall 0.00 with undefined precision**: it never fired where the
  labeller marked `PRESENT`. The gold corpus is nearly all `ABSENT` for it, so this rests on
  very few positives.
- **Six checks are unmeasurable at this corpus size** (`D-003`, `D-026`, `D-027`, `E-016`,
  `E-019`, plus `D-009`/`E-018` near the line), sitting at or below the 10-site floor —
  worsened by D-029's three voided sites.

## 4b. What the first run's worst two checks turned out to be

`CHK-D-006` and `CHK-E-014` both showed a 0.67 clean-site FP rate in the first scoring run.
Neither was a threshold problem; both were defects, and are fixed (**D-029**):

- **D-006's definition regex accepted exactly one sentence shape** — it required a relative
  clause or one of four participles, and rejected every genuine self-definition in the
  corpus, including *"Hugo is one of the most popular open-source static site generators."*
  Precision 0.57 → **1.00**, FP 0.67 → **0.00**. **Recall fell 0.73 → 0.55** — the widened
  pattern buys precision with recall, and both numbers are reported.
- **D-006's Organization-JSON-LD suppression could not reach the About page.** qonto.com's
  `/en/about` is classified `page_type="product"`, so 13 pages carrying a complete
  Organization block suppressed nothing.
- **E-014 read a hidden `rel="me"` anchor as an unnamed control** — Smashing Magazine's
  Mastodon verification link, `class="hidden"`, empty by design, and the very construct
  `CHK-D-025` asks sites to add. Precision and recall 0.88 → **1.00**, FP 0.67 → **0.00**.

Cut-rule trips fell from 12 checks to 7. `CHK-D-007`'s 0.50 FP rate is deliberately
untouched: Web Data Commons put structured-data adoption at 44.1% of domains, so "no
JSON-LD" is the open web's majority condition and D-022 already capped its severity for that
reason. That is a base rate, not a bug.

## 4c. Diagnosis pass: six checks examined, three defects fixed

Every cut-rule trip from the first run was diagnosed to the same standard (D-029 → D-032).
The split matters more than the totals:

**Genuine check defects, fixed:**

| Check | Defect | Effect |
| --- | --- | --- |
| `CHK-D-006` | definition regex accepted one sentence shape; JSON-LD suppression couldn't reach a misfiled About page | prec 0.57 → 1.00, FP 0.67 → 0.00 |
| `CHK-E-014` | hidden `rel="me"` verification anchor read as an unnamed control | prec/recall 0.88 → 1.00, FP 0.67 → 0.00 |
| `CHK-D-001` | robots.txt parser had no RFC 9309 metacharacter support, so `Allow: /$` was never a candidate rule | prec 0.67 → 1.00, FP 0.05 → 0.00 |
| `CHK-D-004` | page-type exclusion defeated by a misfiled contact page | prec 0.69 → 0.75, FP 0.44 → 0.33 |
| `CHK-D-010` | English-only detectors asserting "no evidence" about German and Greek text | FP 0.23 → 0.08 |

**Not defects — gold data or schema, sent to adjudication unchanged:** `CHK-D-004`'s three
index-page rows, `CHK-D-002`'s bookshop.org row (its own notes contradict its label),
`CHK-D-010`'s two German rows, `CHK-E-015`'s two render-gap rows, `CHK-E-021`'s
smashingmagazine row.

Two findings from this pass deserve to outlive the numbers:

1. **The page-type/archetype classifier is a recurring single point of failure.** It defeated
   `CHK-D-006`'s suppression, `CHK-D-004`'s exclusion, and forced `CHK-E-024` to `N/A` on four
   commercial sites during labelling. Three separate checks, one upstream cause.
2. **One `CHK-D-010` recall drop was circularity, not regression.** Two German-site rows were
   model-authored by running the same English-only regexes the check used, so they agreed with
   a bug; fixing the bug turned them into misses. `EVALS.md` §1's no-model-authored-labels rule
   failing in the concrete.

## 5. What Stage E did not do

- **Reproducibility.** The 8-site test–retest (`EVALS.md` §1) has not run. Apparatus is
  built and the subset is drawn and logged (`harness/retest.py`,
  `docs/evals/retest-log.md`), but the second pass must be re-labelled **by hand, blind,
  ≥ 48 h after the first**. The first pass for the last 11 sites completed 2026-09-10, so
  the earliest valid second pass is **2026-09-12**. Until it runs, **no cut rule in §1 may
  be acted on** — a check is cut on a *reproducible* number, not a single pass.
- **Severity metrics.** Severity-exact rate and mean ordinal severity error (`EVALS.md` §2)
  need a gold severity column the current CSV does not have.
- **Held-out corpus.** Untouched by design; `docs/evals/holdout-log.md` remains empty.
- **Resolve the four `UNMEASURABLE` render checks.** `E-014`'s contrast sub-check, `E-015`'s
  overflow sub-check, `E-016` and `E-018` have no rendered evidence anywhere in this
  harness run — no headless-browser pass exists. Eleven sites carry a partial manual
  substitute; the rest are unmeasured.
