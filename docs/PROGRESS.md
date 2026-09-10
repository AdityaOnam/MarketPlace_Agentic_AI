# Progress

Living state of the Round 3 build. Updated at the end of every meaningful chunk of work
(see the `project-flow` skill). Newest notes at the top of each list.

**Current phase:** 4 — Corpus and harness, in progress. Stages A, A′, B, B′, C are done
(see `docs/evals/stage-b-report.md`, `docs/evals/stage-c-report.md`, and **D-017…D-026** in
`docs/DECISIONS.md`). The adversarial set (6 sites) has run live, both composition tests
from `EVALS.md` §7 have run (leave-one-skill-out ablation and the merge test), and the
marketplace is now **five skills, not six** — `render-extractability-audit` and
`engagement-defect-audit` merged into `content-engagement-audit` on real evidence (D-025).
**R-1 (source hand-verification) closed 2026-09-09 (D-027)** — a human worked the 14-source
`in_minimum_set` in `docs/evals/r1-verification-worksheet.csv`, judging each cited source
against the ledger's actual claim. `CHK-D-011` and `CHK-D-013` had zero surviving support
and were demoted to `recommendations[]` rather than cut; `CHK-D-001/002`'s crawler-taxonomy
citation gap was flagged, not fixed (see `DECISIONS.md`).

**Stage D closed 2026-09-10 at 624/624 rows** (24 sites × 26 checks), and **Stage E scored
it the same day** — the project's first measured precision/recall:
`docs/evals/stage-e-report.md`. Getting there required **D-028**: the first run returned
precision 0.00 / recall 0.00 for *all 26 checks* because both of the matching rule's
evidence-text conditions were unsatisfiable by construction (the checks describe their
evidence, the labeller quotes hers), with two locus bugs underneath. Matching is now
`check_id` + locus; the retired conditions are printed as diagnostics and read **near-zero
across the corpus**, which travels with every precision figure quoted from that report.
A four-decision diagnosis pass (**D-029 → D-032**) then went through every cut-rule trip:
three checks had genuine defects and were fixed, trips fell **12 → 8**, and **six of the
eight now point at gold data or the worksheet schema rather than at code** — each written up
in `docs/evals/adjudication-queue.md` with a suggested resolution and no label edited.
**None have been cut**, because a check is cut on a reproducible number.
Phase 3 (all six skills authored, since revised to five) closed 2026-09-03.

**The whole remaining critical path is the 8-site test–retest** (`EVALS.md` §1).
`harness/retest.py --emit` has drawn and logged the subset and written a blinded
208-cell worksheet; a human must re-label it from the frozen snapshots **without opening
`gold-labels-dev.csv`** and **≥ 48 h after the first pass** — earliest **2026-09-12**. A
model filling it in would measure only that two runs of the same system agree, which §1
rules out. Then `--score` gives Krippendorff's alpha per check and the cut rules become
actionable.

**Next up, in order (see `PLAN.md` §10 "What to pick up next"):** (1) the 8-site test–retest
second pass, on or after 2026-09-12 — the only thing standing between here and a closed
Phase 4; (2) ~~Stage D gold labelling~~ — **closed 2026-09-10**; (3) ~~R-1 source
verification~~ — **closed 2026-09-09 (D-027)**; a citation for
`CHK-D-001/002`'s crawler taxonomy is a smaller non-blocking follow-up; (4) ~~the
negative-control corpus gap~~ — **closed 2026-09-04 (D-026)**, the 7th dimension
`offsite_identity` is in and the set is 15 sites; (5) everything else in `PLAN.md` §8's
"Still open" list.

## Done

### 2026-09-10 — Diagnosis pass over every cut-rule trip (D-029 → D-032)

- **Three genuine check defects found and fixed.** `CHK-D-006`'s definition regex accepted
  exactly one sentence shape and rejected every real self-definition in the corpus (prec
  0.57 → 1.00). `CHK-E-014` read a hidden `rel="me"` Mastodon verification anchor as an
  unnamed control — the very construct `CHK-D-025` asks sites to add (0.88 → 1.00).
  **`CHK-D-001`'s robots.txt parser had no RFC 9309 metacharacter support**, so `Allow: /$`
  ("permit the root and nothing else") was never collected as a candidate rule and a
  `critical`-severity check reported bookshop.org as blocking seven AI-retrieval agents it
  explicitly allows (0.67 → 1.00).
- **Two narrower fixes:** `CHK-D-004`/`CHK-D-010`'s page-type exclusion gained a URL fallback
  after a contact form misfiled as `product` was called thin content; `CHK-D-010` now returns
  `not_determinable` on declared non-English pages instead of asserting "no definition,
  numeric fact or comparison" about German text it cannot parse.
- **Cut-rule trips 12 → 8, and six of the eight now point at gold data or schema, not code.**
  All in `docs/evals/adjudication-queue.md` with suggested resolutions and **no labels
  edited** — `EVALS.md` §1 permits a model to flag disagreements, never to resolve them.
- **A circularity in our own gold data was exposed.** Two German-site `CHK-D-010` rows were
  model-authored by running the same English-only regexes the check used; they scored as true
  positives because they agreed with a bug, and fixing the bug turned them into misses. This
  is the no-model-authored-labels rule failing concretely, and it implies every model-authored
  row on the four non-English sites needs auditing for the same assumption.
- **A recurring upstream cause named:** the page-type/archetype classifier defeated
  `CHK-D-006`'s suppression, `CHK-D-004`'s exclusion, and forced `CHK-E-024` to `N/A` on four
  commercial sites. Three checks, one root cause, not yet fixed.
