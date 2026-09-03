# Round 3 — Agent Skill Marketplace: Plan & Status

**Self-contained briefing.** Written so someone with no access to this repo can read it
cold, understand the task, see what has been done, and argue usefully about what's left.
Last updated 2026-09-03.

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

**Phases 1, 1b, 2 and 3 are complete. The marketplace is built.** What exists on disk is a
working six-skill marketplace with 27 checks implemented as tested code, a manifest, and a
root README. What has *not* happened is any evaluation of it against real sites — no
corpus, no gold labels, no measured false-positive rate. Every accuracy claim in this
document is therefore a design argument, not a measurement.

### The marketplace as built (`brand-ai-readiness-audit/`)

| Skill | Role | Checks |
| --- | --- | --- |
| `audit-orchestrator` *(entrypoint)* | Composes the rest; suppression, root-cause dedup, report assembly, budget arbitration, report meta-evaluation | none of its own |
| `site-evidence-collector` | The only skill with network tools. Emits one in-memory evidence bundle | none — observes only |
| `crawl-access-audit` | Mechanism A | D-001, D-002 |
| `render-extractability-audit` | Mechanisms B, C | D-003, D-004, D-005, D-009, D-010, D-011, D-013 |
| `entity-identity-audit` | Mechanism D | D-006, D-007, D-008, D-012, D-025, D-026, D-027 |
| `engagement-defect-audit` | Mechanisms E, F | E-014 … E-024 |

27 checks, disjoint, each traced to a row in `docs/research/EVIDENCE-LEDGER.md`. Every
check is implemented as a pure `evaluate(bundle)` function in that skill's `scripts/`,
stdlib-only Python so the zip needs no dependency install. The collector's scripts do the
parsing and extraction; the network calls themselves stay with the invoking agent's
declared tools, which is what keeps the read-only and budget guarantees structural rather
than promised.

**Tested, not just written:** each module has been exercised against synthetic bundles, and
a full pipeline run (HTML → extraction → four analysers → composed report) confirms the
pieces integrate. That testing found four real bugs, all fixed: a falsy-string check that
silently dropped empty anchors from the accessibility count; a sampling step that ignored
its own per-type cap; a module-name collision (`checks.py` × 4) that would have made
analysers silently load each other's code; and a false positive in the new
meta-evaluation itself, where two checks that legitimately grade one page twice were
flagged as duplicates.

**What testing has *not* done:** none of this has been run against a real website. Synthetic
bundles prove the logic does what it was written to do; they cannot tell us whether the
checks fire correctly on the open web. That is Phase 4 and it is the only thing that can
turn "designed for few false positives" into a number.

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
- `docs/DECISIONS.md` — append-only decision log (D-001 … D-013, summarized in §6)
- `docs/PROGRESS.md` — current state and phase plan, updated per work session
- `docs/ARCHITECTURE.md` — the six-skill decomposition, why this axis, and the three tests
  that would falsify it
- `docs/BUNDLE-SCHEMA.md` — the pinned collector↔analyser contract, with a coverage walk
  proving all 27 checks are satisfiable from it
- `docs/RESEARCH.md` — mechanism-anchored signals — **done**
- `docs/research/EVIDENCE-LEDGER.md` — per-check audit trail, 27 rows + 4 declared
  limitations — **done, except the hand-verification column (see R-1 below)**
- `docs/EVALS.md`, `docs/CORPUS.md` — filled from domains 05 and 08
- `docs/FETCH-STRATEGY.md` — fetch fallbacks, block taxonomy, testing against blocked sites
- `.claude/skills/round3-spec/` and `.claude/skills/project-flow/` — the task and the
  working method, encoded so context survives across sessions

**The immediate gap is no longer synthesis — it is evidence about whether any of this
works.** Two things stand between here and a defensible submission:

1. **R-1 (blocking).** Every row in the evidence ledger still reads
   `Verified by hand: — pending`. The rows were originally self-certified by the tool that
   wrote them, which defeats the control entirely, so they were reset. **A human must open
   at least one cited source per check before it ships.** This cannot be delegated to a
   model — a model certifying its own sourcing is the exact failure the column exists to
   catch.
2. **No measured accuracy.** No corpus, no gold labels, no negative-control run. Until
   Phase 4 runs, the three metrics that can sink the submission (clean-site false-positive
   rate, `pass^k` stability, per-skill ablation delta) are all unmeasured.

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
| D-013 | **Six skills, split by mechanism, with network I/O extracted** into `site-evidence-collector`. Full rationale and falsification tests in `docs/ARCHITECTURE.md`, which is authoritative for check ownership |

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
degradation.

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

