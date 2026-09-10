# Round 3 — Agent Skill Marketplace: Plan & Status

**Self-contained briefing.** Written so someone with no access to this repo can read it
cold, understand the task, see what has been done, and argue usefully about what's left.
Last updated 2026-09-04.

---

## 1. The task

Adobe University Hackathon 2026, **Round 3 — "Build the Agent Skill Marketplace."**
Take-home. AI assistance explicitly allowed.

Round 2 tested reasoning *on paper*: why a brand is invisible, stale, or bouncing in AI
apps. Round 3 tests whether that reasoning can be **encoded into reusable agent skills**,
so a general AI agent pointed at *any* website audits it automatically and produces a
report of findings plus suggested fixes.

**The deliverable** is a zip of a marketplace root directory containing:
- `marketplace.json` — a manifest listing every skill, with **exactly one** marked as the
  entrypoint
- one or more skill folders, each a valid **agentskills.io** `SKILL.md` (YAML frontmatter
  + instructions, optional bundled `scripts/` and `references/`)
- a root `README.md` describing what each skill does and how the entrypoint composes them

**What it must do.** Given a website, the entrypoint audits it and emits one JSON report
covering *both* halves of the problem:
- **Off-site discoverability** — why AI assistants don't find, cite, or correctly
  represent the brand
- **On-site engagement** — why visitors who do arrive don't stay

Each finding carries evidence and a severity; each gets a suggested action, prioritized.
Suggested actions may go *beyond* detected defects — proactive improvements where no
explicit defect was found.

