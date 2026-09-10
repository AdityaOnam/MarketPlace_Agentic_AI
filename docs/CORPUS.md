# Website corpus

Development and held-out test sets of real websites. We are graded on unseen sites, so the
corpus exists to do two jobs: give us a defensible measurement of the checks we already
have, and give us an untouched set to test whether they generalize.

**Resized 2026-09-04 under D-017**, from 129 sites to 54. The largest single cut is the dev
set (60 → 24), and the reason is that its original size was justified by a job that no
longer exists: 60 sites were sized for *deriving* checks. Phase 3 authored all of them. What
remains is measurement, whose floor is D-010's own labelling minimum of 24.

**Grown back to 57 on 2026-09-04 under D-026**: the negative-control set went 12 → 15 when
its missing seventh dimension (off-site identity anchors) was finally added. That is the
only movement since D-017.

| Set | Size | Purpose | Hygiene rule |
| --- | --- | --- | --- |
| **Dev** | 24 | Gold-labelled. Source of the headline precision, recall and clean-site FP numbers | Look at freely |
| **Held-out** | 12 | Measure generalization | Selected and sealed **before the harness is built**. 3 logged looks, total |
| **Negative control** | 15 | Catastrophic-FP screen | Each site curated clean on one named dimension. Counts, never rates |
| **Adversarial / edge** | 6 | Graceful degradation | Must not crash, must emit valid JSON |

## 0. Design commitments

1. **The unit of analysis is the site, not the finding.** Findings within a site are
   correlated; all intervals carry a site-level clustering correction.
2. **Every eval run is against a frozen local snapshot we captured ourselves** — raw HTTP
   response, headers, and robots.txt. Per D-015 there is no rendered-DOM half any more: the
   grading sandbox has no headless browser, so capturing a rendered DOM would let us
   measure a code path that never runs when it counts. The Wayback Machine is **not** used
   as a fixture source.
3. **Dev and held-out are drawn by the same procedure from the same strata**, in one pass,
   before either is opened.
4. **No site name, brand, or selector from this corpus may appear in any shipped `SKILL.md`
   or script.**
5. **The sample is chosen, not sampled from a frame.** D-017 cut the pinned Tranco /
   Common Crawl frames as bureaucracy at n=54. The selection rule and the rejection log are
   recorded instead, and every number derived from this corpus is reported as performance
   on a chosen sample rather than as a population rate.

## 1. Dev corpus

**24 sites.** Stratified 6 × 4: the six archetypes the collector can label, four sites each.

`ecommerce` · `documentation` · `saas_marketing` · `news_editorial` · `local_business` ·
`brochure`

Within each archetype of 4: 1 head (well-known), 2 mid, 1 long-tail. Archetype balance is
prioritised over popularity balance, because `archetype` drives suppression rules and is
therefore the stratum whose errors propagate (see §6).

**Secondary balance constraints**, scaled from the 60-site version:

- ≥ 6 JS-heavy sites (where static HTML plausibly under-represents the page)
- ≥ 5 non-English sites, ≥ 2 languages, ≥ 1 non-Latin script
- ≥ 4 sites outside US/UK/EU
- Max 2 sites on any single CMS/platform

**Procedure.** Walk the candidate list in a recorded order; fetch the homepage; label the
archetype by hand; fill quotas; record every rejection with its reason. Freeze by snapshot.
The rule, the declared selection bias and the rejection log are in
`docs/evals/corpus-selection.md`; the sets themselves live in the git-ignored harness at
`harness/corpus/*.csv`, because a corpus list is site-specific and must never enter the
submission zip (§8).

## 2. Held-out corpus

**12 sites**, drawn in the same pass as dev, maintaining archetype proportions (2 per
archetype).

- Stored separately in `corpus/heldout.csv`, not opened during development.
- **Total run budget: 3 looks**, pre-declared, each logged in `docs/evals/holdout-log.md`.
- Any inspection of a held-out site's pages or per-finding results beyond the aggregate
  metric converts that site to dev, permanently.
- **Selected before the harness exists.** This ordering is the only defence against the
  failure mode a hand-picked held-out set is prone to — unconsciously choosing sites we
  expect to do well on. Selection cannot be informed by results that do not exist yet.

**What 12 sites buy:** roughly ±15 pp on precision. It detects a collapse, not a drift.

## 3. Negative-control set

**15 sites**, two per dimension across the seven check families with the most
false-positive exposure, plus one spare on `offsite_identity`. Each site is verified clean
on its named dimension *before* the audit runs — perfect structured data, no accessibility
violations, explicitly evergreen content, and so on.