- **A discriminator was tested and rejected** rather than shipped: link-density looked like it
  separated index pages from thin ones, but `page.links` counts site chrome, so it merely
  restates thinness and would have suppressed a genuinely thin page.
- **Schema limitation recorded:** the gold CSV has one row per check, but `CHK-E-015` has two
  sub-checks of different measurability (static viewport meta vs rendered 375px overflow).
  The analyser envelopes already carry a `subcheck` field; the worksheet does not.

### 2026-09-10 — Stage D closed, Stage E measured, matching rule repaired (D-028)

- **Stage D gold labels complete: 624/624 rows**, 24 sites × 26 checks. The last 11 sites
  (lwn.net onward) were labelled this session and merged into
  `dist/gold-labels-template.csv` → `docs/evals/gold-labels-dev.csv`; the 13 earlier sites
  were left untouched and verified byte-identical. Backup at
  `dist/gold-labels-template.pre-merge-backup.csv`.
- **Stage E ran and produced the project's first precision/recall numbers** —
  `docs/evals/stage-e-report.md`. Twelve checks trip a cut rule; clean-site FP rate is the
  weak axis (7 checks above 0.15), not recall.
- **D-028 — the matching rule was returning 0.00 for every check.** Both evidence-text
  conditions were unsatisfiable by construction: verbatim-in-snapshot rejected 129/129
  `PRESENT` rows (no check quotes its source), and evidence-Jaccard then rejected 73/129
  (gold quotes what was read, the check describes what it concluded). Two locus bugs sat
  underneath — unstripped gold cells (61 rows) and D-019 rollups being unmatchable by
  construction (60 rows). Matching is now `check_id` + locus, rollup-aware; both retired
  conditions are computed and printed as match-quality diagnostics, and they read near-zero
  across the corpus.
- `EVALS.md` §1's claim that precision was protected "because every match is separately
  verified verbatim against the snapshot" **became false with this change and was
  corrected**, not left standing.
- **Test–retest apparatus built** (`harness/retest.py`): seeded 8-site selection logged to
  `docs/evals/retest-log.md`, blinded worksheet emitted, Krippendorff's alpha scorer
  implemented and self-tested (perfect agreement → 1.0, total disagreement → −0.88,
  single-category → undefined rather than a misleading 1.0). The second pass itself is
  deliberately **not** generated — a model doing it would measure only self-agreement.
- Known gaps carried forward: `E-014`'s contrast sub-check, `E-015`'s overflow sub-check,
  `E-016` and `E-018` are `UNMEASURABLE` corpus-wide (no headless-browser pass exists);
  severity-exact rate and ordinal severity error need a gold severity column the CSV lacks.