Phase 1b turned 102 sources into `docs/RESEARCH.md` and the 27-row evidence ledger, then
survived its own review (findings R-1…R-7, all resolved, producing D-011/012/013).
Phase 2 fixed the decomposition deliberately as D-013. Phase 3 authored all six skills,
the root README, and the `scripts/` implementing every check.

The Phase 3 design principle held: **everything mechanically decidable went into code** —
robots.txt parsing and agent classification, JSON-LD extraction, viewport meta, tap-target
geometry against WCAG's 24×24 floor, the raw-vs-rendered text diff, ad density behind a
two-detector agreement rule, the WCAG contrast formula, Jaccard near-duplicate comparison.
What is left to model judgment is narrow and named: evergreen-vs-time-sensitive page
classification, archetype labelling, and the wording of suggested actions. Each of those is
a declared threat to `pass^k` stability and is where Phase 4 should look first if stability
comes back low.

### Phase 4 — Corpus and harness  ← **critical path, next**

Build the four site sets, snapshot them, hand-author gold labels, run the eval, ablate.
This is the phase that converts design arguments into numbers, and it is gated on human
labour (two independent labellers) in a way the previous phases were not. See §10.

### Phase 5 — Harden and package

Guardrail and generalization gates, re-copy `docs/BUNDLE-SCHEMA.md` into the collector's
`references/` so the zip is self-contained and cannot drift, final zip (≤50 MB). Also the
last chance to catch anything Phase 4 surfaces.

---

## 8. Open questions

### Settled since the last revision

1. **Decomposition axis and skill count** — settled as D-013: six skills, split by
   mechanism, network I/O extracted. `docs/ARCHITECTURE.md` §7 records three falsification
   tests, and is honest that leave-one-skill-out ablation is weak on its own because any
   disjoint partition passes it. The sharper test is **suppression-necessity**: count how
   often the orchestrator's cross-skill logic actually fires across the dev corpus. If it
   never fires, the orchestrator is a concatenator and the decomposition is decorative.
   That test is unrun and is a Phase 4 deliverable.
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
8. **New: what happens when the checks meet a real site.** Every accuracy property claimed
   here is a design argument tested against synthetic bundles. The archetype classifier,
   the boilerplate-stripping extractor, and the ad-region detectors are the three most
   likely to behave differently on the open web than in fixtures, and CHK-E-023 is flagged
   in `BUNDLE-SCHEMA.md` as the most false-positive-prone check of the 27.

---

## 9. Known risks

| Risk | Status |
| --- | --- |
| **R-1: no check has had its sources hand-verified.** The ledger's verification column was self-certified by the authoring tool and has been reset to pending. Per D-003 no check may ship without one hand-verified source. | **Open and blocking.** Cannot be delegated to a model — see §10 |
| Nothing in the literature measures our actual target quantity — the effect of a specific site-side fix on a specific brand's representation in a specific assistant. That experiment doesn't appear to exist publicly. | Accepted; we build on mechanism-level evidence and the report's language says so |
| The 04 and 06 domain files were produced by a different tool and have had no hand-verification | Open; folded into R-1 |
| SEARCH-ONLY sources include the JS-rendering-gap study — exactly what a crawl strategy wants to lean on | **Mitigated by removing the dependency:** CHK-D-003's severity rule is now definitional (no h1 + <50 raw words vs ≥200 rendered), which needs no effect size, so the search-only source is demoted to a lead |
| The ρ≈0.20 intra-cluster correlation in the sample-size math is assumed, not measured. ρ > 0.4 falsifies the split plan | Open — measurable as a by-product of Phase 4 |
| Budget: an earlier run of 8 concurrent research agents was killed by an account rate limit with zero output | Mitigated — concurrency ≤ 4, incremental writes, briefs stored for replay |
| Human labelling cost for gold data | Open — see §10; this is the main Phase 4 constraint |
| **Nothing has been run against a real website.** All testing to date is against synthetic bundles. | Open — the entire point of Phase 4 |
| The orchestrator's cross-skill logic may never fire in practice, which would make the six-skill decomposition decorative | Open — the suppression-necessity test in Phase 4 settles it, and the answer might be "merge skills" |

---

## 10. How checking and evaluation carries on from here

The build is done; **nothing about its accuracy is known yet.** This section is the plan for
finding out, in the order that fails cheapest first.

### The three numbers that decide the submission

Everything below exists to produce these, and they are worth stating before the method:

