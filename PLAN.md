# Round 3 — Agent Skill Marketplace: Plan & Status

**Self-contained briefing.** Written so someone with no access to this repo can read it
cold, understand the task, see what has been done, and argue usefully about what's left.
Last updated 2026-09-01.

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

**Phase 1 (field research) is 6 of 8 domains complete — ~102 sources.** Nothing has been
built yet: no skills, no manifest, no code.

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
- `docs/DECISIONS.md` — append-only decision log (D-001 … D-010, summarized in §6)
- `docs/PROGRESS.md` — current state and phase plan
- `docs/RESEARCH.md` — mechanism-anchored signals — **still empty, this is the next step**
- `docs/research/EVIDENCE-LEDGER.md` — per-check audit trail — **still empty**
- `docs/EVALS.md`, `docs/CORPUS.md` — **still placeholders**, to be filled from domains 05
  and 08
- `.claude/skills/round3-spec/` and `.claude/skills/project-flow/` — the task and the
  working method, encoded so context survives across sessions

**The immediate gap:** 102 sources are raw research. The synthesis that turns them into a
list of checks with severity rules and false-positive guards has not been done. That is
Phase 1b and it is the critical path.

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

## 7. Remaining phases

### Phase 1b — Synthesis  ← **critical path, next**
Convert 102 sources into `docs/RESEARCH.md` (mechanism-anchored signals) and
`docs/research/EVIDENCE-LEDGER.md` (one row per candidate check: mechanism, sources,
evidence strength, observation procedure with a page budget, the quantitative evidence
sentence, deterministic severity rule, false-positive guard, not-determinable path,
suggested action, runtime cost). Fill `EVALS.md` and `CORPUS.md` from domains 05 and 08.
No new research needed.

### Phase 2 — Architecture
Fix the skill decomposition and the entrypoint's composition contract. Natural split axis
from the research is by mechanism: crawl access → machine readability / render gap → fact
extractability and structured data → entity disambiguation, corroboration, freshness →
engagement defects, plus the orchestrator. Roughly five skills and an entrypoint.

**Constraint that shapes this:** D-010 commits us to leave-one-skill-out ablation, so
boundaries must be *testable*. A skill whose removal doesn't degrade the composite gets
merged. Choosing boundaries you can't ablate is how a marketplace becomes padding.

### Phase 3 — Author the skills
`SKILL.md` per concern (lean), checklists into `references/`, executable checks into
`scripts/`.

**Design principle:** determinism is graded and LLM judgment isn't deterministic. Push
everything mechanically decidable into scripts — robots.txt parsing, JSON-LD presence and
validity, viewport meta, tap-target geometry, no-JS vs rendered text diff, ad density — and
reserve model judgment for the narrow set that genuinely needs it. Every LLM-judged check
is a threat to the `pass^k` stability metric.

### Phase 4 — Corpus and harness
Build the four site sets, snapshot them, run the eval, ablate.

### Phase 5 — Harden and package
Guardrail and generalization gates, marketplace root `README.md`, zip.

---

## 8. Open questions — where a second opinion is most useful

1. **Decomposition axis and skill count.** Is by-mechanism (≈5 skills + entrypoint) right,
   or is there a better axis — by page type? by evidence-gathering stage (fetch → parse →
   judge)? by report section? Given that a single well-built skill scores fully on
   composition, what actually justifies going to five? What's the strongest argument for
   three, or for one?

2. **How much of the eval protocol to actually run.** The D-010 harness is rigorous but
   expensive in *human* time: two independent labellers on 24+ sites, hitting Krippendorff
   ≥ 0.80. If the gold labels are generated by the same class of system that produces the
   findings, the agreement number is theatre. What's the minimum honest version? Our
   instinct is to protect the negative-control set above everything else, since clean-site
   false-positive rate is the number most likely to sink us.

3. **Is D-008 too conservative?** Framing the engagement half as "detect defects that
   obstruct access and comprehension" rather than "predict engagement" is defensible and
   honest — but the brief literally asks why visitors "don't stay." Does the conservative
   framing under-answer the question as asked, or is it the strongest possible answer given
   the evidence is vendor-authored and correlational?

4. **Off-site corroboration and entity disambiguation are unresolved.** The brief's
   appendix stresses that agreement across the wider web matters and that mistaken identity
   is a real failure mode. But measuring either for an arbitrary brand seems to need search
   APIs we don't have free access to. Is there a cheap, read-only, deterministic proxy — or
   do we honestly report these as not determinable?

5. **Severity vocabulary.** The handout's sample shows critical/high/medium. Do we add
   `low`? An `info` tier for proactive recommendations? How are the beyond-defect proactive
   suggestions represented in a schema whose `findings` array implies defects?

6. **Runtime budget allocation.** Under 5 minutes total. How much goes to headless
   rendering (needed for the JS-render-gap check but expensive), how many pages get
   sampled, and how is the sample stratified across page types so that per-page-type
   scoring (D-009) is possible?

7. **Worth running domains 02 and 03?** They'd give evidence for *how* to author skills for
   reliability and *how many* skills to have. They don't block anything. Is the composition
   rubric line worth spending research budget to argue from evidence rather than judgment?

---

## 9. Known risks

| Risk | Status |
| --- | --- |
| Nothing in the literature measures our actual target quantity — the effect of a specific site-side fix on a specific brand's representation in a specific assistant. That experiment doesn't appear to exist publicly. | Accepted; we build on mechanism-level evidence and the report's language must say so |
| The 04 and 06 domain files were produced by a different tool and have had no hand-verification | Open; per D-003 they're leads until spot-checked |
| SEARCH-ONLY sources include the JS-rendering-gap and robots.txt AI-crawler studies — exactly what a crawl strategy wants to lean on | Open; needs verification before those checks ship |
| The ρ≈0.20 intra-cluster correlation in the sample-size math is assumed, not measured. ρ > 0.4 falsifies the split plan | Open |
| Budget: an earlier run of 8 concurrent research agents was killed by an account rate limit with zero output | Mitigated — concurrency ≤ 4, incremental writes, briefs stored for replay |
| Human labelling cost for gold data | Open — see question 2 |