- 2026-09-09 — **D-027: R-1 source hand-verification closed; CHK-D-011/CHK-D-013 demoted
  to recommendation-only.** A human worked the 14-source `in_minimum_set` from
  `docs/evals/r1-verification-worksheet.csv`, opening each URL and judging it against the
  ledger's actual claim rather than just confirming the source exists. That work had first
  landed in a forked, gitignored copy (`dist/EVIDENCE-LEDGER.md`,
  `dist/r1-verification-worksheet.csv`) built from a 2026-09-04 snapshot — stale relative
  to the canonical ledger, which had since gained D-018's `CHK-E-023` cut and D-014's
  `LIM-05`. Reconciled by merging the verification notes into
  `docs/research/EVIDENCE-LEDGER.md` and `docs/evals/r1-verification-worksheet.csv` (the
  files the ledger's own gate actually reads), preserving the canonical structure rather
  than overwriting it with the stale fork. Outcome: 20 of 22 non-cut checks confirmed with
  adequate support; two citation swaps applied (`CHK-D-025` gains P-06.02 alongside its
  existing sources; `CHK-D-007`'s dead co-citation to P-01.15 noted). Two findings needed a
  real decision, not a paperwork fix: **`CHK-D-001`/`002`**'s critical/low severity split
  rests on a retrieval-vs-training crawler taxonomy that no cited source establishes —
  flagged as an open gap on a `critical`-severity check, not silently accepted. **`CHK-D-011`
  and `CHK-D-013`** had zero surviving support after every cited source was opened by hand
  (unlike `CHK-D-010`/`CHK-E-021`'s earlier demotions, which had a real mechanism behind an
  imprecise proxy) — demoted to `recommendations[]` rather than cut, since the underlying
  advice stands on its own without the academic citations that failed to verify.
  `content_engagement_checks.py`'s `check_d011`/`check_d013` now set
  `recommendation_only=True` on every envelope (mirroring `check_d010`'s existing pattern);
  `content-engagement-audit`'s `SKILL.md`/`references/checks.md` updated to match. Full
  writeup: **D-027** in `docs/DECISIONS.md`. `PLAN.md` §4/§7/§9/§10 updated in the same
  pass — R-1 no longer reads "open and blocking" anywhere. Stage D (gold labels) is now the
  only item left on the critical path.

- 2026-09-04 — **D-026: the negative-control set's missing seventh dimension closed —
  `offsite_identity`, 12 → 15 sites.** `CHK-D-025`/`026`/`027` (declared identity anchors)
  had been screened only incidentally, through the two `entity_identity` rows, neither of
  which was ever verified against an anchor actually resolving — so `CHK-D-026`, the one
  check in the family that is HARD-MECHANICAL with a `high` ceiling, had no clean site
  anywhere in the corpus. Added `stripe.com`, `about.gitlab.com` and `www.docker.com`, and
  registered `offsite_identity` in `harness/score_screen.py`'s `DIMENSIONS` (deliberately
  overlapping
  `entity_identity` on the three anchor checks rather than moving them). **Selected by
  fetch, not by reputation**, per D-020's lesson: candidates were pre-screened by reading
  their homepage `application/ld+json` for an `Organization`/`Corporation` block with a
  non-empty `sameAs` *before* anything was written down. 14 candidates probed, 3
  unreachable, and **8 of the remaining 11 declared no `sameAs` at all** — including
  `www.theguardian.com`, `www.redhat.com`, `www.nature.com` and `www.khanacademy.org`, which
  emit no JSON-LD on the homepage whatsoever. All 12 rejections logged individually in
  `docs/evals/corpus-selection.md`. **All three qualifying candidates were kept**, giving
  this one dimension a spare and breaking the set's uniform 2-per-dimension shape — a
  deliberate trade, since the pre-screen showed qualifying candidates are scarce enough that
  a spare beats the symmetry. Each row was then run live end to end and its
  `anchors.results[]` read before the CSV row was written: Stripe declares 12 anchors
  (Wikipedia, Wikidata, Crunchbase, GitHub — 7 resolve 200, Crunchbase 403s to
  `resolved: null`), GitLab 6 (Wikipedia + six socials, all 200), Docker 8 (GitHub + five
  socials + two outbound profile links, all 200, but no knowledge-base entry — the weakest
  anchor set of the three, which is what makes it the useful spare against `CHK-D-025`'s
  deliberately low bar). **None of the three fires `CHK-D-025`, `CHK-D-026` or
  `CHK-D-027`** — no hard defect, no rejection needed — and Stripe's 403 is the first time
  `CHK-D-026`'s bot-blocked guard has been exercised against a real 403 rather than a
  synthetic one. Full negative set re-run offline: **15/15 schema conformant**, hard-defect
  list unchanged from the pre-D-026 baseline. Two side effects recorded rather than smoothed
  over: `CHK-D-025` fires on `docs.python.org` and `www.gov.uk` outside their curated
  dimensions (adjudication queue, unscored, as before), and Stage B′ archetype accuracy on
  the negative set moves 2/12 → 3/15 because the classifier abstains on both `stripe.com`
  and `www.docker.com`. Corpus is now 57 sites; the B′ pass runs on 45 non-held-out, not 42.
  Full writeup: **D-026** in `docs/DECISIONS.md`.

- 2026-09-04 — **D-025: the merge test ran and `render-extractability-audit` +
  `engagement-defect-audit` merged into `content-engagement-audit`, plus set stability
  (k=3) and the R-1 worksheet.** `ARCHITECTURE.md` §7 had left the merge test as an open
  question pending a real corpus; the leave-one-skill-out ablation (entry below) supplied
  it — O-1 never fired on 36 real sites — so the merge test that depended on that result
  ran the same day. The two skills' 907 lines of check code concatenated into one 908-line
  module with one unified `evaluate()`; O-1 moved in-skill (the same self-suppression
  pattern `CHK-D-004` already used against `CHK-D-003`); `compose_report.py`'s now-dead
  `apply_suppression` (and an already-dead, unrelated `_by_check_and_locus` helper found
  next to it) removed. Verified, not assumed: old two-module code vs. new merged module
  produced **zero differences** across all 42 available bundles (check_id, locus, subcheck,
  state), and the full harness (`harness/run_audit.py`, now importing the merged module)
  re-ran dev+negative+adversarial end to end at 0/42 failures, matching the pre-merge
  baseline. `marketplace.json`, `ARCHITECTURE.md`, both `audit-orchestrator` reference
  files, the root `README.md`, `EVALS.md` §7, and `PLAN.md` all updated in the same pass;
  found and fixed two pre-existing, unrelated staleness bugs along the way (orchestrator
  `SKILL.md` said "27 checks" in three places against the shipped 26; `CHK-D-007`'s
  `checks.md` still described a severity tier the code never implemented, already fixed in
  D-022 but recurring in a second file). Full writeup: **D-025** in `docs/DECISIONS.md`.
  Separately: ran set stability (k=3, 5 sites, live, `harness/stability.py`) — 5/5 stable,
  identical `(check_id, locus)` set across all three runs, no threshold per `EVALS.md` §5.
  And built an R-1 verification worksheet (`docs/evals/r1-verification-worksheet.csv` +
  README) mirroring the gold-labelling kit: 38 distinct cited sources across the 26 checks,
  a greedy set-cover computing that only **14** need verifying to cover every check at
  least once. Organizes the work only — the actual verification is human-only, same rule
  as gold labels, and was not attempted here.

- 2026-09-04 — **D-024 (harness robots.txt Allow-precedence bug) and the leave-one-skill-out
  ablation.** `excalidraw.com`'s robots.txt has both `Allow: /` and `Disallow: /` for the
  generic agent class; per the de-facto standard (longest match wins, ties favour Allow —
  already implemented correctly in the shipped `robots_parser.py`) the site is crawlable,
  but `harness/collect.py`'s separate crawl-gate (`fetcher.parse_disallows`/`path_allowed`)
  had never implemented `Allow` at all, silently discarding every `Allow` line and refusing
  to crawl a site the shipped audit logic would treat as open. Fixed by extending
  `parse_disallows` to capture `Allow` rules and rewriting `path_allowed` to mirror
  `robots_parser._root_allowed`'s precedence, generalised to arbitrary paths. Harness-only
  bug (never shipped); found `chatgpt.com` was affected the same way (0→98 URL inventory
  after the fix). Full writeup: **D-024** in `docs/DECISIONS.md`. Separately, ran
  `harness/ablation.py` (new) — leave-one-skill-out against the full 36-site dev+negative
  corpus. The trivial disjoint-partition count is as expected (each skill's owned checks
  disappear when it's removed). The sharper test — does removing `CHK-D-003`'s owner change
  what `CHK-E-019` does anywhere — came back **no**: the two checks never both fired
  `present` on the same real site, so the orchestrator's one genuine cross-skill rule (O-1)
  had zero measured effect. Matches D-016's synthetic-scenario finding, now confirmed on
  real data — evidence against the composition argument, not for it, though the merge test
  (not yet run — needs a design decision to actually restructure two skill folders) remains
  the deciding test. Full re-run of dev+negative+adversarial (all 42 sites) confirms 0
  failures after all of today's fixes.

- 2026-09-04 — **Adversarial set run live (6 sites); found and fixed D-023, a false-positive
  mechanism affecting 10 checks.** `http://www.gnu.org`'s homepage fetch failed outright
  (network-level failure, not a 4xx/5xx). Ten checks (`CHK-D-003`, `CHK-D-008`, `CHK-D-012`,
  `CHK-D-025`/`026`, `CHK-E-014`, `CHK-E-015`, `CHK-E-017`, `CHK-E-019`, `CHK-E-020`,
  `CHK-E-022`) read the resulting empty placeholder page at face value and emitted six
  confident `present` findings ("missing lang", "no h1", "no canonical", etc.) for a page
  that was never actually retrieved — six other checks already guarded on `extraction_ok`
  correctly and were unaffected. Fixed by adding the same guard to all ten; `www.gnu.org`
  now correctly reports 0 findings for its unfetchable page instead of 6 false ones.
  Re-running the full 36-site dev+negative corpus (all now succeed offline) found total
  findings fell 232→218 even on sites with no full-site failure, meaning individual pages
  within otherwise-healthy sites were also silently affected at smaller scale. Full
  writeup: **D-023** in `docs/DECISIONS.md`. Also refreshed the 2 stale snapshots
  (`creativecommons.org`, `blog.cloudflare.com`) flagged in D-021/D-022 — both now replay
  offline again, and `blog.cloudflare.com`'s archetype fix was confirmed end-to-end on a
  real live fetch (`documentation` → `unknown`, matching the earlier bundle-replay
  prediction). Corrected `harness/corpus/adversarial.csv`'s `expected_behaviour` column
  against what was actually observed for all 6 sites — three predictions were corpus
  assumptions that didn't hold against the real sites (not code defects), three matched.
  All 6 sites: no crashes, 100% schema conformance.

- 2026-09-04 — **Gold-labelling kit built for Stage D.** `harness/gold_worksheet.py`
  generates a 624-row CSV (24 dev sites × 26 checks) with a `criteria` column carrying each
  check's exact "fires when / severity / key exclusions" rule, corrected against the
  Stage C code changes (found `CHK-D-007`/`CHK-D-004`/`CHK-D-010`/`CHK-E-021`'s
  `references/checks.md` had drifted from the code — fixed in the same pass).
  `harness/export_snapshots_html.py` dumps every frozen snapshot's raw HTML to a
  browsable file. Packaged as `dist/gold-labelling-kit.zip` (15 MB, git-ignored) with a
  README covering the taxonomy, workflow, and a deterministically-chosen 8-site
  test–retest subset. Handed to the user; labelling itself is human-only work per
  `EVALS.md` §1 and not something this session can do.

- 2026-09-04 — **Stage C: resolved the five checks Stage B flagged, fixed the archetype
  classifier's dead JSON-LD path, wrote D-021/D-022.** Full detail in
  [`docs/evals/stage-c-report.md`](evals/stage-c-report.md); one-line version: a harness-only
  bug (`harness/collect.py` reading `structured_data.get("types")`/`.get("sameAs")`, keys
  that were never produced) had silently killed every JSON-LD-driven archetype/page-type
  signal for the entire Stage B/B' run. Fixing it plus four related mechanisms (raw-HTML
  price regex, uncorroborated `product_count`, an unanchored "plans" match, sitemap media
  URLs mislabelled `documentation`) took archetype confident-wrong labels from 5 to 1 of 34
  sites. Separately resolved the five checks `stage-b-report.md` §3 left open: `CHK-E-014`
  and `CHK-E-022` accepted as-is (hand-verified against real HTML, matches cited base
  rates); `CHK-D-007` severity capped medium→low (D-009 base-rate conditioning); `CHK-D-004`
  now excludes `home` page type; `CHK-E-021` and `CHK-D-010` demoted to
  `recommendations[]`. Negative-control findings fell 107–112 → 88; hard-defect sites 7/12
  → 5/10. Bundle-sufficiency (`EVALS.md` §7) verified by grep — no analyser imports
  networking. Merge test and leave-one-skill-out ablation not run (structural changes, not
  code fixes). Entirely offline, against `harness/snapshots/`; two sites
  (`creativecommons.org`, `blog.cloudflare.com`) now need a live re-fetch to replay offline
  again, since the sampler fix changed which pages they select.

- 2026-09-04 — **Stage A/A′/B/B′: harness built, held-out sealed, first contact with real
  sites.** `harness/` (git-ignored, imports shipped `scripts/` unmodified) walks a real
  site end-to-end. Found and fixed 5 crashes on real sites (3 `RecursionError`s from
  recursive DOM traversal, one array-valued JSON-LD `@type`, one unrendered sitemap
  template) — **D-019/D-020** in `docs/DECISIONS.md`. Full detail:
  [`docs/evals/stage-b-report.md`](evals/stage-b-report.md).

- 2026-09-03 — **Post-officials-Q&A repair, item 3 of the action list (context efficiency
  and skill-count justification).**
  - **D-016 — suppression-necessity test found rule O-2 unreachable, removed it.** Item 3
    asks the six-skill count to be *demonstrably* justified via §7's suppression-necessity
    test. The full test needs the Phase 4 dev corpus (doesn't exist yet), but checking
    `compose_report.py`'s `dedup_js_only_cluster` (the JS-only four-way root-cause collapse)
    against the checks it depends on found the answer doesn't need a corpus: `CHK-D-003`
    and `CHK-E-019` only fire when the homepage's raw word count is <50, while `CHK-D-005`
    requires >500 words on a page before it evaluates at all — mutually exclusive on the
    same page, so the four-way pattern can never occur. Separately, `CHK-D-004` already
    self-suppresses on the homepage whenever `CHK-D-003` fires, which alone already
    prevented the "four findings for one defect" failure O-2 existed to solve. Removed
    `dedup_js_only_cluster`, `JS_ONLY_CLUSTER`, `JS_ONLY_DEDUP_TITLE`, and the
    `consequences` field from `compose_report.py`. Kept rule O-1 (`CHK-E-019` defers to
    `CHK-D-003`), confirmed by a synthetic-bundle run (5 scenarios, not the real dev corpus)
    to actually fire, including under D-015's no-headless-browser condition. Updated every
    doc that described the old four-way collapse: `ARCHITECTURE.md` §4.3/§7 (now records
    the partial result and leaves open whether one real cross-skill rule justifies keeping
    `render-extractability-audit` and `engagement-defect-audit` separate — a question for
    Phase 4's real numbers, not five synthetic scenarios), `audit-orchestrator/SKILL.md`
    and `references/report-schema.md`, both analysers' `SKILL.md`/`references/checks.md`,
    and the root `README.md`'s "novelty" claims. Full writeup: **D-016** in
    `docs/DECISIONS.md`.
  - **File-size audit (item 3a).** Measured every skill's `SKILL.md`/`references/` word
    count and `scripts/` line count. `audit-orchestrator/SKILL.md` is the standout at
    ~2,258 words — roughly double the next-largest `SKILL.md` — but reading it end to end
    found the length load-bearing (the 7-step procedure, the meta-evaluation table, the
    D-016 honesty record), not padding, so no cut was forced just to hit a number. The
    larger `references/` files (`engagement-defect-audit` ~3,722 words,
    `site-evidence-collector` ~3,551 words) are loaded on demand per-skill, which is what
    progressive disclosure is for, not eager-loaded bloat. Total marketplace on disk is
    344 KB — nowhere near the 50 MB cap, confirming size risk here is about agent-context
    tokens per run, not zip size. No file was cut on this pass; `audit-orchestrator/SKILL.md`
    is the next trim candidate if a future pass wants one.
  - Not run this pass: the merge test and bundle-sufficiency test from `ARCHITECTURE.md`
    §7 (both need either the dev corpus or a deliberate refactor exercise, neither of which
    this pass attempted).

- 2026-09-03 — **Post-officials-Q&A repair, items 1 and 2 of the action list.** Read
  `OFFICIALS-QA.md` and checked the actual code (not just the docs) before touching
  anything.
  - **D-015 — no-headless-browser handling.** Checking the code found the "graceful
    degradation" claim was half true: checks correctly emit `not_determinable` when
    `rendered[]` is empty, but `not_determinable` envelopes are dropped before the report
    is assembled (`compose_report.py`'s `split_findings_recommendations` keeps only
    `state == "present"`), so in the grading sandbox — where there is no headless-browser
    tool for the *entire* run, not occasionally — the seven render-dependent checks would
    vanish from every report with no trace, unless `budget.stages` separately declared the
    render stage abandoned, which nothing previously instructed for the "tool doesn't
    exist" case (only for a mid-run timeout). Fixed two ways: (1) `CHK-D-003` and
    `CHK-E-019` now re-derive a one-sided static-only signal (no h1 + <50 words; noscript +
    static volume) instead of going fully dark, capped one severity tier below their
    two-sided result; (2) `site-evidence-collector`'s procedure now requires declaring
    `render_pass` as `abandoned: true` at zero elapsed time whenever `headless_browser`
    isn't available, so `degraded_stages[]` names the five checks with no static proxy
    (`CHK-E-014` contrast, `CHK-E-015` overflow, `CHK-E-016`, `CHK-E-018`)
    instead of them being silent. Verified against four synthetic-bundle cases (no
    renderer + sparse static → fires; no renderer + rich static → stays
    `not_determinable`; renderer present → unchanged two-sided behaviour; `degraded_stages`
    correctly lists all seven affected check IDs). Full writeup: **D-015** in
    `docs/DECISIONS.md`.
  - **D-014 — llms.txt surfaced visibly.** Added a fifth static declared limitation,
    `LIM-05`, to `compose_report.py`'s `DECLARED_LIMITATIONS` — always present, like
    LIM-01…04, not a per-site check or recommendation. Deliberately routed through
    `limitations[]` rather than `recommendations[]`: the D-007 prohibited-recommendation
    regex scans `findings[]`/`recommendations[]` action text for the literal string
    "llms.txt", which would have false-positived on a disclosure that declines to
    recommend it. `limitations[]` isn't scanned by that check. Verified: `len(report
    ["limitations"]) == 5`, `meta_evaluation.passed == True`.
  - Docs updated to match in the same pass (not left to drift): `EVIDENCE-LEDGER.md`
    (D-003/E-019 rows, the render-pass degradation-rule paragraph, LIM-05 row),
    `BUNDLE-SCHEMA.md` (`rendered[]` section, budget stage example), both analysers'
    `references/checks.md`, `site-evidence-collector`'s `SKILL.md` and
    `references/procedure.md`, `audit-orchestrator`'s `SKILL.md` and
    `references/report-schema.md`.
  - **Not changed:** `CHK-E-014`'s five static WCAG sub-checks and `CHK-E-015`'s
    viewport-meta sub-check were already unconditional on `rendered[]` — checking the code
    confirmed they already matched the officials' guidance exactly, so nothing was touched
    there.
  - **Still open from the action list:** item 4 (`archetype`-driven vertical checks), item
    5 (context-carry-over / landing-intent), item 8 (teammate-prompt rewrites), and R-1
    (human hand-verification, cannot be delegated to a model). Item 3 done in the entry
    above.

- 2026-09-02 — **Phase 3, all 6 skills authored.** See "Phase 3 — skill authoring
  (6 of 6 — 2026-09-02)" below for the full per-skill breakdown and the note on how the
  three duplicated skills were reconciled between two parallel sessions.

- 2026-09-02 — **Phase 1b Synthesis Complete.**

  - `docs/RESEARCH.md` mapped with all 24 signal definitions (13 discoverability, 11 engagement) backed by literature.
  - `docs/research/EVIDENCE-LEDGER.md` populated with the 24 candidate checks, their source mappings, severity rules, and false-positive guards.
  - `docs/EVALS.md` rewritten with the concrete metric targets and procedures derived from `05-evaluation-methodology.md`.
  - `docs/CORPUS.md` rewritten with the stratified sampling frame and split logic derived from `08-web-corpora-and-sampling.md`.
- 2026-09-01 — **Domains 04 and 06 landed**, executed in Antigravity (separate tool,
  separate budget) from the stored briefs — 13 entries each, statuses marked per entry:
  [`papers/04-...`](research/papers/04-web-agents-page-understanding.md) (WebArena,
  Mind2Web, VisualWebArena, WorkArena, BrowserGym, AssistantBench, WebVoyager, AutoWebGLM,
  Trafilatura) and
  [`papers/06-...`](research/papers/06-structured-data-entity-grounding.md) (WDC Oct 2024,
  Web Almanac 2024, MAVE, FEVER, BLINK, ReFinED, PopQA/Mallen, FreshLLMs, TempLAMA).
  These close the two substantive discoverability gaps.
- 2026-09-01 — **Literature review, priority half complete.** Four domain agents landed: 01 (GEO), 05 (Eval), 07 (On-site), 08 (Corpora). Conclusions banked as decisions **D-006** to **D-010**.
- 2026-09-01 — Research scaffolding: `research/README.md`, `research/EVIDENCE-LEDGER.md`, `research/AGENT-BRIEFS.md`, `EVALS.md`, `CORPUS.md`.
- 2026-09-01 — Handout read in full, copied to `round3-handout.pdf`, distilled into the `round3-spec` skill; working method in the `project-flow` skill.

## Next — phased, each phase ends in a checkpointed state

**Phase 2 — architecture.** Fix the skill decomposition and the entrypoint's composition
contract. Blocked on nothing, but running research domains 02 and 03 would strengthen the justification.

**Phase 3 — author the skills.** `SKILL.md` per concern, `references/` for checklists,
`scripts/` for executable checks.

**Phase 4 — corpus + harness.** Build the dev/held-out/negative-control/adversarial sets
and the eval harness per D-010.

**Phase 5 — harden and package.** Guardrail and generalization gates, root `README.md`,
manifest, zip.

## Deferred — the four unrun research domains

Briefs are ready in [`AGENT-BRIEFS.md`](research/AGENT-BRIEFS.md); relaunch is copy-paste.

| Domain | Why it was deferred | What we lose without it |
| --- | --- | --- |
| 02 Skill authoring | Phase 3 can proceed on general practice | Weaker evidence base for *how* instructions are written for reliability and determinism |
| 03 Composition | Phase 2 can proceed on judgment | The rubric's composition line becomes an argument from taste, not evidence |

**Honest status of coverage:** both halves of the audit now have a research base — 01/04/06
for discoverability, 07 for engagement, 05 for evaluation, 08 for corpora. The two
remaining domains affect how well we can *justify* design choices (how skills are authored,
and how many there should be), not what the checks are. They are worth running before
Phase 2 if budget allows, but they do not block it.

## Phase 1b review — corrections outstanding

Reviewed 2026-09-02; full detail in
[`research/EVIDENCE-LEDGER.md`](research/EVIDENCE-LEDGER.md) under "Review — 2026-09-02".

- **R-1 (done)** — all 24 rows had been self-certified as hand-verified by the authoring
  tool; reset to `— pending`. A human must spot-check one cited source per check.
- **R-2 (done)** — search-only sources removed from load-bearing roles: CHK-D-003's severity
  rule is now definitional rather than threshold-based; CHK-E-024 demoted to a proactive
  recommendation under the new single-source rule.
- **R-3 (done)** — `NORMATIVE` recorded as **D-011** with a full strength vocabulary and
  ceilings; CHK-E-020 re-grounded on WCAG 2.2 SC 1.4.2 and demoted to `medium`; CHK-E-021
  given one coherent label and capped.
- **R-7 (done)** — ID sequence documented as deliberate and stable; dev gold labels 20 → 24;
  negative controls 24 → 27; report schema settled as **D-012** (`findings[]` for defects,
  sibling `recommendations[]` and `limitations[]`).
- **R-4 (done)** — headless rendering now budgeted: one shared render pass per sampled page
  (max 3), seven declared consumers, 220 s subtotal against the 300 s cap with 80 s
  reserve, and a degradation rule emitting `not_determinable` rather than inferring from
  static HTML.
- **R-5 (done)** — off-site coverage added: **CHK-D-025** (no declared identity anchors),
  **CHK-D-026** (declared anchors that don't resolve — bounded off-site HEAD checks),
  **CHK-D-027** (identity attributes self-inconsistent across own pages). What stays
  unmeasurable is declared as **LIM-01…LIM-04** and reported, not omitted. Ledger is now
  **26 checks + 5 declared limitations** (27 checks and 4 limitations when written; CHK-E-023
  was cut by D-018 and LIM-05 added by D-014).
  - *Follow-on:* `CORPUS.md` sizes negative controls at 3 per each of 8 dimensions; the
    off-site dimension makes 9, so that set should grow to 27 sites.
    **Closed 2026-09-04 (D-026)**, at the post-D-017 arithmetic rather than this one: 2 per
    dimension, 6 → 7 dimensions, 12 → 15 sites (the new dimension keeps a third row as a
    spare). The dimension is `offsite_identity`.
- **R-6 (done)** — Phase 2 decomposition decided deliberately as **D-013**: six skills, split
  by mechanism with network I/O extracted into `site-evidence-collector`. Full rationale,
  composition contract, and check map in [`ARCHITECTURE.md`](ARCHITECTURE.md), now
  authoritative for check ownership.

**All seven review findings resolved.** Phase 2 complete.

## Phase 3 — skill authoring (6 of 6 — 2026-09-02)

Marketplace root at [`brand-ai-readiness-audit/`](../brand-ai-readiness-audit).

Authored across two parallel Claude sessions on two devices working from the same handoff
brief. `render-extractability-audit` was written once (session A only). The other three —
`entity-identity-audit`, `engagement-defect-audit`, and `audit-orchestrator` — were written
independently by *both* sessions, producing two full versions of each. Reconciled
2026-09-02: for each of the three, the more rigorous version was kept (concrete numeric
thresholds and normalization rules rather than looser prose — e.g. named legal-entity-suffix
equivalence for CHK-D-027, explicit WCAG contrast ratios for CHK-E-014f), and
`audit-orchestrator/references/report-schema.md` was enriched with the other session's
27-check title-map table, which the kept version didn't have but needs for D-010's
run-to-run title stability. Both sessions independently reached the same correction to
`ARCHITECTURE.md` §4.3 (see below) — a useful cross-check that it's actually right.

- ✅ `BUNDLE-SCHEMA.md` — interface contract with coverage walk (all checks satisfied — 27 at the time of writing, 26 since D-018).
  Three caveats recorded (ad detection is the weakest check; CHK-D-012's time-sensitivity
  label belongs in the analyser; CHK-E-016's "standalone" is deliberately collector-side).
  One conflict with ARCHITECTURE.md found and resolved: 3 navigations / 4 viewport
  measurements, not 6.
- ✅ `marketplace.json` — exactly one entrypoint, all six skill paths now exist on disk.
- ✅ `site-evidence-collector` — `SKILL.md` (lean), plus `references/procedure.md`,
  `references/ai-crawler-agents.md` (the retrieval-vs-training classification that separates
  CHK-D-001 from CHK-D-002), and `references/bundle-schema.md`.
- ✅ `crawl-access-audit` — `SKILL.md` (lean, no `references/` — two checks reading one
  bundle section don't need progressive disclosure).
- ✅ `render-extractability-audit` — `SKILL.md` + `references/checks.md` (7 checks,
  mechanisms B/C: CHK-D-003, D-004, D-005, D-009, D-010, D-011, D-013).
- ✅ `entity-identity-audit` — `SKILL.md` + `references/checks.md` (7 checks, mechanism D —
  the only skill reading `anchors`; classifies EVERGREEN vs. TIME-SENSITIVE for CHK-D-012
  per `BUNDLE-SCHEMA.md` Caveat 2; documents LIM-01/LIM-02 as structurally out of scope).
- ✅ `engagement-defect-audit` — `SKILL.md` + `references/checks.md` (11 checks, mechanisms
  E/F — the biggest skill; framed per D-008 as defect detection, never outcome prediction;
  CHK-E-024 routes to `recommendations[]` via `"route": "recommendations"` under the
  single-source rule).
- ✅ `audit-orchestrator` — `SKILL.md` + `references/report-schema.md` (entrypoint; collect
  → run four analysers → cross-skill suppression (rule O-1: CHK-E-019 yields to CHK-D-003,
  the one genuinely cross-skill dependency) → JS-only root-cause dedup (rule O-2, requires
  all of CHK-D-003/004/005/E-019 present simultaneously before collapsing) → separate
  findings/recommendations/limitations → assemble). Documents that two of
  `ARCHITECTURE.md` §4.3's three named "cross-skill suppression" examples
  (CHK-D-002/D-001, CHK-D-010/D-004) are actually same-skill pairs already resolved inside
  `crawl-access-audit` and `render-extractability-audit` respectively.
- ✅ **`brand-ai-readiness-audit/README.md`** — the root README required at submission per
  `round3-spec` §7: what the marketplace does, a table of all six skills and their checks,
  how `audit-orchestrator` composes them (collect → analyse → reconcile → assemble), the
  guardrails, and the declared limitations. Links verified against the actual `docs/`
  paths.
- ✅ **`scripts/` for all six skills** (2026-09-03), stdlib-only Python (no pip installs,
  keeps the marketplace self-contained). `site-evidence-collector`'s scripts turn
  already-fetched raw content into bundle sections — robots.txt parsing/classification, a
  full HTML extraction pipeline built on a from-scratch DOM tree (`html.parser`, no
  bundled dependency), deterministic seeded sampling, and the render-geometry
  classification (WCAG contrast ratio via the real relative-luminance formula, the
  ad-region two-detector rule, overlay/tap-target detection) — they never fetch or render
  anything themselves; that stays the agent's `http_fetch`/`headless_browser` tool calls.
  Every one of the checks is implemented as a pure `evaluate(bundle)` function and
  exercised against synthetic bundles; a full pipeline run (real HTML → extraction → all
  four analysers → orchestrator composition) confirmed the pieces integrate, not just
  each in isolation. Two real bugs found and fixed during testing: an `href=""` falsy-string
  check that silently excluded empty anchors from the `interactive_empty` count, and a
  leftover-redistribution step in page sampling that ignored the per-type cap it was
  supposed to enforce. One naming bug found and fixed structurally: all four analysers had
  independently named their check script `checks.py` — `import checks` after adding more
  than one to `sys.path` would silently reuse whichever loaded first for all the others;
  renamed each to a unique module name (`crawl_access_checks.py`,
  `render_extractability_checks.py`, `entity_identity_checks.py`,
  `engagement_defect_checks.py`) rather than relying on the invoking agent to use
  `importlib` correctly. One doc inconsistency found in `BUNDLE-SCHEMA.md`: it claims
  `trigram_hash` (a single SHA-256 digest) "supports CHK-D-013's Jaccard comparison," but a
  single hash of a whole set can only prove two pages identical or different — it cannot
  produce a similarity *percentage*. Routed around it rather than redesigning the schema:
  CHK-D-013 computes Jaccard directly from `pages[].main_text`, which is already in the
  bundle at no extra cost; `trigram_hash` is left as documented, unused by this check.
- ✅ **Review-pass changes (2026-09-03)** — seven items from an external read of the
  submission, all applied to the marketplace root (`docs/` internal research retains its
  original wording; only `brand-ai-readiness-audit/` ships):
  1. **"rendered page evidence", not "headless browser evidence"** throughout the prose and
     the `not_determinable` reason strings. `headless_browser` stays as the literal
     `allowed-tools` identifier — renaming that would break the tool contract the invoking
     agent binds to; the change is about how the *evidence* is described.
  2. **Determinism reframed as a reproducibility goal, not a requirement.** A live site is
     not a fixed object; the report now says where run-to-run variation is possible
     (`degraded_stages`, `not_determinable`) instead of implying stability it cannot promise.
  3. **Meta-evaluation step added** as orchestrator Step 7 — seven coherence checks over the
     finished report (counts reconcile, findings complete, no duplicate check per locus, known
     check IDs, D-007 prohibited-recommendation scan, limitations present), emitted as a
     `meta_evaluation` block. Warnings are reported, never auto-corrected. **This surfaced a
     real bug in itself on first run:** CHK-E-014 and CHK-E-015 each legitimately grade one
     page twice (static WCAG vs. contrast; viewport meta vs. overflow), which the duplicate
     detector flagged falsely — fixed structurally by tagging those envelopes with a
     `subcheck` discriminator rather than by loosening the check.
  4. **Recommendations stated as vertical-specific**, with the assumed archetype now carried
     in `preamble.archetype` / `recommendations_scoped_to` so a reader knows which vertical
     the actions were written for; `unknown` suppresses archetype-conditioned checks rather
     than guessing.
  5. **Runtime scope clarified**: the budget bounds how long the audit *waits* on an external
     origin, and is not a claim about site latency — a slow site yields a partial report on
     time, never a complete one late.
  6. **Persistent storage removed as an assumption** — the bundle is in-memory for one run
     and discarded; nothing is written to disk or cached, and no run can influence another.
  7. **Novelty stated explicitly** — evidence-capped urgency, root-cause collapse instead of
     four tickets, vertical-conditioned wording, and mechanically-enforced refusal of the
     advice a baseline checklist would emit.
- **Still outstanding from Phase 2 (R-1, blocking before ship):** every row in
  `EVIDENCE-LEDGER.md` still reads `Verified by hand: — pending`. Authoring the skills
  didn't require this, but shipping does — a human needs to open at least one cited source
  per check before this goes in the zip.

**Packaging note:** `docs/BUNDLE-SCHEMA.md` is canonical during development. Re-copy it
to `skills/site-evidence-collector/references/bundle-schema.md` at packaging time (Phase 5).

## Phase 4 — corpus + harness (next)

Build the dev/held-out/negative-control/adversarial sets and the eval harness per D-010.

## Phase 5 — harden and package (queued)

Guardrail and generalization gates, root `README.md`, manifest, zip.


## Blocked / open questions

- **No public AI-assistant citation dataset exists**, and no curated site-quality label
  corpus — domain 08 searched and found neither. Gold labels must be hand-authored.
- **Corpus access blockers:** HTTP Archive needs a billed Google Cloud project; CrUX needs
  an API key and excludes small sites (exactly our target population); ClueWeb22 is gated;
  Tranco's combined-list licence is unclear. Wayback is unreliable as a fixture source (at
  most ~17.9% of composite mementos are both temporally coherent and complete).
- **Nothing in the literature measures our actual target quantity** — the effect of a
  specific site-side fix on a specific brand's representation in a specific assistant. That
  experiment does not appear to exist publicly. We build on mechanism-level evidence, and
  the report's language must say so.
- **ICC assumption.** Domain 08's sample-size math assumes ρ≈0.20 (unmeasured). ρ > 0.4
  falsifies the split plan.