| Metric | Why it can sink us | Target |
| --- | --- | --- |
| **Clean-site false-positive rate** | The rubric penalizes false positives as hard as misses, and a report that cries wolf on a healthy site discredits every other finding in it | ≤ 0.05 per check on the negative-control set |
| **`pass^k` set stability at k=5** | Instability means the audit's answer depends on luck, which is fatal to "deterministic" and to a reader's trust | all 5 runs agree, never a mean of 5 |
| **Per-skill ablation delta** | If removing a skill doesn't degrade the composite, the decomposition is padding and D-013 was wrong | every skill's removal measurably hurts |

### Stage 0 — Hand-verification (R-1), blocking, human-only

Before any measurement is worth taking: **a person opens at least one cited source per
check** and marks the ledger row. 27 checks, and many share sources, so the real count is
closer to 20 distinct sources. This is not a formality — the column was previously
self-certified by the tool that wrote the rows, and a model verifying its own citations is
exactly the failure the control exists to catch. **No amount of Phase 4 rigour compensates
for skipping this**, because a check resting on a misread source can be perfectly stable,
perfectly precise, and still wrong.

### Stage 1 — Negative controls first, not last

Run the marketplace against the 27 clean/negative-control sites **before** building the
full dev corpus. Rationale: the cheapest possible refutation. If checks fire on sites that
are fine, we learn it in an afternoon and fix guards before investing in gold labels.
Ordering this first is deliberate — it front-loads the number most likely to sink us.

Specific suspects to watch, already flagged in the design:
- **CHK-E-023 (ad density)** — named in `BUNDLE-SCHEMA.md` as the most FP-prone of the 27,
  which is why it needs two independent detectors to agree
- **CHK-D-006/D-010/D-011** — heuristic text patterns; likeliest to misfire on prose styles
  the regexes weren't written for
- **The archetype classifier** — a wrong vertical activates suppression rules written for a
  different kind of site, so its errors propagate rather than staying local

### Stage 2 — Gold labels on the dev corpus, written blind

24+ dev sites, **two labellers working independently**, labels written *before* seeing any
tool output, using the closed `PRESENT`/`ABSENT`/`UNMEASURABLE`/`N/A` taxonomy. Krippendorff's
alpha ≥ 0.80 per check; a check that cannot reach 0.67 is cut rather than shipped on a
label nobody can reproduce.

**The integrity constraint that makes this worth doing at all:** if the labels are produced
by the same class of system that produces the findings, the agreement number measures
nothing. The two labellers must not coordinate, and neither should look at the audit's
output first. This is why it is human work and why it is the schedule's real constraint.

### Stage 3 — Scoring, honestly

Strict three-condition matching: same taxonomy node, same canonicalized locus, **evidence
string appears verbatim in the snapshot**. Severity mismatches go in a confusion matrix
rather than silently breaking or granting a match. The **site** is the unit of analysis with
cluster bootstrap intervals — 24 sites × 12 findings is ~90 effective samples, not 288, and
naive intervals are too narrow by roughly √3.

**The asymmetric-justification rule applies from here on:** any change to matcher, rubric,
or composite that *raises* scores needs written justification plus a negative-control re-run
in the same commit. Score-lowering changes don't. This is the guardrail against the
SWE-Bench+ failure — 31% of "successful" patches passing on weak tests, collapsing a 12.47%
headline to 3.97%.

### Stage 4 — Ablation and the suppression-necessity test

Leave-one-skill-out at matched token budget. But per `ARCHITECTURE.md` §7, that test is
weak on its own — any disjoint partition passes it, because removing a skill mechanically
removes its checks. **The sharper question is how often the orchestrator's cross-skill
logic actually fires** across the dev corpus. If suppression (O-1) and root-cause dedup
(O-2) never trigger on real sites, the orchestrator is a concatenator and the honest
response is to merge skills before submitting, not to defend the count.

### Stage 5 — Held-out, once, with the looks logged

30 held-out sites, **hard 3-look budget, every look logged.** Peeking converts a held-out
site into a dev site permanently. This is the number that estimates generalization to the
unseen sites the graders will actually use, and it is only meaningful if we do not tune
against it.

### Standing rules for the rest of the project

- **The report's own meta-evaluation runs on every audit** and its warnings are reported,
  never auto-corrected. A report that edits itself until its own check passes is the exact
  failure mode this project is most careful about.
- **A finding we cannot reproduce is a bug, not a finding.**
- **Prefer cutting a check to shipping one we cannot defend.** 26 defensible checks beat 27
  with one that fires on healthy sites.