| Dimension | Checks screened | Sites |
| --- | --- | --- |
| `crawl_access` | `CHK-D-001`, `CHK-D-002` | 2 |
| `render_extractability` | `CHK-D-003`/`004`/`005`/`009`/`010`/`011`/`013`, `CHK-E-019` | 2 |
| `entity_identity` | `CHK-D-006`/`007`/`008` (+ the three anchor checks below) | 2 |
| `offsite_identity` | `CHK-D-025`, `CHK-D-026`, `CHK-D-027` | 3 |
| `accessibility` | `CHK-E-014`, `CHK-E-017`, `CHK-E-020`, `CHK-E-022` | 2 |
| `mobile_layout` | `CHK-E-015`, `CHK-E-016`, `CHK-E-018`, `CHK-E-021` | 2 |
| `freshness_trust` | `CHK-D-012`, `CHK-E-024` | 2 |

`offsite_identity` was added **2026-09-04 under D-026**, closing a gap R-5's follow-on note
had flagged when the anchor checks were authored and that survived D-017's redesign
unnoticed. It deliberately overlaps `entity_identity` on the three anchor checks — the
`entity_identity` rows were curated on on-page markup *and* declared profile links, so they
stay screened on all six — but only the `offsite_identity` rows were verified against the
anchors' actual resolution before the audit ran. The map lives in
`harness/score_screen.py`'s `DIMENSIONS`.

It carries **three** rows rather than two, breaking the set's otherwise uniform
2-per-dimension shape. That is deliberate and recorded rather than smoothed away: the
pre-screen found qualifying candidates so scarce (8 of 11 reachable well-known sites declare
no `sameAs` at all) that a spare is worth more than the symmetry. It also gives this one
dimension 3 observations per check-cell instead of 1–2, so any count read off it is read
against a slightly larger denominator than the rest — §3's "counts, never rates" rule is
what keeps that from mattering.

**Read it as a screen.** With 1–3 observations per check-dimension cell it can catch a check
that fires on every clean site; it cannot establish a rate. A firing **inside** a site's
curated dimension is a hard defect. A firing **outside** it is an unlabelled finding and
goes to the adjudication queue — counting it as a false positive would be counting an
absence of evidence.

Priority suspects, already flagged in the design: **CHK-D-006 / D-010 / D-011** (heuristic
text patterns, likeliest to misfire on prose styles the regexes were not written for), and
the **archetype classifier** itself (§6).

## 4. Adversarial / edge set

**6 sites**, one per condition: JS-only SPA · robots.txt disallowing `/` · single-page site
· very large site · non-Latin script · redirect chain.

Cut from the original 12: the four bot-blocking conditions (cloaking, challenge pages,
paywall, parked domain) and `Crawl-delay`. Per `OFFICIALS-QA.md` §2.2 the graders will use
sites that do not block the agent, so these cost snapshot effort against a scenario that
will not be graded. The handling code stays — it is written, it is cheap, and robustness
reads well on static review — it just stops consuming corpus budget.

**Requirement:** terminate within 5 minutes, emit schema-valid JSON, degrade explicitly
(`not_determinable`, `degraded_stages[]`, or an omitted check) rather than inferring.

## 5. Snapshotting and reproducibility

Live sites change; every eval runs against a capture.

- Raw HTTP response: status, headers, body, per URL.
- robots.txt as fetched, with its status code.
- Capture metadata: timestamp, User-Agent, redirect chain.
- Content-addressed by SHA-256 of the response body.
- Max 20 pages per site, matching the collector's own `max_static_pages`. (The old 100-page
  cap captured pages the collector would never sample.)
- Snapshots are git-ignored and never enter the submission zip.

## 6. The archetype classifier is measured separately, and first

`classify_archetype` is not just another check — it is an input to the suppression rules,
so **its errors propagate rather than staying local**: a site labelled `saas_marketing`
when it is `ecommerce` activates suppression written for a different kind of site, and
contaminates every downstream number for that site.

It is therefore measured on its own, before the detection metrics are computed, across the
**45 non-held-out sites** (dev + negative control + adversarial; 42 before D-026 grew the
negative-control set). Held-out is excluded:
running it there would spend one of three looks before the set is used for its actual
purpose, and archetype accuracy is not what those looks are for. Measured as: predicted label vs hand-assigned label, reported as accuracy plus a full
confusion matrix. `unknown` is scored as a correct abstention when no rule should have
matched, and as an error when a rule should have.

## 7. Sample size and confidence

- Precision and recall as **Wilson score intervals**, never Wald.
- Intervals corrected for site-level clustering via a design effect.
- 24 dev sites → precision ≈ ±10 pp, recall ≈ ±12 pp. 12 held-out → ≈ ±15 pp.
- Below 10 sites in a stratum, report **counts, not rates**.
- The ρ ≈ 0.20 intra-cluster correlation assumed in this arithmetic is **measurable as a
  by-product of Phase 4** and should be reported once measured, rather than left assumed.

## 8. Shipping constraints

The final ≤ 50 MB zip contains **only** the skills and generic reference data. It contains
nothing derived from a specific site: no snapshots, no corpus lists, no site names. The
harness that drives the corpus lives outside the marketplace directory and is git-ignored.
