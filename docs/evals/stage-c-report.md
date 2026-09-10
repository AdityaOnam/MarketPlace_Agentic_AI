# Stage C — resolving what Stage B found

Run 2026-09-04, entirely offline against `harness/snapshots/` (already-fetched fixtures) and
the existing `harness/out/dev`, `harness/out/negative` results. No live site was contacted
in this pass. Closes the five checks `docs/evals/stage-b-report.md` §3 flagged and left
unresolved, plus the archetype-classifier accuracy escalated there as "D-021" without a
written decision. Full mechanism-level writeups: **D-021**, **D-022** in `docs/DECISIONS.md`.

**What may be concluded from these numbers:** that a check misfires, and why, and whether a
fix removes it — same caveat as Stage B. No gold labels exist yet; these are still not a
precision or recall *rate*. That is Stage D.

## 1. Headline

| | Before Stage C | After |
| --- | --- | --- |
| Total findings, 12 negative-control sites (10 replay offline; see §4) | 107–112 | **88** |
| Hard defects (fire inside a site's own curated-clean dimension) | 7/12 | **5/10** |
| Archetype confident-wrong labels (of 34 dev+negative sites) | 5 | **1** |
| Archetype raw accuracy | 17–22% | 21% (unchanged in kind — see D-021) |
| Harness crashes | 0 | 0 |
| Schema conformance | 36/36 | 34/34 that ran |

The archetype row is the one worth reading carefully: raw accuracy barely moved, and that
is the intended result, not a shortfall. Four of the five confident-wrong labels flipped to
`unknown` (safe by design — it suppresses archetype-conditioned checks rather than
activating the wrong ones), not to the correct answer. `unknown` costs capability;
confident-wrong costs correctness. This pass traded the second for the first.

## 2. A bug that had been silently killing every JSON-LD signal

The real story of the archetype fixes is one bug, not five unrelated ones. `harness/collect.py`
read `structured_data.get("types")` and `structured_data.get("sameAs")` — keys the shipped
`extract_page._extract_structured_data` has never produced (the real shape is
`{"json_ld": [{"type", "raw", "fields_present"}], ...}`). Both reads silently returned `[]`
on every page of every site for the entire Stage B/B' run. That is three signals dead at
once: JSON-LD-driven `page_type` labelling (Product/Offer/Article/FAQPage never fired from
structured data, only from path/title regexes), the archetype `is_local_business` rule
(literally unreachable), and CHK-D-025/026's declared `sameAs` discovery.

This was a **harness bug, not a shipped-skill bug** — `page_classifier.py` and
`entity_identity_checks.py` read the correct shape throughout; only the harness's own glue
code had the wrong key names. Fixed with `_json_ld_types`/`_json_ld_entities` helpers in
`harness/collect.py`, normalising `@type` string-or-array the same way
`entity_identity_checks._org_type_names` already does.

## 3. Four more mechanisms, each general and independently confirmed

- **`has_price` was a raw-HTML regex**, matching any `"price"`/`"priceCurrency"` JSON key
  anywhere on the page — ad-tech and analytics payloads included. Fired at 0.6 confidence on
  two news/editorial sites with zero commerce signal. Now reads `price` from Product/Offer
  JSON-LD entities only.
- **`product_count >= 5` had no price corroboration.** heise.de's *free* software-download
  catalogue (`/download/product/<name>`) satisfied the path pattern alone and was labelled
  `ecommerce` at 0.9 confidence. Now requires `has_offer_price` too.
- **The `pricing` rule matched the bare word "plans"** anywhere in path or title —
  false-positiving a UK government page about rights-of-way improvement *plans*. Anchored to
  a path segment, the same fix already applied to `documentation` in Stage B'.
- **A sitemap listing media URLs could flip a site's archetype.** blog.cloudflare.com's
  sitemap listed 95 image URLs under `/_emdash/api/media/file/*.png`; `/api/` matched the
  `documentation` path rule and alone flipped the site from `news_editorial` to
  `documentation` at 0.9 confidence. `page_classifier.py` gains an `asset` page_type
  (non-HTML extensions, checked first), excluded from sampling, from the inventory cap, and
  from every archetype proportion.

## 4. The five flagged checks

| Check | Verdict | Why |
| --- | --- | --- |
| `CHK-E-014` (WCAG failures) | **Accepted as-is** | Matches the cited 95.9%-prevalence base rate almost exactly; not a bug |
| `CHK-E-022` (no h1/main/heading) | **Accepted as-is, hand-verified** | Traced gohugo.io's firing to the actual frozen HTML: genuinely no `<h1`. Homepage (which has one) correctly does not fire |
| `CHK-D-007` (no Organization JSON-LD) | **Severity capped medium → low** | WDC 2024: only 44.1% of domains carry any structured data at all — absence is the majority condition, not a differentiator (D-009 enforced in code) |
| `CHK-D-004` (thin content, <200 words) | **Excludes `home` page type** | A homepage's job is framing, not comprehensive information; was flagging gohugo.io's 197-word hero-plus-links homepage |
| `CHK-E-021` (images without dimensions) | **Demoted to `recommendations[]`** | 26/34 sites, `THEORETICAL` strength, no perception research behind CLS (already stated in `PLAN.md` §5) |
| `CHK-D-010` (no definition/fact/comparison) | **Demoted to `recommendations[]`** | 17/34 sites including MDN and Django's own docs — the 3-pattern regex proxy is too narrow to assert as a confirmed defect |

Two of six were left unchanged on purpose: the reasoning for *not* touching `CHK-E-014` and
`CHK-E-022` rests on the same base-rate evidence as the four that did change, applied in the
opposite direction. All four changes are score-lowering and need no defence under the
asymmetric-justification rule.

## 5. Composition tests (`EVALS.md` §7)

- **Bundle-sufficiency: holds structurally.** Grepped all four analyser scripts for any
  network import (`urllib`, `requests`, `http.client`, `socket`, `fetcher.`, `.fetch(`) —
  zero matches. Each analyser runs to completion on the bundle alone; this was already
  guaranteed by the collector-boundary architecture (D-013) and is now checked, not just
  argued.
- **Merge test: not run.** The literal test (merge `render-extractability-audit` and
  `engagement-defect-audit`'s `SKILL.md`/`references/`/manifest entries and re-run) is a
  marketplace-structure change, not a code fix, and wasn't attempted this pass. A partial,
  weaker observation: since this harness already calls all four analysers as plain Python
  functions over one bundle with no skill-boundary enforcement at execution time, precision,
  conformance and runtime are *mechanically* identical regardless of which skill folder a
  check's code lives in — that much is close to tautological given the architecture, not a
  result of running anything. It says nothing about whether an invoking agent's behaviour
  differs when reading one merged `SKILL.md` versus two, which is the part the real merge
  test is for. Left for a deliberate pass.
- **Leave-one-skill-out ablation: run (2026-09-04, post-adversarial), against the full
  36-site dev+negative corpus via `harness/ablation.py`.** Two results:
  1. **The trivial disjoint-partition count**, as predicted: removing each skill drops its
     owned checks' findings+recommendations — `engagement-defect-audit` 47.4% of the
     corpus total, `render-extractability-audit` 28.3%, `entity-identity-audit` 22.1%,
     `crawl-access-audit` 2.2% (it owns only 2 checks, and root-level robots blocks are
     rare in this corpus). Reported per `EVALS.md` §7, not gated — `ARCHITECTURE.md` §7
     already said any disjoint partition would pass this.
  2. **The sharper test**: does removing the skill that owns `CHK-D-003`
     (`render-extractability-audit`) actually change what `CHK-E-019`
     (`engagement-defect-audit`) does anywhere in the corpus — i.e. is rule O-1
     load-bearing? **On all 36 real sites, no.** `CHK-D-003` and `CHK-E-019` never both
     fired `present` on the same site, so O-1's suppression branch never activated. This
     matches D-016's finding on 5 hand-built synthetic scenarios, now confirmed on the real
     corpus rather than constructed cases — and it is evidence *against* the composition
     argument, not for it: the one genuine cross-skill rule the orchestrator has has zero
     measured effect so far. This does not settle the question — the merge test below is
     still the deciding one — but it is the first real-corpus data point on it, and it
     points the same direction the merge test would need to overturn.

## 6. Runtime: first real measurement, small sample

`stage-b-report.md` §5 left this outstanding: offline replay only bounds analysis cost, not
fetch cost under the real 1.0 s per-host politeness gap. Ran 5 sites live with `--refresh`
(forcing fresh fetches, 0 cache hits, 229 real network requests total), picked to span size:
a small blog, a small local-business site, a mid-size multilingual SaaS site, a large
documentation site, and a large news site.

| Site | Wall-clock |
| --- | --- |
| franklinbbq.com | 35.9s |
| docs.python.org | 41.7s |
| sive.rs | 46.1s |
| qonto.com | 59.1s |
| www.heise.de | 72.4s |

Median (p50) 46.1s, max 72.4s — both far under the 150s/270s p50/p95 targets and the 300s
hard cap. **This is 5 sites, not a rate** — per `EVALS.md`'s own rule, a metric computed on
fewer than 10 sites is reported as a raw count, not a percentile with confidence bounds.
None of the 5 declared a `Crawl-delay` in `robots.txt` (all `crawl-delay=None`), so this
sample does not exercise the tail case `stage-b-report.md` recorded earlier — one live
collection under a declared long `Crawl-delay` took 1033s. **The 300s cap is a per-run
budget the harness enforces by declaring stages abandoned, not a ceiling this measurement
tests** — a site with a long crawl-delay would hit that budget logic rather than a
1033s wall-clock in the real submission path. A larger, more deliberately adversarial
runtime sample (including a long-`Crawl-delay` site) is the natural next step if runtime
becomes a concern, not attempted here.

## 6b. Set stability (k=3, 5 sites, live)

`EVALS.md` §5: "measured once at k=3 on 5 sites, reported as counts of sites whose
(check_id, locus) set is identical across all three runs. No threshold." Ran the same
5-site sample as §6, live, three times each (`harness/stability.py`), comparing the
`(check_id, locus)` set of `findings[] + recommendations[]` per run.

| Site | Runs | Result |
| --- | --- | --- |
| sive.rs | 3, 3, 3 pairs | STABLE |
| franklinbbq.com | 8, 8, 8 pairs | STABLE |
| qonto.com | 9, 9, 9 pairs | STABLE |
| docs.python.org | 9, 9, 9 pairs | STABLE |
| www.heise.de | 17, 17, 17 pairs | STABLE |

**5/5 stable.** None of the three named instability sources (`PLAN.md` §7: evergreen-vs-
time-sensitive classification, archetype labelling, suggested-action wording) produced a
visible difference on this sample — real page content also didn't drift enough between the
three live fetches (spaced only by fetch/processing time, not days) to change any check's
verdict. This is a small, same-session sample; it says nothing about drift over longer
time horizons (a page edited between fetches days apart) or a larger site set.

## 7. What Stage C did not do

- **No gold labels.** Still Stage D, still unstarted, still requires a single human labeller
  per `EVALS.md` §1 — a model may find disagreements, never author or verify a label.
- **Adversarial set not run.** Only `en.wikipedia.org` of the 6 adversarial domains has a
  local snapshot; the other 5 need a live fetch, out of this pass's local-only scope.
- **Two negative-control sites need a live re-fetch.** `creativecommons.org` and
  `blog.cloudflare.com` now select a different (previously-unfetched) page under the
  corrected sampler and return `OfflineMiss` on replay. `blog.cloudflare.com`'s underlying
  fix was verified directly against its existing bundle instead (§2); `creativecommons.org`
  was not independently re-verified this pass.
- **Held-out untouched**, 3 looks intact.
- **R-1 (hand-verification of one source per check) remains open** and still blocks ship.
- **No further `classify_page_type` path-pattern tuning.** The dominant remaining cause of
  `unknown` (URLs like `/templates/`, `/getting-started/` not matching the `documentation`
  pattern) was identified in Stage B' and deliberately left alone — fixing it against these
  same 36 sites would be corpus-fitting. `unknown` is safe; this is a capability gap, not a
  correctness one.