### Required report schema (a floor, not a ceiling)

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": { "total_findings": 6, "critical": 1, "high": 2, "medium": 3 },
  "findings": [
    {
      "id": "F-001",
      "title": "No JSON-LD structured data on product pages",
      "severity": "high",
      "evidence": "Crawled 12 product pages; 0/12 contain schema.org markup.",
      "suggested_action": {
        "summary": "Add Product/Offer JSON-LD to every product page.",
        "priority": "high"
      }
    }
  ]
}
```

Required per finding: `id`, `title`, `severity`, `evidence`, `suggested_action`.
Required top level: `site`, `audited_at`, counts-by-severity `summary`.

---

## 2. Hard constraints

| Constraint | Detail |
| --- | --- |
| Recommend-only | No skill ever alters a live site. Audits and reports only. |
| Read-only, sandboxed | No destructive, authenticated-area, or rate-abusing actions |
| robots.txt | Respected |
| Runtime | **< 5 minutes** for a typical website on a standard machine |
| Size | Submission zip **≤ 50 MB**, no pre-trained model weights |
| Portability | agentskills.io format is provider-neutral; each skill declares its tool needs |
| Self-contained | The manifest resolves with no external service |

---

## 3. How it's graded

They evaluate **the marketplace itself** — its skills' instructions, checks, logic, and
how the entrypoint composes them — **not any single report it produces**. No example sites
are provided at any point; generalization is "tested by construction" on unseen sites.

| Criterion | Looking for |
| --- | --- |
| Detection accuracy | Real problems, evidence-backed, across both halves, **few misses and few false positives** |
| Suggested-action quality | Fixes correctly targeted, mechanism-sound, prioritized; beyond-problem suggestions relevant and non-obvious |
| Output design | Clear, structured, actionable report a **non-expert** could act on |
| Skill-format & hygiene | agentskills.io compliant; well-formed manifest with exactly one entrypoint; deterministic; safe |
| Marketplace composition | Genuine separation of concerns, cleanly composed — **not padding**. A single well-built skill scores fully here too. |
| Generalization | Works on sites never seen |

**Three things that follow from this and drive every decision below:**

1. False positives are penalized as hard as misses. A check that fires wrongly costs us
   twice — once on accuracy, once on the credibility of the whole report.
2. Decomposition is rewarded but padding is punished, and a single good skill scores
   fully. So skill count must be *earned*, not assumed.
3. Nothing can be fitted to example sites, because there are none. Every check must derive
   from a mechanism that generalizes.

---

## 4. Where we are now

**Phases 1, 1b, 2 and 3 are complete; Phase 4 is in progress.** What exists on disk is a
working five-skill marketplace with 26 checks implemented as tested code, a manifest, and a
root README (started as six skills under D-013; two merged 2026-09-04 as **D-025**, after
Phase 4's ablation found the real evidence to justify it — see §7 below). Phase 4 has run
against real sites (Stages A–C, plus the adversarial set and both composition tests); Stage
D (gold labels) has not, so no precision/recall number exists yet. Every accuracy claim
that isn't explicitly sourced to a Stage B/C/adversarial result in `docs/DECISIONS.md` is
still a design argument, not a measurement.

### The marketplace as built (`brand-ai-readiness-audit/`)

| Skill | Role | Checks |
| --- | --- | --- |
| `audit-orchestrator` *(entrypoint)* | Composes the rest; report assembly, budget arbitration, report meta-evaluation | none of its own |
| `site-evidence-collector` | The only skill with network tools. Emits one in-memory evidence bundle | none — observes only |
| `crawl-access-audit` | Mechanism A | D-001, D-002 |
| `content-engagement-audit` | Mechanisms B, C, E, F | D-003, D-004, D-005, D-009, D-010, D-011, D-013, E-014 … E-022, E-024 |
| `entity-identity-audit` | Mechanism D | D-006, D-007, D-008, D-012, D-025, D-026, D-027 |

26 checks, disjoint, each traced to a row in `docs/research/EVIDENCE-LEDGER.md`. Every
check is implemented as a pure `evaluate(bundle)` function in that skill's `scripts/`,
stdlib-only Python so the zip needs no dependency install. The collector's scripts do the
parsing and extraction; the network calls themselves stay with the invoking agent's
declared tools, which is what keeps the read-only and budget guarantees structural rather
than promised.

**Tested well beyond synthetic bundles now.** Phase 3 exercised every module against
synthetic bundles and one full pipeline run, which found four bugs (a falsy-string check
that silently dropped empty anchors; a sampling step that ignored its own per-type cap; a
module-name collision that would have made analysers silently load each other's code; a
false positive in the meta-evaluation itself). Phase 4 then ran the harness against **42
real websites** (24 dev + 12 negative-control + 6 adversarial) and found substantially more
— five harness crashes, four false-positive mechanisms, a bug that had silently killed
every JSON-LD-driven signal for two full evaluation stages, a false-positive-generating
treatment of failed page fetches affecting ten checks, and a robots.txt precedence bug —
all found and fixed, all logged as **D-019 through D-024** in `docs/DECISIONS.md`. The
leave-one-skill-out ablation and the merge test (`EVALS.md` §7's two composition tests)
have both run against the real corpus and resolved the six-vs-five-skill question the
architecture doc had left open (**D-025**): the marketplace is five skills now, not six.

**Phase 4 now has a measured precision/recall number** (2026-09-10). Stage D gold labelling
completed at **624/624 rows, 24 sites × 26 checks**, and Stage E scored it:
`docs/evals/stage-e-report.md`. Two things must travel with those numbers:

1. **The matching rule had to be loosened to produce them at all.** Its first run returned
   precision 0.00 / recall 0.00 for all 26 checks — both of its evidence-text conditions
   were unsatisfiable by construction (the checks describe evidence, the labeller quotes
   it), and two locus bugs sat underneath. Matching is now `check_id` + locus. The retired
   conditions are computed and printed as diagnostics, and **they read near-zero across the
   corpus**: the detections hit the right check on the right page, and essentially none of
   them corroborate against the labeller's wording. See **D-028**.
2. **Nothing is cut yet.** Twelve checks trip a cut rule, but the 8-site test–retest
   (`EVALS.md` §1) has not run — earliest valid date **2026-09-12**, because the second pass
   must be blind and ≥48 h after the first. A check is cut on a reproducible number, not a
   single pass.

So "designed for few false positives" is now a number rather than an argument — and the
number says clean-site false-positive rate is the weak axis, with seven checks above the
0.15 cut line.

### Research corpus on disk (`docs/research/papers/`)

| Domain | Sources | Verification | Size |
| --- | --- | --- | --- |
| 01 GEO / AI-search citation | 15 | 15 verified | 44 KB |
| 04 Web agents & page understanding | 13 | 10 verified, 3 search-only | 37 KB |
| 05 Evaluation methodology | 31 | 29 verified, 1 biblio-only, 1 search-only | 67 KB |
| 06 Structured data & entity grounding | 13 | 9+ verified, 1+ search-only | 35 KB |
| 07 On-site engagement | 16 | 8 verified, 8 search-only (paywalled, cross-indexed) | 58 KB |
| 08 Web corpora & sampling | 14 | 13 verified, 1 search-only | 47 KB |

`VERIFIED` = the source was opened and read. `SEARCH-ONLY` = it appeared in search with a
plausible title and venue but could not be opened — **usable as a lead, not as
justification for a shipped check.**

**Not yet run:** domain 02 (skill authoring / instruction reliability) and domain 03
(multi-agent composition and its failure modes). Briefs are ready. These affect how well we
can *justify* design choices, not what the checks are.

### Supporting documents

- `docs/round3-handout.pdf` — the source of truth, plus a full transcription in
  `.claude/skills/round3-spec/references/handout-full.md`
- `docs/DECISIONS.md` — append-only decision log (D-001 … D-025 as of this writing,
  summarized in §6)
- `docs/PROGRESS.md` — current state and phase plan, updated per work session
- `docs/ARCHITECTURE.md` — the five-skill decomposition, why this axis, and the three tests
  that falsify it — one of which already has, per D-025
- `docs/BUNDLE-SCHEMA.md` — the pinned collector↔analyser contract, with a coverage walk
  proving all checks are satisfiable from it (written against 27; 26 ship since D-018)
- `docs/RESEARCH.md` — mechanism-anchored signals — **done**
- `docs/research/EVIDENCE-LEDGER.md` — per-check audit trail, 26 shipped checks + 5 declared
  limitations — **done, including hand-verification (R-1 closed 2026-09-09, see D-027)**
- `docs/EVALS.md`, `docs/CORPUS.md` — filled from domains 05 and 08
- `docs/FETCH-STRATEGY.md` — fetch fallbacks, block taxonomy, testing against blocked sites
- `.claude/skills/round3-spec/` and `.claude/skills/project-flow/` — the task and the
  working method, encoded so context survives across sessions
- `docs/evals/stage-b-report.md`, `docs/evals/stage-c-report.md` — Phase 4's first-contact
  and bug-fixing results against real sites, with numbers (findings before/after, hard
  defects, archetype accuracy, set stability, a 5-site runtime sample)
- `docs/evals/corpus-selection.md`, `docs/evals/holdout-log.md` — the sealed selection rule
  and the (still-empty) held-out look log
- `docs/evals/gold-labels-template.csv` + `dist/gold-labelling-kit.zip` — the Stage D
  worksheet (624 rows, 24 sites × 26 checks, criteria pre-filled) and a packaged,
  self-contained kit (worksheet + all 24 sites' pages as browsable HTML + a README) handed
  off for gold labelling
- `docs/evals/r1-verification-worksheet.csv` + README — the R-1 equivalent: 38 cited
  sources ranked by leverage, with a computed 14-source minimum that covers all 26 checks
  at least once. **Filled in as of 2026-09-09** — all 14 opened and judged by hand; see
  D-027
- `harness/` — the evaluation driver (git-ignored, never ships): `run_audit.py`,
  `collect.py`, `fetcher.py`, `ablation.py`, `stability.py`, `gold_worksheet.py`,
  `r1_worksheet.py`, `export_snapshots_html.py`, plus `corpus/*.csv` and `out/*/` results

**The immediate gap is no longer synthesis, and it is narrower than it was.** Phase 4 has
already turned most of the "design argument, not a measurement" problem into tested code —
what's left is specifically the one thing that cannot be done by anything other than a
human:

1. **R-1 — closed 2026-09-09 (D-027).** A human opened all 14 `in_minimum_set` sources
   (`docs/evals/r1-verification-worksheet.csv`) and judged each against the ledger's actual
   claim; every non-cut check in `docs/research/EVIDENCE-LEDGER.md` now carries a real
   `Verified by hand` entry. Two outcomes needed a decision rather than a paperwork fix:
   **CHK-D-011** and **CHK-D-013** had zero surviving support after all cited sources were
   checked — demoted to `recommendations[]`, not cut (D-027). **CHK-D-001/002**'s
   critical/low severity split rests on a retrieval-vs-training crawler taxonomy no cited
   source actually establishes — flagged as an open gap, not silently accepted (see §9).
2. **Accuracy — measured 2026-09-10, not yet reproducible.** Stage D labelling is complete
   (624/624) and Stage E has scored it (`docs/evals/stage-e-report.md`, D-028). What remains
   is the one part still gated on a human *and* on the calendar: the **8-site test–retest**
   (`EVALS.md` §1). The subset is drawn and logged, and `harness/retest.py --emit` has
   written a blinded worksheet — but the second pass has to be re-labelled by hand, blind to
   the first, **≥ 48 h later**. A model filling it in would measure only that two runs of the
   same system agree, which §1 explicitly rules out. Earliest valid date: **2026-09-12**.
   Until then the twelve cut-rule trips in the Stage E report stand as *unconfirmed*.

---

## 5. What the research actually established

The findings that changed the design. These are the load-bearing ones.

### Discoverability

**Visibility is a distribution, not a fact.** Whether a brand appears in an assistant's
answer varies across runs, prompts, and time. Consequence: the audit must **never query a
live generative engine** — doing so would break determinism, the 5-minute budget, and
reproducibility at once. We audit site-side properties and never claim citation outcomes.

**Extractable evidence density is the strongest content signal.** Pages that get absorbed
into answers are longer, more structured, and richer in definitions, numerical facts,
comparisons, and procedural steps (measured across 602 prompts / 21k citations / 18k
fetched pages on three platforms). All of that is observable in extracted main text.

**Crawler access splits into two different levers.** Retrieval-time fetching and
training-corpus crawling have different consequences; one study measured ~0% general
knowledge loss from opt-out compliance. So "AI bot blocked = bad" is wrong — severity
depends on which class and on intent.

**Citation errors are large and partly site-controlled.** A study of 1,600 queries found
>60% error overall (37–94% by engine), >50% fabricated URLs on two engines, and systematic
citing of syndicated copies over originals. Canonicalization and link stability are the
slice a site actually controls.

**An unresolved disagreement:** one study (55,936 queries) finds LLM search cites with
*greater* domain diversity than traditional search; others find heavy concentration around
a repeatedly-cited core. These license opposite advice and nobody has reconciled them.
Our position: stay agnostic — audit retrievability and correctness, never citation share.

### Engagement

**Almost every quantified result in this literature was authored or commissioned by a party
selling the answer.** This is the single most important finding in the engagement half.

Specifically untraceable or misattributed, and therefore banned from our output: "1s delay
= 7% of conversions" (Aberdeen 2008, not public); "100ms = 1% of Amazon sales"; the causal
phrasing of Deloitte's 0.1s→8.4% result (that study is explicitly observational); the
3-second bounce threshold (2016 Google/DoubleClick vendor research promoting AMP, never
independently replicated). **CLS has no perception research behind it** — Google's own
threshold documentation says so.

**What survives as mechanically checkable:** the six machine-detectable WCAG failures
(95.9% prevalence — contrast, `alt`, input labels, empty links/buttons, `<html lang>`);
mobile layout integrity (viewport meta, `user-scalable=no`, 375px overflow, WCAG 2.2's
normative 24×24 CSS px tap targets); non-descriptive link text and heading integrity;
content-blocking overlays; blank first paint without JS; and the Better Ads 30% mobile /
50% desktop ad-density thresholds — the only published numeric engagement thresholds
applicable mechanically.

**Confirmed not observable read-only:** bounce, dwell, scroll depth, conversion, task
success, field Core Web Vitals, and real assistive-tech barriers — one CHI 2012 study found
only 50.4% of the problems blind users actually hit map to any WCAG criterion at all.

### Base rates

Web Data Commons (Oct 2024) measured 37.4M domains, with only ~16.5M (44.1%) carrying any
structured data at all. **Two research agents working independently reproduced this same
figure**, which is unusually good corroboration for a load-bearing number. Consequence:
"no JSON-LD" fires on most of the web and would be our dominant false positive if shipped
as a standalone finding.

### Evaluation

**We author both the checks and the gold labels, so every weakness in the matching rule
fails silently in our favour.** SWE-Bench+ found 31% of "successful" patches passed on weak
tests, collapsing a 12.47% headline to 3.97% — roughly 3× inflation from grader leniency
alone. Related work reports estimation errors up to 100% from the same class of bug.

**Findings are not independent samples.** 24 sites × 12 findings is ~90 effective samples,
not 288; naive confidence intervals are too narrow by roughly √3. The unit of analysis must
be the *site*.

**No public dataset exists** of AI-assistant citations, and no curated site-quality label
corpus. Gold labels must be hand-authored.

---

## 6. Settled decisions

| # | Decision |
| --- | --- |
| D-001 | Task context lives in repo files, not chat history |
| D-002 | Research is recorded as mechanisms, never as named example sites |
| D-003 | No check ships without a complete evidence trace and one hand-verified source |
| D-004 | **Evidence strength caps severity** — causal/hard-mechanical → critical; correlational → high; theoretical → medium; contested → low or proactive-only |
| D-005 | The literature review runs as eight parallel domain agents with stored briefs |
| D-006 | **The audit never queries a live generative engine** |
| D-007 | **Prohibited-recommendation list**, enforced in eval |
| D-008 | **The engagement half detects defects; it does not predict engagement** |
| D-009 | Findings are conditioned on base rates and page type |
| D-010 | Evaluation harness backbone (below) |
| D-011 | **`NORMATIVE` is a first-class evidence strength, capped at `high`** — a WCAG or Better Ads violation is a violation of a published standard, not a measured outcome, and saying so plainly beats dressing it up as empirical |
| D-012 | **Proactive recommendations live outside `findings[]`** — `findings[]` stays defects-only as the schema implies, with sibling `recommendations[]` and `limitations[]` arrays. A check demoted under the single-source rule moves to `recommendations[]` rather than disappearing |
| D-013 | **Skills split by mechanism, with network I/O extracted** into `site-evidence-collector`. Full rationale and falsification tests in `docs/ARCHITECTURE.md`, which is authoritative for check ownership. Six skills originally; revised to five by **D-025** (2026-09-04) once Phase 4's merge test had real evidence — see §7 |

### D-007 in full — things we must never recommend

Hidden or retriever-directed text (such attacks demonstrably transfer to live products);
bulk content generation; **`llms.txt` as a substantive fix** — 97% of existing files were
never requested in a 137k-domain measurement, and it is currently the most fashionable GEO
recommendation, so declining to make it is where our audit visibly beats a practitioner
checklist; any promise of citation outcomes; above-the-fold rules; "improve visual design
to build trust" (the aesthetics→usability arrow has failed causal replication and may run
backwards); reading-grade targets (formulas disagree by up to six grade levels on the same
text and are gamed by adding periods); blanket popup removal; Lighthouse-100 chasing;
"accessible sites convert better" (no traceable evidence).

### D-010 in full — the eval harness

Frozen content-addressed site snapshots. The **site** is the unit of analysis, with
site-level cluster bootstrap intervals (Wilson, never Wald). Two independent labellers write
gold *before* seeing output, using a closed `PRESENT`/`ABSENT`/`UNMEASURABLE`/`N/A`
taxonomy; Krippendorff's alpha ≥ 0.80 per check, and any check that can't reach 0.67 is
cut. Strict three-condition matching: same taxonomy node + same canonicalized locus +
**evidence appears verbatim in the snapshot** — severity mismatch is tracked in a confusion
matrix rather than breaking the match. Negative-control false-positive rate ≤ 0.05 per
check. `pass^k`-style all-runs-agree stability at k=5, never a mean. Leave-one-skill-out
paired ablations at matched token budget. Hard, logged 3-look budget on the held-out set.
p95 wall-clock against the 5-minute cap.

**Asymmetric justification rule:** any change to matcher, rubric, or composite that
*raises* scores requires written justification plus a negative-control re-run in the same
commit. Score-lowering changes don't.

**The three metrics that can sink the submission:** clean-site false-positive rate; set
stability at k=5; per-skill ablation delta.

### Corpus plan (from domain 08)

Dev **60 sites** (6 archetype strata × 10, split 3 head / 3 mid / 4 tail by coarse
popularity band — fine ranks are noise). Held-out **30 sites**, drawn in the *same pass* by
continuing the same shuffled walk, so a dev→test drop is interpretable rather than a
sampling artifact. Plus **24 negative controls** (3 each across 8 dimensions, including a
"minimal-by-design one-pager" row) and a **12-site adversarial set** scored only on graceful
degradation. **D-017 later cut dev to 24 sites and held-out to 12**, and separately
redesigned negative-control down to **12 sites, 2 per dimension across 6 dimensions**
(`CORPUS.md`'s current, authoritative text — superseding the 24-site/8-dimension figure
this paragraph originally quoted from domain 08's pre-cut plan). What survived that
redesign as a real, unresolved gap: an R-5 follow-on note (`docs/PROGRESS.md`, Phase 1b
review) had already flagged that adding the off-site identity-anchor dimension
(`CHK-D-025`/`026`/`027`) should add a 7th negative-control dimension — that never
happened, before or after D-017's redesign. Under the current 2-per-dimension scheme, the
gap was **12 → 14 sites**, not the larger 24→27 figure the note's original arithmetic
implied under the pre-cut plan. **Closed 2026-09-04 (D-026):** `offsite_identity` added
with `stripe.com`, `about.gitlab.com` and `www.docker.com`, each selected by fetching and
reading its JSON-LD `sameAs` before the row was written and each run live end to end; none
fires `CHK-D-025`/`026`/`027`. Three rows rather than the uniform two, because qualifying
candidates turned out scarce (8 of 11 reachable well-known sites declare no `sameAs` at all)
and a spare is worth more than the symmetry. The negative control is **15 sites across 7
dimensions** and the corpus is **57**. `CHK-D-026`'s bot-blocked guard (403 →
`resolved: null`, never a finding) was exercised against a real 403 for the first time, on
Stripe's Crunchbase anchor.

Sample size: precision ≈ 0.90 at ±0.05 needs n = 139 findings, but clustering
(`DEFF = 1 + (m−1)ρ`, m≈10, ρ≈0.2 → 2.8) means ~30 sites gives roughly **±6pp** — enough to
distinguish 0.90 from 0.75, not 0.90 from 0.86. Recall is sized separately and smaller
(~±12pp) and is our weakest number.

Access blockers: HTTP Archive needs a billed Google Cloud project; CrUX needs an API key
and excludes small sites (exactly our target population); ClueWeb22 is gated; Tranco's
combined-list licence is unclear. Wayback is unreliable as a fixture source — at most ~17.9%
of composite mementos are both temporally coherent and complete.

---

## 7. Phases — done and remaining

### Phases 1b, 2, 3 — **complete**

Phase 1b turned 102 sources into `docs/RESEARCH.md` and the 27-row evidence ledger (26 checks ship; CHK-E-023 was cut as D-018), then
survived its own review (findings R-1…R-7, all resolved, producing D-011/012/013).
Phase 2 fixed the decomposition deliberately as D-013. Phase 3 authored all six skills (as
they stood then — see §7 for the later merge to five, D-025), the root README, and the
`scripts/` implementing every check.

The Phase 3 design principle held: **everything mechanically decidable went into code** —
robots.txt parsing and agent classification, JSON-LD extraction, viewport meta, tap-target
geometry against WCAG's 24×24 floor, the raw-vs-rendered text diff, the WCAG contrast
formula, and Jaccard near-duplicate comparison.
What is left to model judgment is narrow and named: evergreen-vs-time-sensitive page
classification, archetype labelling, and the wording of suggested actions. Each of those is
a declared threat to set stability and is where Phase 4 should look first if stability
comes back low.

### Phase 4 — Corpus and harness  ← **one item left, gated until 2026-09-12**

Build the driver that walks a real site, snapshot the four sets, screen for false positives,
hand-author gold labels, score, ablate. This is the phase that converts design arguments
into numbers. Its protocol was reduced on 2026-09-04 (**D-017**) from the two-labeller
D-010 harness to a single-labeller one, and the corpus from 129 sites to 54.

**Stages A, A′, B, B′, C are done. The adversarial set has run. Both composition tests
have run (D-025 merged two skills on the result). R-1 (source verification) closed
2026-09-09 (D-027).** Everything that could run without a human labeller has now run —
see §10 for the stage-by-stage record. What remains is gated on human labour in a way
nothing before it was: **Stage D (gold labels)**, not delegable to a model.

**Stage D closed 2026-09-10** at 624/624 rows. **Stage E scored it the same day**
(`docs/evals/stage-e-report.md`), after D-028 repaired a matching rule that had been
returning 0.00 for every check. A four-decision diagnosis pass (**D-029 → D-032**) then went
through every cut-rule trip: three checks had genuine defects and were fixed (`CHK-D-006`,
`CHK-E-014`, `CHK-D-001` — the last a robots.txt parser with no RFC 9309 metacharacter
support, which made a `critical` check report a site as blocking crawlers it explicitly
allows). Trips fell 12 → 8, and **six of the eight now point at gold data or the worksheet
schema rather than at code**, each written up in `docs/evals/adjudication-queue.md` with no
label edited. None have been cut.

**The entire remaining critical path is one task:** the 8-site intra-rater test–retest
(`EVALS.md` §1). `harness/retest.py --emit` has drawn the subset (seeded, logged in
`docs/evals/retest-log.md`) and written a blinded worksheet with every label cell empty. It
needs a human to re-label those 208 cells from the frozen snapshots, **without opening
`gold-labels-dev.csv`**, **≥ 48 h after the first pass** — earliest **2026-09-12**. Then
`harness/retest.py --score` computes Krippendorff's alpha per check and the cut rules become
actionable. Phase 4 closes there.

### Phase 5 — Harden and package

Guardrail and generalization gates, re-copy `docs/BUNDLE-SCHEMA.md` into the collector's
`references/` so the zip is self-contained and cannot drift, final zip (≤50 MB). Also the
last chance to catch anything Phase 4 surfaces.

---

## 8. Open questions

### Settled since the last revision

1. **Decomposition axis and skill count** — settled as D-013 (six skills, split by
   mechanism, network I/O extracted), then **revised by D-025** to five once the deferred
   test below actually ran. `docs/ARCHITECTURE.md` §7 records three falsification tests,
   and is honest that leave-one-skill-out ablation is weak on its own because any disjoint
   partition passes it. The sharper test, **suppression-necessity**, ran against the real
   36-site dev+negative corpus on 2026-09-04: the orchestrator's one cross-skill rule (O-1)
   never fired on any real site, so the merge test that depended on that result also ran —
   `render-extractability-audit` and `engagement-defect-audit` merged into
   `content-engagement-audit`, re-run against all 42 available sites with byte-identical
   output. No longer an open question; full writeup in `docs/DECISIONS.md` D-025.
2. **Off-site corroboration** — settled by adding CHK-D-025/026/027, which audit *the
   anchoring the site itself provides* rather than corroboration itself, and by declaring
   what remains unmeasurable as LIM-01/LIM-02 in every report rather than omitting it.
3. **Severity vocabulary** — settled as D-012: `findings[]` stays defects-only with `low`
   included and counted; proactive items go in a sibling `recommendations[]`; declared
   limitations in `limitations[]`.
4. **Runtime budget allocation** — settled: one shared rendered-page pass across ≤3 pages
   serving seven checks, 220 s subtotal against the 300 s cap with 80 s reserve, and a
   degradation rule that emits `not_determinable` rather than inferring from static HTML.

### Still open

5. **How much of the eval protocol to actually run.** Unchanged and now urgent, because
   Phase 4 is next. The D-010 harness is rigorous but expensive in *human* time: two
   independent labellers, Krippendorff ≥ 0.80. **If gold labels are generated by the same
   class of system that produces the findings, the agreement number is theatre.** What is
   the minimum honest version? Standing instinct: protect the negative-control set above
   everything else, since clean-site false-positive rate is the number most likely to sink
   us.
6. **Is D-008 too conservative?** Framing the engagement half as "detect defects that
   obstruct access and comprehension" rather than "predict engagement" is defensible and
   honest — but the brief literally asks why visitors "don't stay." Does the conservative
   framing under-answer the question as asked, or is it the strongest possible answer given
   the evidence is vendor-authored and correlational?
7. **Worth running domains 02 and 03?** They'd give evidence for *how* to author skills for
   reliability and *how many* skills to have. They don't block anything, and Phase 3 has
   already shipped without them. Lower value now than when this question was first written.
8. **Answered, 2026-09-04: what happens when the checks meet a real site.** This was
   exactly right to flag — the archetype classifier did behave very differently on the open
   web (17% first measurement, root-caused to a harness bug in D-021, 1 confident-wrong
   label of 34 after the fix). CHK-E-023 was cut before this even ran (D-018), for
   unrelated reasons (never executes without a headless browser). What wasn't anticipated:
   the boilerplate-stripping extractor and ad-region detectors turned out *not* to be where
   the real bugs were — the actual surprises were a harness-only JSON-LD parsing bug
   (D-021), ten checks mishandling failed page fetches (D-023), and a robots.txt precedence
   gap (D-024). Full results: `docs/evals/stage-b-report.md`, `stage-c-report.md`,
   D-019–D-024 in `DECISIONS.md`.

---

## 9. Known risks

| Risk | Status |
| --- | --- |
| **R-1: no check has had its sources hand-verified.** The ledger's verification column was self-certified by the authoring tool and has been reset to pending. Per D-003 no check may ship without one hand-verified source. | **Closed 2026-09-09 (D-027).** All 14 `in_minimum_set` sources opened and judged by hand; see §10 |
| **CHK-D-001/002's critical/low severity split rests on a taxonomy no cited source establishes.** R-1 verification confirmed crawler-restriction sources (P-01.03, P-01.12) but neither distinguishes retrieval-time from training-only crawlers — the exact distinction the split depends on. | Open — flagged by R-1 (D-027), not fixed. Needs a citation to vendor crawler docs (OpenAI/Anthropic/Google) or a re-derivation of the split |
| Nothing in the literature measures our actual target quantity — the effect of a specific site-side fix on a specific brand's representation in a specific assistant. That experiment doesn't appear to exist publicly. | Accepted; we build on mechanism-level evidence and the report's language says so |
| The 04 and 06 domain files were produced by a different tool and have had no hand-verification | Open; folded into R-1 |
| SEARCH-ONLY sources include the JS-rendering-gap study — exactly what a crawl strategy wants to lean on | **Mitigated by removing the dependency:** CHK-D-003's severity rule is now definitional (no h1 + <50 raw words vs ≥200 rendered), which needs no effect size, so the search-only source is demoted to a lead |
| The ρ≈0.20 intra-cluster correlation in the sample-size math is assumed, not measured. ρ > 0.4 falsifies the split plan | Open — measurable as a by-product of Phase 4 |
| Budget: an earlier run of 8 concurrent research agents was killed by an account rate limit with zero output | Mitigated — concurrency ≤ 4, incremental writes, briefs stored for replay |
| Human labelling cost for gold data | Open — reduced, not removed, by D-017: one labeller with an 8-site test–retest replaces two independent labellers, and dev drops 60→24 sites. Still the main Phase 4 constraint |
| **One labeller means systematic misreading of the rubric is undetectable.** Test–retest measures consistency, not correctness | Accepted and declared (D-017). Recall is the exposed number; precision is protected by verbatim evidence matching |
| A hand-picked held-out set can be unconsciously easy | Mitigated by sealing it in Stage A′, before any result exists — still sealed, 0 looks taken |
| **Nothing had been run against a real website** — all testing was against synthetic bundles | **Closed.** 42 real sites run (Stages A–C, adversarial); found and fixed D-019 through D-024 |
| The orchestrator's cross-skill logic may never fire in practice, which would make the six-skill decomposition decorative | **Settled (D-016, D-025):** rule O-2 was proven unreachable and removed. O-1 fired in synthetic scenarios but never on the real 36-site corpus, so it did not justify the four-analyser split — `render-extractability-audit` and `engagement-defect-audit` merged into `content-engagement-audit`; five skills now, not six |
| **The negative-control corpus had no off-site-identity dimension.** R-5's follow-on note called for a 7th dimension (`CHK-D-025`/`026`/`027`, declared identity anchors) when that check family was added; it was never created, before or after D-017's later redesign to 2-per-dimension | **Closed 2026-09-04 (D-026).** `offsite_identity` added, 12 → 15 sites: `stripe.com`, `about.gitlab.com` and `www.docker.com`, each pre-screened by fetching its JSON-LD and each run live before the row was written. None fires `CHK-D-025`/`026`/`027`. Three rows, not two — every qualifying candidate was kept as a spare, because the pre-screen is itself the finding: 8 of 11 reachable well-known candidates declare no `sameAs` at all |
| **New (2026-09-04): the evaluation harness itself had bugs that shaped early results.** A harness-only JSON-LD key mismatch (D-021), a harness-only robots.txt Allow-precedence gap (D-024), and a shipped-code bug in how ten checks treated failed page fetches (D-023) were all found only once real sites were run against | Closed per-instance (all fixed, all re-verified against the full corpus), but stands as a general lesson: synthetic-bundle testing and even early real-site testing can both under-detect this class of bug — worth remembering if Stage D's numbers look surprising in either direction |

---
## 10. How checking and evaluation carries on from here

**Its accuracy against real websites is now partly known.** Stages A through C, the
adversarial set, and both composition tests have run; Stage D (the one that would produce
an actual precision/recall number) has not. This section is the plan for finishing that,
in the order that fails cheapest first — written 2026-09-04 as D-017, updated the same day
as each stage below actually ran. `docs/EVALS.md` holds the protocol; `docs/CORPUS.md`
holds the sets; this section holds the order of work and its current status.

### The three numbers that decide the submission

| Metric | Where it comes from | Status |
| --- | --- | --- |
| **Clean-site false-positive rate** | The `ABSENT` labels on the 24-site dev corpus. **Not** the negative-control set, which is a screen and can only report counts | **Not measured — blocked on Stage D.** Target ≤ 0.05 per check |
| **Schema conformance** | Every report emitted, every run, validated against `report-schema.md` | **100%, all 42 sites run to date** (24 dev + 12 negative-control + 6 adversarial). Gating, holding so far |
| **The merge test** | `render-extractability-audit` + `engagement-defect-audit` merged and re-run | **Done, 2026-09-04 (D-025).** Nothing changed — they merged for real, into `content-engagement-audit` |

The previous version of this table named `pass^k` at k=5 and the per-skill ablation delta.
Both are now **reported without a threshold** — `pass^k` because the officials said output
determinism is not graded (`OFFICIALS-QA.md` §2.1), and leave-one-out ablation because
`ARCHITECTURE.md` §7 is explicit that any disjoint partition passes it. The merge test
replaced the ablation as the deciding composition test, and D-016/D-025 narrowed it to,
then resolved, a single candidate pair. Set stability (a k=3 analogue) was also measured on
a 5-site live sample, unthresholded per `EVALS.md` §5: 5/5 stable — see `stage-c-report.md`
§6b.

### Stage A — the harness — **done**

`harness/` (git-ignored, never ships) is a driver that fetches politely, builds the bundle,
runs the analysers, and composes the report — imports the shipped scripts unmodified rather
than reimplementing them, so a bug found here is a bug in the shipped code, not a harness
artifact. `run_audit.py`, `collect.py`, `fetcher.py` and the corpus/output plumbing all
exist and have processed all 42 sites run to date.

### Stage A′ — seal the held-out set — **done, still sealed**

12 sites chosen by the stratification rule and written to `harness/corpus/heldout.csv`
**before any result existed** (`corpus-selection.md`). `holdout-log.md` records zero looks
taken — correctly untouched, since Stage F (the only stage that should spend a look) hasn't
run.

### Stage B — negative-control screen (12 sites) — **done, D-019/D-020/D-023/D-024**

Found and fixed real false-positive mechanisms rather than just screening: total findings
across the 12 sites fell from 356 (first contact) to 88 (after Stage C's fixes). Reported
as **counts, not rates** per `EVALS.md` §3. Full trace: `stage-b-report.md`,
`stage-c-report.md`, and D-019 through D-024 in `DECISIONS.md`.

### Stage B′ — archetype classifier accuracy — **done, D-021**

17% on first measurement (36 sites), with 5 confidently-wrong labels — the dangerous
failure mode, since a wrong label activates suppression rules written for a different kind
of site. Root cause (D-021): a **harness-only** bug reading JSON-LD keys that were never
actually produced, silently killing every structured-data signal for the entire run. Fixed;
confident-wrong labels fell to 1 of 34. Raw accuracy stayed ~21% by design — `unknown` is
the safe answer and most flips landed there rather than on the correct one. No further
`classify_page_type` pattern-tuning was done deliberately, to avoid corpus-fitting.

### Stage C — cut and guard — **done, D-022**

Five checks `stage-b-report.md` flagged were resolved: `CHK-E-014`/`CHK-E-022` accepted
as-is (hand-verified against real HTML, matches cited base rates); `CHK-D-007` severity
capped; `CHK-D-004` excludes `home` page type; `CHK-E-021`/`CHK-D-010` demoted to
`recommendations[]`. All score-lowering, so none needed defence under the
asymmetric-justification rule.

### Stage D — dev corpus gold labels (24 sites) — **not started; tooling ready**

Written blind, before any tool output is seen, using the closed
`PRESENT`/`ABSENT`/`UNMEASURABLE`/`N/A` taxonomy. One labeller with sole authority; a model
may run as a disagreement-finder feeding an adjudication queue, never as a second rater.
Reproducibility comes from an **8-site test–retest** at ≥ 48 h, blind to the first pass.

**This is the schedule's real constraint and the only reason the project isn't further
along.** A packaged, self-contained kit exists to make it tractable —
`dist/gold-labelling-kit.zip`: the 624-row worksheet (24 sites × 26 checks, each row's
exact criteria pre-filled) plus all 24 sites' pages exported as browsable HTML plus a
README with the workflow and the pre-selected 8-site test–retest subset. Cannot be done by
a model; nothing further blocks starting it.

### Stage E — scoring, ablation, merge test, bundle-sufficiency — **partly done**

Strict three-condition matching, cluster-bootstrap intervals, and the severity confusion
matrix all need Stage D and have not run. The three composition tests from `EVALS.md` §7
**have** run, ahead of schedule since they didn't need gold labels: leave-one-skill-out
ablation (`harness/ablation.py`), the merge test (executed for real — D-025), and
bundle-sufficiency (grep-verified, zero networking imports in any analyser).

### Stage F — held-out, at most 3 looks, every look logged — **not started, correctly**

The only number estimating generalization to sites the graders will actually use, and only
meaningful if we never tune against it. Should not run before Stage E's scoring exists —
spending a look before there's a protocol to validate wastes the budget for nothing.

### R-1 — **closed 2026-09-09 (D-027)**

Hand-verification of one cited source per check **gates ship, not measurement**. Opening a
citation does not change what the code does on a real site, so serialising Stages A and B
behind ~20 sources of human reading would have bought nothing — and in fact all of Stages
A through C, the adversarial set, and both composition tests ran without it, confirming
that instinct. A human worked the 14-source `in_minimum_set` in
`docs/evals/r1-verification-worksheet.csv` (greedy set-cover over the 38 cited sources) and
judged each against the ledger's actual claim, not just its existence. Result: 20 of 22
non-cut checks confirmed with adequate support (two citation swaps applied where a
stronger source was found — see D-027); **CHK-D-011** and **CHK-D-013** had zero surviving
support and were demoted to `recommendations[]` rather than cut; **CHK-D-001/002**'s
critical/low crawler-taxonomy split remains an undischarged citation gap, recorded rather
than papered over. Full detail: D-027 in `docs/DECISIONS.md`.

### What to pick up next

In order of what actually unblocks the most: **(1) Stage D gold labelling** — the only
thing standing between here and a real precision/recall number, kit is ready, the only
remaining item on the critical path; **(2)** ~~R-1 source verification~~ — **done
2026-09-09, D-027**; find a citation for CHK-D-001/002's crawler taxonomy as a smaller
follow-up, not blocking; **(3)** ~~close the negative-control corpus gap~~ — **done
2026-09-04, D-026**; **(4)** everything else in §8's "Still open" list is lower-value now
than when first written.

### Standing rules for the rest of the project

- **The report's own meta-evaluation runs on every audit** and its warnings are reported,
  never auto-corrected. A report that edits itself until its own check passes is the exact
  failure mode this project is most careful about.
- **A finding we cannot reproduce is a bug, not a finding.**
- **Prefer cutting a check to shipping one we cannot defend.** 26 defensible checks beat 27
  with one that fires on healthy sites — which is precisely what D-018 did to CHK-E-023.
- **Every number carries how it was obtained.** The corpus is chosen, not sampled from a
  frame; the labels come from one person; recall is the weakest number we report. These
  travel with the results rather than living in a footnote.
