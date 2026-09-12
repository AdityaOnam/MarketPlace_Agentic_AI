# Decisions

Append-only log of settled choices. A future session reads this instead of re-opening
the same debates. Never edit an old entry — add a new one that supersedes it.

Format:

```
## D-00N — <decision, in one line>
Date: YYYY-MM-DD
Context: what forced the choice
Decision: what we chose
Reason: why, tied to the handout/rubric where possible
Consequences: what this now constrains
Supersedes: D-00M (if any)
```

---

## D-001 — Task context lives in repo skills, not in chat history

Date: 2026-09-01
Context: The Round 3 handout is a take-home spec worked on across many sessions; chat
context is lost between them.
Decision: The handout is copied to `docs/round3-handout.pdf`, distilled into the
`round3-spec` skill (with a full transcription under `references/`), and the working
method is captured in the `project-flow` skill. `docs/PROGRESS.md`, `docs/DECISIONS.md`,
and `docs/RESEARCH.md` carry the mutable state.
Reason: Retaining task fidelity and flow across sessions; the rubric rewards precision
about the spec (exactly one entrypoint, required schema fields, guardrails) that is easy
to lose to paraphrase drift.
Consequences: Every session starts with the orientation ritual in `project-flow`. The
PDF is authoritative; the skill is kept in sync with it.

## D-002 — Research notes are recorded as mechanisms, never as site examples

Date: 2026-09-01
Context: The handout requires field research but grades only on unseen sites, and
explicitly warns against fit-to-examples.
Decision: `docs/RESEARCH.md` records findings as *mechanism → signal → check → evidence
shape → severity → false-positive guard*. No domain names, brands, or site-specific
selectors enter the repo.
Reason: Generalization is a rubric line and is "tested by construction"; site-specific
notes invite hard-coding.
Consequences: Any check that can only be expressed against a named site is rejected or
generalized before it ships.

## D-003 — Every shipped check must trace to a documented mechanism

Date: 2026-09-01
Context: The handout gives no checklist and grades on unseen sites; checks invented from
SEO folklore or fitted to observed examples are the predictable failure mode.
Decision: A check ships only when `docs/research/EVIDENCE-LEDGER.md` holds a complete row
for it — mechanism, cited sources, evidence strength, observation procedure with a page
budget, the quantitative evidence sentence, a deterministic severity rule, a
false-positive guard, a not-determinable path, the suggested action, and runtime cost —
with at least one supporting source hand-verified, not merely agent-reported.
Reason: Makes detection accuracy and generalization arguable from evidence rather than
asserted, and forces every check to declare when it must stay silent.
Consequences: Literature review (`docs/research/`) is a prerequisite for Phase 2, not a
parallel nicety. Checks supported only by `SEARCH-ONLY` sources are leads, not
justifications.

## D-004 — Evidence strength caps severity

Date: 2026-09-01
Context: Most on-site-engagement evidence is correlational, and much of the widely-cited
web-performance material is industry research without a traceable primary source. Calling
a weak correlation "critical" is exactly the kind of false positive the rubric penalizes.
Decision: Severity is capped by the strength of the evidence behind the check — causal or
hard-mechanical up to critical, correlational up to high, theoretical/practitioner up to
medium, contested or single-study to low or proactive-recommendation only. Recorded in
`docs/research/EVIDENCE-LEDGER.md`.
Reason: Detection accuracy is graded on false positives as well as misses, and severity
inflation is a false positive in everything but name.
Consequences: Every check must declare its evidence strength before it can be assigned a
severity. Engagement findings will mostly cap at high.

## D-006 — The audit never queries a live generative engine

Date: 2026-09-01
Context: The obvious way to test "is this brand cited?" is to ask an assistant. Domain 01
found that visibility is a *distribution* across runs, prompts, and time
(arXiv 2604.07585), not a fact.
Decision: The audit observes site-side properties only. No live query to ChatGPT,
Perplexity, Gemini, or any generative search product during a run.
Reason: Live querying would break determinism, the <5-minute budget, and reproducibility
simultaneously — three graded properties at once.
Consequences: We audit *retrievability and correctness of what the site exposes*, never
citation share or observed citation outcomes. Load-bearing; do not revisit casually.

## D-007 — Prohibited-recommendation list, enforced in eval

Date: 2026-09-01
Context: The fashionable GEO advice is partly manipulative and partly unevidenced.
Recommending it would be a false positive with a reputational edge.
Decision: The marketplace must never recommend: hidden or retriever-directed text
(Pfrommer et al., EMNLP 2024 — such attacks transfer to Perplexity); bulk content
generation; **llms.txt as a substantive fix** (97% of existing files were never requested
in a 137k-domain May 2026 measurement); any promise of citation outcomes; above-the-fold
rules; "improve visual design to build trust" (the aesthetics→usability arrow has failed
causal replication and may run backwards); reading-grade targets (formulas disagree by up
to six grade levels on the same text); blanket popup removal; Lighthouse-100 chasing;
"accessible sites convert better" (no traceable evidence).
Also banned as untraceable or misattributed statistics: "1s delay = 7% of conversions"
(Aberdeen 2008, not public), "100ms = 1% of Amazon sales", causal phrasing of Deloitte's
0.1s→8.4% result (explicitly observational), the 3-second bounce threshold (2016
Google/DoubleClick vendor research promoting AMP, never independently replicated), and the
9.2mm tap-target figure (use WCAG 2.2's normative 24×24 CSS px instead).
Reason: Declining to recommend llms.txt in particular is where our audit visibly beats a
practitioner checklist.
Consequences: The eval harness tests for these explicitly — emitting one is a hard failure,
not a style issue.

## D-008 — The engagement half detects defects, it does not predict engagement

Date: 2026-09-01
Context: Domain 07's central finding — almost every quantified result in the web-engagement
literature was authored or commissioned by a party selling the answer, and CLS has no
perception research behind it (Google's own threshold documentation says so).
Decision: The on-site half is framed as *detecting defects known to obstruct access and
comprehension*, never as predicting bounce, dwell, or conversion.
Reason: We cannot observe engagement outcomes read-only, and the evidence linking page
properties to those outcomes is correlational and vendor-authored. Claiming prediction
would be a false positive at the framing level.
Consequences: Tier-1 engagement checks are the statically detectable ones — the six
machine-detectable WCAG failures (95.9% prevalence), mobile layout integrity
(viewport meta, `user-scalable=no`, 375px overflow, 24×24px tap targets), non-descriptive
link text and heading integrity, content-blocking overlays, blank first paint without JS,
and the Better Ads 30% mobile / 50% desktop ad-density thresholds (the only published
numeric thresholds applicable mechanically). Bounce, dwell, scroll depth, conversion, task
success, field CWV, and real assistive-tech barriers are recorded as not observable —
Power et al. (CHI 2012) found only 50.4% of problems blind users hit map to any WCAG
criterion.

## D-009 — Findings are conditioned on base rates and page type

Date: 2026-09-01
Context: Web Data Commons (Oct 2024) measured 2.39B URLs across 37.4M domains with only
16.5M carrying any structured data at all.
Decision: Absence of a common-but-not-universal feature is not a finding on its own. Every
check declares the base rate it is judged against, and scoring is per page type, never
pooled.
Reason: "No JSON-LD" fires on most of the web and would be our dominant false positive.
Pooled scoring hides the same failure mode — firing "no statistics / no procedural steps"
on About, contact, and pricing pages, where the absorption features from domain 01 don't
apply.
Consequences: Page-type classification is a prerequisite for the content checks, not an
optional refinement.

## D-010 — Evaluation harness backbone

Date: 2026-09-01
Context: Domain 05 (31 sources). We author both the checks and the gold labels, so every
matcher weakness fails silently in our favour — SWE-Bench+ found 31% of "successful"
patches passed on weak tests, collapsing a 12.47% headline to 3.97%.
Decision: Frozen content-addressed site snapshots; the **site** is the unit of analysis
with site-level cluster bootstrap intervals; two independent labellers write gold *before*
seeing output using a closed `PRESENT`/`ABSENT`/`UNMEASURABLE`/`N/A` taxonomy, requiring
Krippendorff's alpha ≥ 0.80 per check (a check that can't reach 0.67 is cut); strict
three-condition matching (same taxonomy node + same canonicalised locus + evidence verbatim
in the snapshot), severity mismatch tracked in a confusion matrix rather than breaking the
match; negative-control false-positive rate ≤ 0.05 per check; pass^k-style all-runs-agree
stability at k=5, never a mean; leave-one-skill-out paired ablations at matched token
budget; hard logged 3-look budget on the held-out set; p95 wall-clock against the 5-minute
cap.
Asymmetric-justification rule: any change to matcher, rubric, or composite that *raises*
scores requires written justification plus a negative-control re-run in the same commit.
Score-lowering changes don't.
Reason: The three metrics that can sink the submission are clean-site false-positive rate,
set stability at k=5, and per-skill ablation delta.
Consequences: Findings are not independent samples — 24 sites × 12 findings is ~90
effective samples, not 288; naive intervals are too narrow by roughly √3. Sample-size floor
is ~24 dev sites (±7.4 pp on precision at ρ=0.2); below ~12 sites we report counts, not
rates.

## D-011 — `NORMATIVE` is a first-class evidence strength, capped at high

Date: 2026-09-02
Context: Phase 1b review (R-3). Several engagement checks rest on published standards —
WCAG success criteria, the Better Ads Standards — rather than on measured effect sizes.
D-004's vocabulary forced these into `CORRELATIONAL`, which misdescribes them.
Decision: `NORMATIVE` is added as an evidence strength: the check detects violation of a
published, citable standard. The standard is the authority; we do not claim a measured
outcome. Ceiling is `high` — a normative violation is real but is not, on its own, evidence
of an effect on any user.
Reason: Lets accessibility and ad-density checks be stated accurately instead of dressed up
as empirical findings, which would be a false positive at the framing level.
Consequences: Suggested actions for `NORMATIVE` checks cite the criterion (e.g. "WCAG 2.2
SC 1.4.2") rather than an outcome claim. Applied to CHK-E-020, re-grounded on SC 1.4.2.

## D-012 — Proactive recommendations live outside `findings[]`

Date: 2026-09-02
Context: Phase 1b review (R-7). The brief requires suggested actions that "go beyond the
detected problems", but the required schema's `findings` array implies a defect for every
entry. Six checks emit `low`, and two now ship as recommendations rather than findings.
Decision: The report keeps `findings[]` exactly as the schema requires — every entry a
detected defect, severity in {critical, high, medium, low}, and `low` counted in the
severity summary. Beyond-defect proactive improvements go in a sibling top-level
`recommendations[]` array, each with `summary`, `priority`, `rationale`, and the mechanism
it strengthens. Declared limitations (LIM-01…LIM-04) go in a third top-level `limitations[]`
array.
Reason: The schema is explicitly "a floor, not a ceiling — you may add fields". Putting a
non-defect in `findings` would inflate `total_findings` and misrepresent the audit; putting
it nowhere would forfeit the rubric's beyond-problem credit.
Consequences: `summary.total_findings` counts defects only. Recommendations and limitations
are counted separately. A check demoted under the single-source rule (D-011's companion
rule) moves from `findings[]` to `recommendations[]` rather than disappearing.

## D-013 — Six skills, split by mechanism, with network I/O extracted

Date: 2026-09-02
Context: Phase 1b review (R-6) found the ledger had assigned all checks to a single
`marketplace_auditor` by default, making the composition decision by accident. The rubric
grades decomposition as genuine separation of concerns and explicitly penalizes padding,
while allowing a single well-built skill to score fully.
Decision: `site-evidence-collector` (the only skill with network tools), four mechanism
analysers (`crawl-access-audit`, `render-extractability-audit`, `entity-identity-audit`,
`engagement-defect-audit`), and `audit-orchestrator` as the entrypoint. Full rationale,
composition contract, and check map in `docs/ARCHITECTURE.md`, which is **authoritative for
check ownership** over the ledger's `Owning skill` column.
Reason: The mechanism axis is the brief's own ontology (appendix A–F), and each mechanism
carries a different evidence type and severity ceiling. Extracting network I/O makes the
<5-minute budget and the shared render pass (R-4) structurally enforceable rather than
conventional, and makes the analysers pure functions from bundle to findings — which is what
makes D-010's `pass^k` determinism achievable.
Consequences: No skill except the collector declares a network tool. Analysers are blind to
each other, so cross-skill suppression and root-cause dedup become the orchestrator's
defined responsibility rather than emergent behaviour. Three falsification tests are
recorded in ARCHITECTURE.md §7, including the admission that leave-one-skill-out ablation is
weak on its own because any disjoint partition passes it — if the suppression-necessity test
shows the orchestrator never fires, the decomposition is decorative and gets merged.

## D-005 — The literature review runs as eight parallel domain agents

Date: 2026-09-01
Context: ~100 sources are needed across discoverability, engagement, agent design,
composition, evaluation, and corpus methodology. Serial review is too slow and mixing
domains in one pass produces shallow coverage.
Decision: Eight domain agents, each with a fixed per-source schema and a strict
anti-fabrication protocol (real retrieved URL required; VERIFIED vs. SEARCH-ONLY;
peer-reviewed vs. industry; causal vs. correlational; drop rather than guess). Briefs are
stored verbatim in `docs/research/AGENT-BRIEFS.md` so the run is reproducible.
Reason: The review is the foundation for every check; it has to be re-runnable and
auditable, and agent-reported sources must be distinguishable from verified ones.
Consequences: Relaunching or extending the review is a copy-paste operation, not a
re-derivation. First launch (2026-09-01) failed on an account session rate limit before
any agent wrote output — see `docs/PROGRESS.md`.

## D-014 — llms.txt: keep the refusal, surface it visibly

Date: 2026-09-03
Context: The officials' Q&A (`docs/OFFICIALS-QA.md` §2.8) confirmed recommending llms.txt
is acceptable in their view ("your audit report could say, hey, this site doesn't have it,
so one recommendation is to add it"). D-007 bans recommending it as a substantive fix on
measured evidence: 97% of existing llms.txt files were never requested across a
137k-domain measurement. A silent omission is indistinguishable from having missed it — the
same risk the officials raised unprompted about AI-generated bloat and about a report not
looking beyond common-denominator advice.
Decision: Keep D-007's refusal — llms.txt is never recommended as a substantive fix — but
state the position visibly rather than saying nothing. Implemented as a fifth *static*
declared limitation, **LIM-05**, always present in `limitations[]` alongside LIM-01…04
(`compose_report.py`'s `DECLARED_LIMITATIONS`), not as a per-site `recommendations[]` entry
and not as a new check. Two reasons for `limitations[]` over `recommendations[]`: (1) this
is a standing policy statement about the audit's own scope, not a per-site defect or a
proactive improvement targeted at one site's evidence, matching LIM-01…04's shape; (2) the
meta-evaluation's D-007 prohibited-recommendation regex scans `findings[]` and
`recommendations[]` action text for the literal string "llms.txt" — routing the disclosure
through `recommendations[]` would trip that scanner on a false positive (declining to
recommend something and recommending it both contain the same substring). `limitations[]`
is not scanned by that check, so no special-casing of the regex was needed.
Reason: This converts a possible perceived miss into a demonstrated piece of judgement — the
official phrasing was permissive ("could be"), not mandatory, and our evidence-based refusal
is exactly the "beyond the common denominator" reasoning the officials said differentiates
submissions, as long as it is stated rather than silently applied.
Consequences: `meta_evaluate`'s limitations-present check (already comparing
`len(report["limitations"])` against `len(DECLARED_LIMITATIONS)` rather than a hardcoded
count) now expects 5, not 4, with no code change required beyond the list itself and its
warning-message text.

## D-015 — No headless-browser tool in the grading sandbox: one-sided re-derivation, not silence

Date: 2026-09-03
Context: The officials' Q&A §1.1 confirmed Playwright/any headless browser will not run in
the grading sandbox — `rendered[]` is structurally empty for every graded run, not
occasionally absent. Checking the actual code (not just the docs) showed the existing
degrade-to-`not_determinable` behaviour has a second, unaddressed problem: `not_determinable`
envelopes never reach the assembled report (`compose_report.py`'s
`split_findings_recommendations` only keeps `state == "present"`), so a check that always
resolves `not_determinable` disappears from every sandbox report with no trace, unless its
stage is separately marked `abandoned` in `budget.stages` — which nothing in the collector's
procedure previously instructed for the "tool doesn't exist" case, only for a mid-run
timeout.
Decision: Two changes.
  1. **Re-derive one-sidedly, not two-sidedly, for CHK-D-003 and CHK-E-019.** When
     `rendered[]` has no entry for the homepage, both checks now evaluate the static-only
     half of their mechanism directly (raw HTML with no h1 and <50 words; noscript +
     static text volume) instead of returning `not_determinable` unconditionally. Severity
     is capped one tier below the two-sided result (`high`, not `critical`) because the
     evidence is incomplete — it proves the static fetch is empty, not that rendering
     specifically fixed it.
  2. **The collector must declare the render-pass gap structurally, not let it go silent.**
     `site-evidence-collector`'s procedure now requires recording a `render_pass` entry in
     `budget.stages` with `abandoned: true` (at zero elapsed time) whenever
     `headless_browser` is unavailable for the whole run — the same field `compose_report.py`
     already reads to populate `degraded_stages[].affected_checks`. This was previously only
     written for a mid-run timeout.
  CHK-E-014's contrast sub-check, CHK-E-015's overflow sub-check, CHK-E-016, CHK-E-018, and
  CHK-E-023 have no defensible static proxy (confirmed against the officials' Q&A, which
  names CHK-E-016/E-023 as unmeasurable outright) and are not re-derived; they stay
  `not_determinable` and rely entirely on fix 2 to be visible in the report.
Reason: "No meaningful static content is still a finding, we just can't confirm the
rendered version is fine" (OFFICIALS-QA.md §1.1) requires code that actually reaches the
static-only branch, not just a doc claim that graceful degradation exists. Verified against
synthetic bundles: a sparse-static/no-renderer bundle now fires CHK-D-003/E-019 at `high`;
a rich-static/no-renderer bundle correctly stays `not_determinable`; a renderer-present
bundle reproduces the prior two-sided behaviour unchanged.
Consequences: `docs/research/EVIDENCE-LEDGER.md`, `docs/BUNDLE-SCHEMA.md`, and both
analysers' `references/checks.md` updated to document the one-sided branches and the
`degraded_stages[]` visibility mechanism. No change to `crawl-access-audit` or
`entity-identity-audit` — neither reads `rendered[]`.

## D-016 — JS-only four-way root-cause dedup (rule O-2) removed: proven unreachable

Date: 2026-09-03
Context: Item 3 of the officials' Q&A action list asks the six-skill count to be
*demonstrably* justified, and names `ARCHITECTURE.md` §7's suppression-necessity test —
counting how often the orchestrator's cross-skill logic actually fires — as the sharper
test to run. The full test needs the Phase 4 dev corpus, which doesn't exist yet, but
checking `compose_report.py`'s `dedup_js_only_cluster` (rule O-2) against the other three
checks it depends on found the answer doesn't need a corpus at all: `CHK-D-003` and
`CHK-E-019` both fire only when the homepage's raw `main_text_words < 50`; `CHK-D-005`
requires `main_text_words > 500` on a page before it evaluates at all
(`render_extractability_checks.py`'s `check_d005`, `if words <= 500: continue`). Those two
thresholds cannot both hold for one page's own word count, so the documented four-way
pattern (D-003 + D-004 + D-005 + E-019 all `present` at the homepage) can never occur —
independent of any corpus, provable from the check definitions as written. Separately,
`CHK-D-004` already self-suppresses on the homepage whenever `CHK-D-003` fires
(`check_d004`'s `d003_result` parameter), which was its own FP guard, authored
independently of O-2, and which alone already prevents the "four findings for one defect"
failure O-2 existed to solve.
Decision: Removed `dedup_js_only_cluster`, `JS_ONLY_CLUSTER`, `JS_ONLY_DEDUP_TITLE`, and
the `consequences` field mechanism from `compose_report.py`. Kept rule O-1 (`CHK-E-019`
defers to `CHK-D-003`, expressed as `state: "suppressed"` / `suppressed_by`), which a
synthetic-bundle run of the suppression-necessity test (5 hand-built scenarios standing in
for the not-yet-built dev corpus) confirmed does fire, including under D-015's
no-headless-browser sandbox condition. Updated every doc that described the old four-way
collapse: `ARCHITECTURE.md` §4.3/§7, `audit-orchestrator/SKILL.md` and
`references/report-schema.md`, both analysers' `SKILL.md`/`references/checks.md`, and the
root `README.md`'s "novelty" claims.
Reason: `ARCHITECTURE.md` §7 pre-committed to exactly this outcome — "if these rules never
fire... the decomposition is decorative" — and the project's own working rule is to cut a
check (or, here, a rule) we cannot defend rather than ship one resting on an untested
claim. Leaving O-2 in the marketplace would have been indistinguishable, to a reviewer
reading the code, from bloat the officials explicitly warned about: "it tends to overdo
things, and could end up adding a lot of extra skills [or logic] which don't add value."
Consequences: The orchestrator's genuine cross-skill surface is now one rule (O-1), not
two. `ARCHITECTURE.md` §7 records this as a partial, corpus-independent result and leaves
open — rather than deciding on five synthetic scenarios — whether one rule is enough to
justify keeping `render-extractability-audit` and `engagement-defect-audit` as separate
skills, to be revisited once Phase 4's real dev-corpus numbers exist. No finding output
changes for any report: O-2 never fired in practice, so no report ever depended on
`consequences` existing.

## D-017 — Phase 4 runs a reduced, single-labeller evaluation protocol; D-010's human-scaled components are cut, not deferred

Date: 2026-09-04

Context: D-010 specified an evaluation harness sized for a team with two independent
labellers and unlimited wall-clock. Phase 4 is now the critical path with one human. Three
of D-010's components were also invalidated by evidence that arrived after it was written:
the officials' Q&A (§2.1) says run-to-run output determinism is not graded ("we are not
looking for deterministic standard output… it is the structure that you need"); D-015
removed `rendered[]`, which halves what a snapshot even contains; and re-reading the
harness against the code found the abstention-calibration metrics (ECE over confidence
bins) were specified against a probabilistic system we did not build — the checks emit
discrete states and there is no confidence bin to calibrate.

A fourth correction is ours, not the officials'. `PLAN.md` §10 named the negative-control
run as the source of the headline clean-site false-positive rate. It cannot be, at any
scale we can afford: a negative-control site is curated clean on **one named dimension**
(this is why `CORPUS.md` sized it 3 sites × 9 dimensions), so a check firing outside that
dimension is an unlabelled finding, not a false positive. 12–27 clean sites give 1–3
observations per check-dimension cell — enough to catch a check that fires on every clean
site, not enough to separate an FP rate of 0.05 from 0.15.

Decision: Phase 4 runs the protocol in `docs/EVALS.md` as rewritten on this date, against
the corpus in `docs/CORPUS.md` as resized on this date. Specifically:

  1. **The clean-site FP rate is sourced from `ABSENT` labels on the gold-labelled dev
     corpus**, where every check gets a per-site verdict. Negative controls still run
     first, but as a **screen, not a measurement** — a cheap catastrophic-FP refutation
     bought for an afternoon before a week of labelling. Nothing may be claimed as a rate
     from the screen.
  2. **`pass^k` all-runs-agree at k=5 is cut as a gate.** Demoted to a reported number with
     no threshold and no architectural consequence, measured once at k=3 on 5 sites and
     reported as counts. The gate it vacates is **schema conformance = 100%** across every
     run — cheap, mechanical, and the thing actually graded.
  3. **Inter-rater agreement (two labellers, Krippendorff ≥ 0.80) is cut.** Replaced by
     **intra-rater test–retest** on a random 8-site subset, second pass ≥ 48 h later, blind
     to the first. A check the labeller cannot reproduce against themselves (α ≤ 0.67) is
     cut. A model may run as a **disagreement-finder** — it produces a queue of check/site
     cells for the human to adjudicate — but its output never becomes a label.
  4. **Abstention calibration (coverage ≥ 0.70, abstention precision ≥ 0.60, ECE ≤ 0.10) is
     cut entirely.** Replaced by one descriptive count: `not_determinable` per site, no
     target.
  5. **The 3-judge, 3-model-family advice panel is cut** to a single-model pass over the
     five binary criteria plus a human read of the full advice set on 5 sites. Two things
     stay hard: criterion 5 (non-manipulative) at 1.00 blocking, already mechanised in
     `meta_evaluate` against D-007's list, and a new mechanical check that every finding's
     suggested action names its own locus — the officials called out disconnected fixes
     explicitly (`OFFICIALS-QA.md` §3.4).
  6. **Pinned sampling frames (Tranco list ID, Common Crawl domain graph) are cut.**
     Replaced by a hand-picked stratified sample with the selection rule and rejection log
     recorded, and an explicit declaration attached to every reported number: *these
     estimate performance on a sample we chose, not a population rate.*
  7. **Corpus resized 129 → 54 sites** (dev 60→24, held-out 30→12, negative control 27→12,
     adversarial 12→6). Dev's 60 was sized for check *discovery*; the checks are already
     authored, so that function is gone and 24 is D-010's own labelling floor.
  8. **Snapshots lose their rendered half** (D-015) and collapse to HTTP response + headers
     + robots.txt.

Kept unchanged from D-010, without exception: frozen content-addressed snapshots, the
**site** as the unit of analysis with cluster-bootstrap intervals, strict three-condition
matching with evidence verbatim in the snapshot, the severity confusion matrix, the logged
3-look held-out budget, and the **asymmetric-justification rule**. Every one of these is
code rather than human hours, and they are the controls that stop us grading our own
homework.

Reason: The cut components divide cleanly into three groups, and it matters which is which.
(a) Measuring something the graders said they do not grade — `pass^k`, per §2.1.
(b) Measuring something that does not exist in the system we built — ECE over confidence
bins on a discrete-state checker. (c) Machinery whose *validating* input we cannot afford,
which makes it worse than the honest smaller thing: an inter-rater alpha where the second
rater is drawn from the same class of system as the checks is theatre — `PLAN.md` §10 said
so before this decision existed — and a judge panel with no human anchor to validate it
against is an unvalidated panel wearing three hats.

Consequences, stated as limits rather than buried: **recall is our weakest number and stays
weak** — one labeller, 24 sites, ±~12 pp. Test–retest buys evidence that the rubric is
applied *consistently*; it does not buy evidence the rubric is not *systematically misread*
by one person. Recall is exposed to that; precision much less so, because every match is
verified verbatim against the snapshot. Held-out at 12 sites gives ±~15 pp — it can detect
a collapse (0.90 → 0.60), not a 10 pp drift. All of these go in the report, not in a
footnote. The held-out sites are selected by a fixed rule **before** the harness exists and
are not opened until Stage F, because a hand-picked held-out set is exactly the one that
can be unconsciously easy.

## D-018 — CHK-E-023 (mobile ad density) is cut

Date: 2026-09-04

Context: The officials' Q&A (`OFFICIALS-QA.md` §1.1) named CHK-E-023 as outright
unmeasurable without a headless browser, and D-015 confirmed `rendered[]` is structurally
empty for every graded run. Checking the code rather than the docs found the consequence is
sharper than "degrades to `not_determinable`": `check_e023` iterates `bundle["rendered"]`,
so with an empty list the loop body never executes and the check emits **nothing at all** —
not a finding, not an `absent`, not even a `not_determinable` envelope. It is dead code in
the sandbox. Independently, `BUNDLE-SCHEMA.md` Caveat 1 already named it the most
false-positive-prone of the 27 even on runs where it *can* execute, which is why it carried
a bespoke two-detector agreement rule no other check needs.

Decision: CHK-E-023 is removed — from `engagement_defect_checks.py`, from
`compose_report.py`'s title map and `STAGE_CONSUMERS["render_pass"]`, from both `checks.md`
files, from `engagement-defect-audit/SKILL.md`, and from the check tables in
`ARCHITECTURE.md`, `BUNDLE-SCHEMA.md`, `report-schema.md` and `EVIDENCE-LEDGER.md`. The
marketplace ships **26 checks**, not 27.

CHK-E-016 (tap targets) and CHK-E-018 (overlay geometry) are equally render-dead and are
**kept**. The distinction is the reason for the deadness, and it is the defensible line:
they are dead because a *tool* is absent, not because the *check* is weak, and
`compute_degraded_stages` already discloses them by name through
`STAGE_CONSUMERS["render_pass"]`, so a reader of the report is told they were not measured.
Cutting them would remove honest, disclosed capability. Cutting E-023 removes a liability.

Reason: Two independent sufficient reasons — it cannot execute in the graded environment,
and it was already the weakest check when it could. Under the asymmetric-justification rule
this needs no written defence at all, since removing a check can only lower our scores; the
rule requires justification in the other direction. The project's standing rule applies
directly: 26 defensible checks beat 27 with one that fires on healthy sites.

Consequences: No behaviour change in the grading sandbox, where the check already emitted
nothing. The two-detector agreement machinery in `render_geometry.py` loses its only
consumer; it is left in place rather than removed, because it is inert without a renderer
and removing it would touch the collector for no gain. `EVIDENCE-LEDGER.md`'s row is struck
through rather than deleted, so the ledger still records that the check existed and why it
went — a deleted row reads as an oversight, a struck one reads as a decision.

## D-019 — Findings are rolled up per defect, not per page

Date: 2026-09-04

Context: Stage B was the first time this marketplace met real multi-page websites. Every
report it produced was a laundry list: 48 findings on one site, 47 on another, 44 on a
third. Inspection showed the cause was not over-detection but **repetition** — a single
site-template defect (one unnamed link in a shared header, one missing `<main>` in a shared
layout) emitted one finding per sampled page. On a 20-page sample that is 17 findings for
one fix. Every one of them was true, and the report was still wrong.

This is the rubric line the officials were most explicit about: "Not just a laundry list of
items. […] The real ingenuity lies in how you order them — what moves the needle the most"
(`OFFICIALS-QA.md` §3.1). Ordering cannot rescue a list where one defect occupies 17 of the
slots being ordered.

Decision: `compose_report.roll_up_site_wide` collapses findings that share a **defect
signature** — check_id, subcheck, and the evidence string with URLs and integers masked —
into one finding carrying `occurrences: {pages, examples[]}`. Its severity is the **worst**
in the group, never an average: a defect is as serious as its worst instance. Its locus
becomes `{"url": null, "scope": "site"}`.

The threshold is **3 pages**. Below that a defect is plausibly specific to the pages it was
found on, and collapsing would hide the locus a reader needs; the two-page case stays
itemised.

Reason: A reader cannot distinguish 17 problems from one problem seen 17 times, and the
difference is the entire prioritisation question. Masking integers as well as URLs matters:
"6 violation(s): missing alt…" and "7 violation(s): missing alt…" are the same template
defect counted on two pages, and a signature that keyed on the exact string would have left
them apart.

Consequences: Measured across the 12 negative-control sites, total findings fell from 356
to 112 — of which roughly half came from this rule and half from D-020's repairs. The
report schema gains an optional `occurrences` object; `report-schema.md`, the orchestrator
`SKILL.md`, and `ARCHITECTURE.md` §4.3 are updated. This is the orchestrator's **second**
genuine cross-cutting rule, alongside O-1 — which is directly relevant to the merge test
`EVALS.md` §7 left open, since it is a rule that operates on the combined output of all
four analysers and could not live inside any one of them. It is not, however, a *cross-skill*
rule in O-1's sense: it groups findings within a check, so it does not on its own justify
the four-analyser split. Recorded so the merge test is not later credited with evidence
this rule does not supply.

## D-020 — Four false-positive mechanisms found by the Stage B screen, repaired at source

Date: 2026-09-04

Context: The Stage B negative-control screen ran the audit against 12 sites each curated
clean on one named dimension. **Eight of the twelve fired inside their own clean
dimension.** Rather than accept or dismiss that in aggregate, each firing was traced to the
site's actual HTML. The traces split three ways, and the split is the useful part:

**(a) The check was right and the corpus was wrong.** `CHK-D-007` fired on a site this
project had listed as clean on `entity_identity` because it "has complete Organization
markup". Fetching it found **zero** `application/ld+json` blocks. The curation was an
assumption, never verified. Logged as a rejection, not a false positive — the fix is to the
corpus row.

**(b) The check enforced something its cited standard does not say.** `CHK-E-022` reported
"2 `<h1>` elements found. Violates … WCAG 2.2 SC 2.4.6". SC 2.4.6 requires headings to
*describe topic or purpose*; it says nothing about how many `h1` elements a page may have,
and HTML5 sectioning permits more than one. The check was enforcing a style preference
under a citation that does not support it.

**(c) The evidence the analyser was given could not support the guard it was asked to
apply.** Three separate cases, all in the collector:

  - `<img alt aria-hidden="true">` — a *correct* decorative marking, found on a
    WCAG-authoring site — was reported as a missing-alt violation. `html.parser` reports a
    valueless attribute's value as `None`, making `<img alt>` indistinguishable from
    `<img>`. `engagement-defect-audit/SKILL.md` had documented the right guard for years
    ("test `alt === null`, not `!alt`"); no analyser could implement it, because the
    distinction had already been destroyed upstream.
  - `contact_signals.org_name_footer` took the footer's text up to its first full stop,
    capped at 120 characters. A modern footer is a navigation menu with no full stop, so on
    most sites it returned 120 characters of link labels. `CHK-D-027` then reported those
    as competing organisation names — including, on one site, its own article headlines.
  - `CHK-D-027` additionally read `name` off **every** JSON-LD entity, not only
    Organization ones, collecting page titles and breadcrumb labels from a real site's
    graph. `_organization_blocks` — the exact filter `CHK-D-007` already used — was sitting
    unused in the same file.

Decision:

  1. **Collector:** `_alt_value` distinguishes an absent `alt` from a valueless one;
     `decorative_hint` (`aria-hidden="true"`, `role=presentation|none`) is added to
     `pages[].images[]`; hidden and aria-hidden elements are excluded from the
     accessible-name scan, and an inline `<svg><title>` counts as naming its control;
     `_footer_org_name` reads the copyright line only, and returns `None` when there is
     none.
  2. **`CHK-E-014`:** skips images marked `decorative_hint`.
  3. **`CHK-E-022`:** the multiple-`h1` branch is removed. Zero `h1` remains a finding, now
     cited to SC 1.3.1 (Info and Relationships), which does support it.
  4. **`CHK-D-027`:** compares names from Organization entities only.
  5. **Corpus:** the mis-curated negative-control row is corrected and logged in
     `docs/evals/corpus-selection.md`.

Reason: Every one of these is score-lowering and therefore needs no defence under the
asymmetric-justification rule; they are recorded at length because *where* the bug lived is
the transferable lesson. Three of the four were in the **collector**, not in any analyser —
a documented false-positive guard is worth nothing if the evidence reaching the analyser
has already lost the distinction the guard depends on. That is an argument for D-013's
collector boundary and simultaneously the sharpest risk it carries.

Consequences: Total findings across the 12 clean sites fell from 356 to 112, and
`CHK-D-027` went from firing on 6 of 12 clean sites to 0. `docs/BUNDLE-SCHEMA.md` and the
collector's `references/bundle-schema.md` gain `decorative_hint`.

**Deliberately not fixed:** `_footer_org_name` still returns imperfect strings on some
sites (a bare year range, a partial phrase). It no longer produces findings, because
`CHK-D-027` falls to `not_determinable` when it has fewer than two comparable names. Tuning
it further against the same 12 sites would be fitting the extractor to the screen — the
failure D-010's asymmetric-justification rule exists to prevent. Recorded as a known
limitation instead, to be re-measured on the dev corpus.

## D-021 — Archetype classifier: fixed a schema-mismatch bug that made every JSON-LD signal dead code; accepted the resulting accuracy without further corpus-fitting

Date: 2026-09-04

Context: Stage B' measured 17% archetype accuracy (6/36) with 5 confidently-wrong labels —
the dangerous failure mode, since `unknown` is safe by design (suppresses
archetype-conditioned checks) but a wrong confident label activates suppression rules
written for a different kind of site. `docs/evals/stage-b-report.md` §4 traced the dominant
cause to `classify_page_type` returning `other` for real doc URLs and explicitly declined
to add more path patterns against the same 36 sites, calling that corpus-fitting, then
escalated the number here as "D-021" without a resolution.

Investigating the 5 confident-wrong cases (not the `unknown` majority, which costs
capability, not correctness) found a single root cause behind three of them, live only in
`harness/collect.py` — the harness's own glue code, not the shipped skill:
`page.get("structured_data", {}).get("types", [])` and `sd.get("sameAs")` read keys that
`extract_page._extract_structured_data` has never produced. The real shape is
`{"json_ld": [{"type", "raw", "fields_present"}], ...}`. Both reads silently returned `[]`
on every page, on every site, for the entire Stage B/B' run — killing three signals at
once: JSON-LD-driven `page_type` labelling (Product/Offer/Article/FAQPage), the archetype
`is_local_business` rule, and CHK-D-025/026's declared `sameAs` discovery.

A fourth, independent cause: `has_price` was a regex over raw HTML for `"price"` /
`"priceCurrency"` anywhere in the page source, which matches ad-tech/analytics JSON
carrying the same key names, not just commerce markup — exactly the "editorial site selling
one book" false positive the archetype rule's comment already named as a risk. It fired
anyway, at 0.6 confidence, on two news/editorial sites with zero real commerce signal
(smashingmagazine.com, heise.de). A fifth: `product_count >= 5` (path-pattern based, 0.9
confidence, checked first) had no price corroboration requirement at all, so a
non-commerce catalogue using `/product/` in its URLs (heise.de's *free* software-download
directory, `/download/product/<name>`) was sufficient on its own.

A sixth, unrelated to JSON-LD: the `pricing` page-type rule matched the bare word "plans"
anywhere in path or title — an ordinary English word (rights-of-way improvement plans,
floor plans) — false-positiving a UK government guidance page.

A seventh, general and unrelated to archetype accuracy directly but sharing the same root
class: `classify_page_type`'s documentation rule matches `/api/` as a path segment, which a
media/CMS API namespace also satisfies. `blog.cloudflare.com`'s sitemap listed 95 image URLs
under `/_emdash/api/media/file/*.png`, all mislabelled `documentation`, which alone flipped
the site's whole archetype from `news_editorial` to `documentation` — the fifth confident-wrong
case.

Decision:

  1. `harness/collect.py` gains `_entity_type_names`/`_json_ld_types`/`_json_ld_entities`,
     reading the real `json_ld` shape (and normalising `@type` string-or-array, mirroring
     `entity_identity_checks._org_type_names`). Used to fix the `page_type` re-labelling
     call, `_archetype_view`, and `_check_anchors`'s `sameAs` extraction.
  2. `_archetype_view`'s `has_price` now checks `fields_present`/nested `offers.price` on
     Product/Offer JSON-LD entities only, not a raw-HTML-wide regex.
  3. `page_classifier.classify_archetype`: `product_count >= 5` now requires `has_offer_price`
     too before returning `ecommerce` at 0.9 confidence.
  4. `page_classifier.py` gains an `asset` page_type (non-HTML extensions, checked before
     every other rule), excluded from sampling (`sampling.py`), from the 200-URL inventory
     cap (`harness/collect.py`'s `_discover`), and from every `archetype` proportion
     denominator — a sitemap that mixes in media URLs must not be able to flip a site's
     labelled type.
  5. `pricing` rule: "plans" is now anchored to a path segment (`/plans(/|$)`), matching the
     fix already applied to `documentation`; "pricing" stays unanchored as unambiguous.
  6. `procedure.md` updated to document `asset` and the anchoring rule, so the invoking
     agent's own discovery (not just this harness) follows the same contract.

Reason: every fix above is general — none references a site by name in its condition, only
in its discovery. Precision, not recall, is the axis the classifier already treats as safe
to trade (`unknown` suppresses rather than misleads), so combining `product_count` with a
price signal is consistent with that stance even though it will miss some real ecommerce
sites whose sampled pages happen not to include a priced one.

Consequences: measured on the 34 dev+negative sites that still replay offline after the
`asset` change altered which pages get sampled (2 sites — creativecommons.org,
blog.cloudflare.com — now need one live re-fetch to rebuild their snapshot; not done in this
pass, see the standing "local directory only" scope note below), confident-wrong labels fell
from **5 to 1** (only www.tartinebakery.com remains, which genuinely carries no JSON-LD at
all — not a bug this pass found a mechanism for). Raw accuracy is roughly flat, 21% vs. 17%,
because most flips landed on the safe `unknown` answer rather than the correct one — which
is the intended trade, not a shortfall. `blog.cloudflare.com`'s fix was verified directly
against its existing bundle (re-classifying its stored inventory: the 95 `documentation`
entries become `asset`, archetype flips from `documentation`/0.9 to `unknown`/0.0) rather
than through a full offline replay, since that site is one of the two needing a fresh fetch.

**Deliberately not done:** no further `classify_page_type` path-pattern additions (the
`/templates/`, `/getting-started/`, `/content-management/` gap `stage-b-report.md` already
identified and declined to fix). That gap is the dominant remaining cause of `unknown`, is
safe by construction, and fixing it against these exact 36 sites would be corpus-fitting.
The number this decision accepts is **21% raw accuracy, 1 confident-wrong site of 34**, not
a higher figure — and no future pass should raise it by tuning against this same corpus
without the justification the asymmetric rule requires.

## D-022 — Stage C: five checks flagged by the Stage B negative-control screen, resolved

Date: 2026-09-04

Context: `docs/evals/stage-b-report.md` §3 flagged five checks with residual false-positive
exposure after D-020's fixes, ranked by how many of the 12 curated-clean sites they still
fired on, and left them explicitly unresolved pending this pass. Re-measured across the
full 34-site dev+negative corpus (not just the 12-site screen) before deciding each:
`CHK-E-022` 29/34, `CHK-E-014` 27/34, `CHK-D-007` 26/34, `CHK-E-021` 26/34, `CHK-D-004`
18/34, `CHK-D-010` 17/34. Each was traced to its actual HTML/regex behaviour, not judged
from the count alone — the count decides which checks are worth tracing, not the verdict.

  - **`CHK-E-014` (WCAG machine-detectable failures) — accepted as-is.** Matches
    `PLAN.md`'s own cited base rate (95.9% prevalence across the open web) almost exactly.
    Near-universal firing is the literature's prediction, not a bug; `stage-b-report.md`'s
    Group (b) already reached this conclusion by hand-verifying two exemplar sites.
  - **`CHK-E-022` (no h1 / missing main / heading skip) — accepted as-is, verified by hand.**
    Traced `gohugo.io`'s "5 pages, no h1" firing to the actual frozen HTML for
    `/documentation/`: genuinely no `<h1` in the raw response. Not a detection bug; the
    check reads `headings[]` correctly (confirmed the homepage, which does have an h1, does
    *not* fire). Same conclusion as `CHK-E-014`: near-universal because the underlying WCAG
    failure is near-universal.
  - **`CHK-D-007` (no Organization JSON-LD) — severity capped `medium` → `low`.** Stays a
    finding (real, correctly targeted, still actionable) but D-009's "findings conditioned
    on base rates" rule is now enforced in code: WDC Oct 2024 measured only 44.1% of
    domains carrying *any* structured data, so absence is the open web's majority
    condition, not a differentiated signal.
  - **`CHK-D-004` (thin content, <200 words) — excludes `home` page type.** A homepage's
    job is navigation and framing, not comprehensive information; the check was applying a
    content-page bar to hero-plus-links pages by design. Found flagging gohugo.io's
    197-word homepage. `home` joins `contact`/`login` in `NON_INFORMATIONAL_PAGE_TYPES`,
    shared with `CHK-D-010`. The now-unreachable `d003_fired`-gated homepage suppression
    inside `check_d004` is a strict subset of this and was removed (D-016 already proved
    its outcome — the "four findings for one defect" case — stays unreachable either way).
  - **`CHK-E-021` (images/iframes without dimensions) — demoted to `recommendations[]`.**
    26/34, `THEORETICAL` evidence strength, and `PLAN.md` §5 already states CLS has no
    perception research behind it. Signal stays true and actionable; it moves out of
    `findings[]` because a signal this common cannot function as a differentiated defect
    claim. Severity floor changed from `medium`/`low` to `low` only, since state is now
    always `recommendation_only`.
  - **`CHK-D-010` (no definition/numeric-fact/comparison) — demoted to
    `recommendations[]`.** 17/34, including `developer.mozilla.org` and
    `docs.djangoproject.com` — elite technical documentation that legitimately lacks the
    three literal regex shapes (`_DEFINITION_RE`/`_NUMBER_UNIT_RE`/`_COMPARISON_RE`)
    without being defective. The GEO evidence-density mechanism is real; this narrow proxy
    for it is not precise enough to assert as a confirmed defect. Same demotion class D-012
    already applied to `CHK-E-024`.

Reason: every change here is score-lowering (a cut, a demotion, or a severity cap), so none
requires defence under the asymmetric-justification rule; recorded at this length because
the reasoning for *not* changing `CHK-E-014`/`CHK-E-022` is exactly as load-bearing as the
reasoning for changing the other four — both rest on the same base-rate evidence, applied
in opposite directions.

Consequences: total findings across the 12 negative-control sites that still replay
offline (10/12, see D-021) fell from 107–112 (D-019/D-020's number) to **88**. Hard-defect
site count (a check firing inside its own curated-clean dimension) fell from 7/12 to 5/10
of the sites that still replay. `render_extractability_checks.py`'s and
`engagement_defect_checks.py`'s local `_envelope` helpers both gained a
`recommendation_only` parameter (engagement's already had it, for CHK-E-024;
render-extractability's did not and now does, for CHK-D-010).

**Scope note — "local directory only":** every fix and re-run in D-021/D-022 used only
`harness/snapshots/` (already-fetched, frozen fixtures) and existing `harness/out/`
results; no live site was contacted. Two sites (`creativecommons.org`,
`blog.cloudflare.com`) now select a different, unfetched page under the corrected sampler
and need one live re-fetch to rebuild their snapshot before they can replay offline again
— flagged, not done, since it would require leaving local-only scope.

## D-023 — A page whose fetch failed outright was scored as a page that genuinely had no content, false-positiving 6 checks at once

Date: 2026-09-04

Context: Ran the 6-site adversarial set (`harness/corpus/adversarial.csv`) live for the
first time — the negative-control and dev sets had never exercised a genuine full-page
fetch failure, only successful fetches of thin/broken content. `http://www.gnu.org`'s
initial HTTP request failed outright (`site.status: "partial"`, `reason:
"target_fetch_failed"`, 0/1 pages fetched). The report nonetheless emitted six `present`
findings — `CHK-D-003` (high, "raw fetch contains 0 words"), `CHK-E-014` (high, "missing
lang attribute"), `CHK-E-022` (high, "no h1 element found"), `CHK-D-008` (medium, "no
rel=canonical found"), `CHK-D-025` (medium, "no sameAs declarations"), `CHK-E-015`
(medium, "missing viewport meta tag") — every one of them a confident description of a page
that was never actually retrieved.

`collect._unavailable_page` (the harness's placeholder for a failed fetch) already sets
`extraction_ok: False` and empty defaults for every content field
(`lang: None`, `headings: []`, `landmarks: {}`, `canonical: {}`, `structured_data: {}`,
`meta: {}`). Several checks (`CHK-D-004`, `CHK-D-006`, `CHK-D-007`, `CHK-D-010`,
`CHK-D-011`, `CHK-D-013`) already guard on `extraction_ok` correctly and would have emitted
`not_determinable` for this page. Eight did not: `CHK-D-003`, `CHK-D-008`, `CHK-D-012`,
`CHK-D-025`/`CHK-D-026` (via a `home_about` list built without the guard), `CHK-E-014`
(static sub-checks a–e), `CHK-E-015` (viewport-meta sub-check), `CHK-E-017`, `CHK-E-019`,
`CHK-E-020`, `CHK-E-022` — reading `None`/`[]`/`{}` at face value as "the attribute is
genuinely absent" rather than "we have no data for this page at all". `CHK-E-021` was
checked and found safe by construction (an empty page contributes 0 to its element count,
which is already below its noise floor). `CHK-D-027` was checked and found safe by
construction (empty structured data and footer text produce no names to compare, and the
check already requires ≥2 names before firing).

This is a different failure mode from the render-gap checks' one-sided re-derivation
(D-015): D-015 is about a page that *was* fetched but has no rendered-DOM evidence — the
static content is real and worth evaluating one-sidedly. This is about a page that was
*never fetched at all* — there is no content to evaluate, one-sidedly or otherwise.

Decision: added the same `if not page.get("extraction_ok", True): emit not_determinable;
continue` guard already used correctly elsewhere to all ten affected checks, mirroring each
check's own evidence-strength and locus conventions. `CHK-D-025`/`CHK-D-026` needed a
slightly different shape since they read a whole `home_about` list rather than one page at
a time: filtered the list to `extraction_ok` pages, and added an explicit
`not_determinable` branch for "a home/about page existed but none of its instances could be
fetched", distinct from the pre-existing (unchanged) behaviour for "no home/about page type
exists in the sample at all".

Reason: every one of these ten checks reads `bundle["pages"]` directly with no reason to
assume every entry represents a successfully-retrieved page — that assumption held
throughout Stage B/B'/C only because none of those 36 sites happened to have a full-page
fetch failure to expose it. A page that returns a timeout, a connection refusal, or a
non-2xx status on the very first request is not exotic on the open web; the fix generalizes
to any such failure on any site, not just `www.gnu.org`'s specific network condition on
2026-09-04.

Consequences: `www.gnu.org` now reports **0 findings** instead of 6 for its single
unfetchable page (`site.status` still correctly reports `partial`/`target_fetch_failed`, so
the failure itself is not hidden — only the false defect claims about the page's content
are removed). Re-running the full 36-site dev+negative corpus (all of which now succeed
offline, see the scope note above) found total findings fell from 232 (34 sites, before
this fix) to 218 (36 sites, after) — a real, if modest, reduction on sites that had no
full-site failure, meaning a handful of *individual pages* within otherwise-healthy dev/
negative-control sites were also silently affected by the same bug at smaller scale.
Schema conformance and harness stability unaffected: 0/36 failures before and after.

## D-024 — The harness's own crawl-gate ignored every `Allow` rule, refusing to crawl a site that is actually open

Date: 2026-09-04

Context: `excalidraw.com` (adversarial set, `js_only_spa` condition) returned a 0-URL
inventory on first run — not even the homepage was fetched. Its real robots.txt declares,
for the generic agent class: `Allow: /$`, `Allow: /`, `Allow: /sitemap.xml`,
`Disallow: /`. The shipped `robots_parser._root_allowed` (used for `CHK-D-001`/`002`'s
findings) already implements the correct de-facto precedence — longest-matching rule wins,
ties favour `Allow` — and correctly computed `allowed_root: True` for this exact robots.txt.
But `harness/collect.py`'s own crawl decision (`fetcher.parse_disallows` /
`fetcher.path_allowed`) is separate code, written for a different question ("may *I* fetch
this path", not "is root allowed for this named AI agent"), and it had never implemented
`Allow` at all: `parse_disallows` parsed `Allow:` lines only far enough to mark that rules
had started, discarding the value, so `path_allowed` treated the `Disallow: /` line as
absolute and refused to crawl a site the shipped skill's own logic (and any real crawler
following the standard) would treat as open.

Decision: extended `parse_disallows` to also capture `Allow` rules, and rewrote
`path_allowed` to implement the same longest-match/ties-favour-Allow precedence as
`robots_parser._root_allowed`, generalised from "does this rule match root" to "does this
rule match this path" (new `_rule_match_len` helper). Updated the four call sites in
`harness/collect.py` (`_discover`, `_bfs`, `_check_internal_links`, plus the initial
`parse_disallows` call) to thread the new `allows` list through alongside `disallows`.

Reason: this is a harness-only bug — `harness/` is git-ignored and never ships, and the
shipped `robots_parser.py` was correct throughout. But the harness exists specifically to
measure how the shipped logic behaves on real sites, and a harness that is *more*
restrictive than the shipped audit's own robots.txt reading understates what the real tool
would actually collect: every corpus site with a self-contradictory or `Allow`-recovering
robots.txt (not rare — CDNs and SEO-conscious sites commonly declare a narrow `Disallow`
alongside a broader `Allow` recovery) would have been under-sampled or entirely skipped by
this harness while the shipped tool, following the correct precedence, would have crawled
normally.

Consequences: `excalidraw.com` now collects a 1-page inventory (its homepage) instead of 0,
fetches successfully, and reports `archetype: brochure` instead of `unknown`. No other
adversarial/dev/negative-control site's robots.txt exercises this precedence conflict, so no
other site's numbers changed. `CHK-D-003`/`CHK-E-019` still do not fire on this page even
after the fix — the real homepage's raw HTML has 0 words of main text but does carry a
static `<h1>`, and both checks' definitional critical rule requires `h1 == 0` *and*
`words < 50` together, which this site does not satisfy. That is a real result, not a
residual bug: logged as a correction to `harness/corpus/adversarial.csv`'s
`expected_behaviour`, not treated as something to chase further.

## D-025 — `render-extractability-audit` and `engagement-defect-audit` merged into `content-engagement-audit`: the merge test ran, and the boundary bought nothing

Date: 2026-09-04

Context: `ARCHITECTURE.md` §7 named the merge test as the deciding evidence for whether the
six-skill decomposition was real or partly decorative, and left it explicitly open pending
a real corpus: "Whether one real rule is enough to justify four analyser skills … is worth
weighing again once Phase 4's real dev-corpus numbers exist." That corpus now exists.
`harness/ablation.py` was extended to test the sharper, non-trivial question directly: does
removing the skill that owns `CHK-D-003` (`render-extractability-audit`) change what
`CHK-E-019` (`engagement-defect-audit`) does anywhere in the 36-site dev+negative corpus?

**On all 36 real sites, no.** `CHK-D-003` and `CHK-E-019` never both reached `present` on
the same site. Rule O-1 — the orchestrator's one genuine cross-skill suppression, and the
only real connection between these two skills per D-016's earlier analysis — never
activated. This directly contradicts D-016's synthetic-scenario finding (5 hand-built
cases, O-1 fired in every one shaped like a JS-only site): the scenarios were representative
of the *mechanism*, not of how often real sites actually land in the narrow window where
both checks independently cross their own thresholds at once.

Decision: merged the two skills into `content-engagement-audit`.

1. **Code**: `render_extractability_checks.py` (415 lines, 7 checks) and
   `engagement_defect_checks.py` (492 lines, 10 checks) concatenated into
   `content_engagement_checks.py` (908 lines, 17 checks) — imports and constants merged
   (no naming collisions), the two files' slightly different `_envelope` helpers unified
   into one supporting every parameter either needed (`suppressed_by`,
   `recommendation_only`, `subcheck`), and one `evaluate()` calling all seventeen checks in
   the dependency order both skills already required (`CHK-D-004` reads `CHK-D-003`'s
   result, `CHK-D-010` reads `CHK-D-004`'s). Rule O-1 is now applied **in-skill**, last,
   inside `evaluate()` — the same pattern `CHK-D-004`'s self-suppression against
   `CHK-D-003` already used, extended to the one relationship that used to need the
   orchestrator.
2. **Orchestrator**: `compose_report.py`'s `apply_suppression` function (and the unused
   `_by_check_and_locus` helper sitting next to it, itself dead code predating this
   change) removed — there is no cross-skill suppression left for it to apply.
   `audit-orchestrator/SKILL.md` Step 3 rewritten to state explicitly that it is now empty,
   kept in the numbering so the absence is a documented decision rather than a silent gap.
3. **Manifest**: `marketplace.json` drops from six skill entries to five.
4. **Docs**: `ARCHITECTURE.md` (§1, §4.3, §5, §6, §7, §8), the root `README.md`, both
   `audit-orchestrator` reference files, `EVALS.md` §7, and `PLAN.md` all updated in the
   same pass — including two pre-existing staleness bugs found and fixed along the way,
   unrelated to the merge itself: `audit-orchestrator/SKILL.md` said "27 checks" in three
   places when the shipped `CHECK_TITLES` dict (and every other doc) has always had 26
   (`CHK-E-023` was cut by D-018); and `entity-identity-audit/references/checks.md`'s
   `CHK-D-007` entry described a `logo`/`sameAs`/`contactPoint` recommended-field severity
   tier `check_d007` has never implemented (already corrected in D-022, unrelated to this
   decision, but caught again here while auditing the same area).

Reason: `ARCHITECTURE.md` §6 committed to this in advance — "If the ablation in §7 fails to
justify a boundary, we merge it" — precisely so the decision would be made by the test
result, not by after-the-fact rationalization once the result was known. The two skills
were genuinely different in evidence type and severity semantics from
`crawl-access-audit` and `entity-identity-audit` (§6's argument still holds for those), but
not from each other in any way the corpus could detect. Keeping them split on architectural
taste alone, once the one dependency that would have justified it tested negative, is
exactly the "padding" the rubric penalises.

Consequences, verified before committing to the merge, not assumed:

- **Functional equivalence, checked mechanically.** Ran both the old two-module code and
  the new merged module against all 42 available bundles (24 dev, 12 negative-control, 6
  adversarial) and compared every `(check_id, locus_url, subcheck)` key and every `state`:
  **zero differences on all 42 sites.** The merge changed which file the code lives in, not
  what the code does.
- **Full pipeline re-run, not just the module-level comparison.** `harness/run_audit.py`
  (imports, `ANALYSERS` list) and `harness/ablation.py` updated to the new module and
  three-analyser structure; dev, negative-control, and adversarial sets all re-run end to
  end through the real harness (not the direct-import comparison above) — 0/42 failures,
  matching the pre-merge baseline exactly.
- **`harness/ablation.py`'s Test 2 is now structurally moot** and says so explicitly rather
  than silently reporting a number that stopped meaning what it used to: `CHK-D-003` and
  `CHK-E-019` are owned by the same skill now, so ablating one always removes both, and the
  script detects this (`d003_owner == e019_owner`) and reports "MOOT" with a pointer to this
  decision instead of computing a comparison that can no longer isolate anything.
- **Bundle-sufficiency (`EVALS.md` §7 test 2) re-verified, not just assumed to survive.**
  Grepped all three remaining analyser scripts for any networking import — zero matches,
  same as before the merge.
- **What this does not resolve:** whether `crawl-access-audit` and `entity-identity-audit`
  are correctly split from `content-engagement-audit` and from each other rests on §6's
  evidence-type argument, which — unlike O-1 — has no known cross-skill dependency to test
  in the first place. Recorded in `ARCHITECTURE.md` §7 as open rather than claimed settled
  by extension of this result.

## D-026 — The negative-control set's missing seventh dimension closed: `offsite_identity`, 12 → 15 sites, every row verified by fetch before it was written

Date: 2026-09-04

Context: `CHK-D-025`/`026`/`027` (declared identity anchors: absent, unresolvable,
self-inconsistent) were added under R-5, and R-5's own follow-on note said the negative
control needed a dimension for them. It was never created — not when the checks landed, and
not when D-017 redesigned the set to 2-per-dimension. The result was that the three anchor
checks were only ever screened incidentally, via the two `entity_identity` rows, neither of
which had been verified against an anchor's actual resolution. `CHK-D-026` in particular had
**no clean site anywhere in the corpus** whose declared anchors were known to resolve, so
the one check in the family with a HARD-MECHANICAL evidence strength and a `high` severity
ceiling had never been screened at all.

Decision: add `offsite_identity` as the seventh dimension with three rows — `stripe.com`,
`about.gitlab.com` and `www.docker.com` — and register it in `harness/score_screen.py`'s
`DIMENSIONS`. Three rather than two, breaking the set's uniform 2-per-dimension shape,
because the pre-screen below found qualifying candidates scarce enough that a spare is worth
more than the symmetry; every candidate that qualified was kept. It
deliberately overlaps `entity_identity` on the three anchor checks rather than moving them:
the `entity_identity` rows were curated on on-page markup *and* declared profile links, so
they stay screened on all six, and the overlap costs nothing because the map is only ever
read forwards, per site, as `DIMENSIONS[row.dimension]`.

**Selected by fetch, not by reputation — which is the part worth recording.** D-020 found
that two of the original 12 rows had been curated from an assumption, one of them on a site
with zero JSON-LD. So candidates here were pre-screened by fetching the homepage and reading
its `application/ld+json` for an `Organization`/`Corporation` block with a non-empty
`sameAs`, before anything was written down. **14 candidates probed; 3 unreachable; 8 of the
remaining 11 declared no `sameAs` at all** — including `www.theguardian.com`,
`www.redhat.com`, `www.nature.com` and `www.khanacademy.org`, which emit no JSON-LD on the
homepage whatsoever, and `www.bbc.co.uk` and `www.wired.com`, which emit an entity block
with no anchors in it. Every one of the eight is a site a reputation-based curation would
have picked. The full pre-screen is in `docs/evals/corpus-selection.md`, rejections logged
individually.

Each chosen row was then run through the full live audit (`harness/run_audit.py --site`,
no `--offline`) and its `anchors.results[]` read before the CSV row was written:

- `stripe.com` — 12 declared anchors incl. `en.wikipedia.org/wiki/Stripe,_Inc.`,
  `wikidata.org/wiki/Q7624104`, Crunchbase, GitHub. 8 checked, 7 resolve 200, 1
  (`crunchbase.com`) returns 403 → `resolved: null`, `note: bot_blocked_not_broken`. This is
  the exact case `CHK-D-026`'s FP guard exists for, and the check correctly did **not** fire
  on it — the first time that guard has been exercised against a real 403 rather than a
  synthetic one.
- `about.gitlab.com` — Wikipedia plus six official social profiles, 6 checked, 6 resolve 200.
- `www.docker.com` — GitHub plus five official social profiles in `sameAs`, plus two outbound
  profile links the collector picked up (`dockerstatus.com`, a merch store). 8 checked, 8
  resolve 200. The weakest of the three as a knowledge-base case — no Wikipedia or Wikidata
  entry declared — which is what makes it a useful spare: `CHK-D-025`'s bar is deliberately
  low (any one resolvable anchor passes), and this row is the one that tests that bar rather
  than a rich anchor set.

Result: **none of the three sites fires `CHK-D-025`, `CHK-D-026` or `CHK-D-027`.** No hard
defect, so no rejection was needed. `python harness/score_screen.py --screen negative` now
reports 15 sites, 15/15 schema-conformant, and the hard-defect list is unchanged from the
pre-D-026 baseline (the seven known entries from D-020/D-022, all in other dimensions).

Consequences:

- Negative control 12 → 15; corpus total 54 → 57; the Stage B′ archetype pass now runs on
  **45** non-held-out sites, not 42. `CORPUS.md` (§3 gains a dimension table, §6's count),
  `docs/evals/corpus-selection.md` (construction rule + 12 rejection-log rows), `PLAN.md` §6
  / §8 / §9 and `docs/PROGRESS.md` updated.
- **`CHK-D-025` fires on two sites outside their curated dimension** — `docs.python.org` and
  `www.gov.uk` — and goes to the adjudication queue, unscored, exactly as intended. It was
  in that queue before this change too; the difference is that the family now has curated
  rows to be falsified against, so a future firing there means something.
- Stage B′ archetype accuracy on the negative set moves 2/12 → 3/15 (`about.gitlab.com`
  predicted `saas_marketing` at 0.8, correct; `stripe.com` and `www.docker.com` both
  predicted `unknown` at 0.0, two misses). Recorded rather than avoided: the honest hand
  label for both is `saas_marketing`, and the classifier already abstains on 12 of the 15,
  which is the known behaviour D-021 decided not to fit further against this set.
- **`offsite_identity` is the only dimension with 3 observations per check-cell**, where the
  rest have 1–2. §3's counts-never-rates rule is what stops that asymmetry from mattering;
  it would matter immediately if anyone computed a per-dimension rate off this set.

**Deliberately not done:** the `why_clean` strings for the three new rows assert consistent
name/phone/address across pages (`CHK-D-027`), but that was verified only by the check not
firing, not by reading each page's `contact_signals` by hand. `CHK-D-027`'s known limitation
from D-020 — `_footer_org_name` returning imperfect strings and the check falling to
`not_determinable` below two comparable names — means a non-firing is weaker evidence for
that third check than for the other two. Stated here rather than papered over in the CSV.

## D-027 — R-1 hand-verification completed; CHK-D-011 and CHK-D-013 demoted to recommendation-only on a genuine evidence gap

Date: 2026-09-09

Context: R-1 (`EVIDENCE-LEDGER.md`'s gate: every check needs at least one hand-spot-checked
source, not self-certified by the authoring tool — see the R-1 finding in the ledger's own
"Review — 2026-09-02" section) had been open and blocking since Phase 2. The worksheet
(`docs/evals/r1-verification-worksheet.csv` + README, D-025) organized the work: 38 cited
sources across 26 checks, reduced by greedy set-cover to 14 sources that clear every check
at least once. A human worked that list, opening each URL and checking the ledger's claim
against the actual text — the same rule as Stage D's gold labels: a system verifying its
own sourcing is exactly the failure the control exists to catch, so this could not be
delegated to a model. The completed pass was first recorded in a forked copy of the ledger
(`dist/EVIDENCE-LEDGER.md`, `dist/r1-verification-worksheet.csv` — built from a
2026-09-04 snapshot, before D-018's `CHK-E-023` cut and D-014's `LIM-05` landed in the
canonical file) rather than in `docs/research/EVIDENCE-LEDGER.md` itself, the file the
ledger's own gate actually reads. This decision folds that work back into the canonical
ledger and worksheet, and resolves the two findings that came out of it needing a real
decision rather than a paperwork fix.

Decision:

1. **R-1 is satisfied.** All 24 non-cut checks now carry a `Verified by hand` entry in
   `docs/research/EVIDENCE-LEDGER.md` sourced from the completed worksheet;
   `docs/evals/r1-verification-worksheet.csv` replaced with the filled copy. Two citation
   swaps applied where verification found a stronger fit than the original: **CHK-D-025**
   gains P-06.02 (Web Almanac 2024) alongside its existing sources — it independently
   confirms real `sameAs`-to-Wikidata/Wikipedia adoption rates, which the family's original
   anchor citation (BLINK, P-06.05) does not address, since BLINK explicitly avoids
   external identifiers. **CHK-D-007** was already citing P-06.02; the note now records
   that its co-citation to P-01.15 does not hold up on inspection (adjacent findings about
   entity-specific hallucination rates, not Organization markup).
2. **CHK-D-001/002 has an undischarged gap, flagged not fixed.** The critical/low severity
   split between these two checks rests entirely on distinguishing retrieval-time AI
   crawlers from training-only ones. Every source checked (P-01.03, P-01.12) confirms
   crawler restrictions are real and rising but neither establishes that specific
   taxonomy. No replacement citation was found in this pass — it should cite vendor
   crawler documentation (OpenAI/Anthropic/Google) directly. Left as a recorded gap on a
   `critical`-severity check rather than silently accepted, per this project's own rule
   against grading in its own favour (the same rule R-1 exists to enforce).
3. **CHK-D-011 (pronoun-saturated key claims) and CHK-D-013 (near-duplicate templated
   content) are demoted to `recommendations[]`.** Unlike every other check in this pass,
   these are not weak-citation or imprecise-proxy cases (`CHK-D-010`'s and `CHK-E-021`'s
   class, D-022) — all cited sources were opened by hand (three for D-011: P-01.05,
   P-01.02, P-06.04; two for D-013: P-01.09, P-06.03) and **none discuss the check's actual
   claim at all**. P-01.05 is about attribution scoring, not pronoun ambiguity; P-06.04
   (FEVER) is claim verification against Wikipedia, not referent ambiguity; P-01.09 audits
   AI-generated citation sources, not templated near-duplicate content; P-06.03 (MAVE) is
   product attribute-value extraction. This is a genuine evidence gap, not a citation
   mismatch a swap could fix.

   Cut vs. demote was a real choice (`PLAN.md`'s own stated preference is "prefer cutting a
   check to shipping one we cannot defend," and the worksheet's own instructions offered
   both options). Demoted rather than cut because the underlying advice in both cases —
   name a claim's subject before a pronoun stands in for it; give each variant page unique
   substantive text — is ordinary defensible writing/content guidance that doesn't actually
   need an academic citation to be worth surfacing, the same way `CHK-D-010`'s and
   `CHK-E-024`'s demotions kept a plausible mechanism visible as a recommendation once it
   couldn't stand as a confirmed defect. The distinction from a full cut (`CHK-E-023`,
   D-018): that cut was for a structural reason (render-dependency in a sandbox with no
   headless browser at all) unrelated to whether the mechanism was real; this is a
   citation-support failure on checks that remain fully computable from static HTML.

Consequences:

- `content_engagement_checks.py`'s `check_d011`/`check_d013` now set
  `recommendation_only=True` on every envelope, mirroring `check_d010`'s existing pattern.
  `content-engagement-audit/references/checks.md` and `SKILL.md` updated to match (five
  checks now `recommendation_only`, not three).
- `docs/research/EVIDENCE-LEDGER.md`'s severity-rule cells for both checks now read "Not
  emitted as a finding," matching `CHK-E-024`'s existing framing.
- **Not changed:** check count (still 26 — a demotion, unlike D-018's cut, does not remove
  a check from the ledger or the gold-labelling worksheet), `CORPUS.md`, `marketplace.json`,
  and the in-progress `docs/evals/gold-labels-dev.csv` labelling pass (labellers still judge
  `PRESENT`/`ABSENT` of the underlying condition; only the report's `findings[]` vs.
  `recommendations[]` routing changes, which Stage E's scoring already handles per-check
  regardless of route — see `CHK-D-010`/`CHK-E-024` precedent).
- `dist/EVIDENCE-LEDGER.md` and `dist/r1-verification-worksheet.csv` remain as the
  human-authored record of the verification work itself (dated notes, per-source
  judgment); they are not regenerated by this decision and should not be treated as
  authoritative going forward — `docs/research/EVIDENCE-LEDGER.md` is.

---

## D-028 — The Stage E matching rule drops both evidence-text conditions; matching is locus-only, and the retired gates become reported diagnostics

**Date:** 2026-09-10
**Status:** Applied — `harness/score_dev.py`, `docs/EVALS.md` §1–§2

### What happened

The first real Stage E run, against a 100%-labelled `docs/evals/gold-labels-dev.csv` (624
rows, 24 sites × 26 checks), returned **precision 0.00 and recall 0.00 for all 26 checks**.
That was not a measurement of the tool. It was the matching rule rejecting every correct
detection in the corpus.

`EVALS.md` §2 required three conditions. Two of them compared evidence *text*:

- **Condition 3 — `P.evidence` appears verbatim in the frozen snapshot.** Unsatisfiable by
  construction. All 26 checks write `evidence` as constructed prose describing the defect
  (`"robots.txt line 120: Disallow: / applies to Applebot (retrieval-time AI crawler)"`),
  never as a copy-pasted excerpt. Verified by hand against `www.heise.de`: the tool's
  CHK-D-001 evidence is correct and that exact sentence appears nowhere in the site's
  robots.txt, because it *describes* the file rather than quoting it. Rejected **129/129**
  PRESENT rows.
- **Condition 2's Jaccard branch — ≥ 0.6 token Jaccard between predicted and gold
  evidence.** With condition 3 removed, this became the binding constraint and rejected
  **73/129**. Sampled failures, all of them correct detections:

  | gold evidence | predicted evidence | Jaccard |
  | --- | --- | --- |
  | `no definitional sentence present; page consists entirely of product l…` | `No sentence in the first 300 words explicitly names the organisation…` | 0.12 |
  | `"@type": "WebSite"` | `No Organization JSON-LD block found.` | 0.00 |
  | *(blank cell)* | `Site-wide: 5 sampled pages share this defect…` | 0.00 |
  | `PRESENT ` | `Site-wide: 4 sampled pages share this defect…` | 0.00 |

  The failure mode is structural: the labeller records *what they read* (often a quotation,
  sometimes nothing); the check emits *a description of what it found*. Two registers, no
  string overlap, same claim.

Two locus bugs were found and fixed in the same pass, both of which had been masked while
the evidence gates were rejecting everything anyway:

- **Unstripped gold cells.** `canonical_url("https://x/ ")` ≠ `canonical_url("https://x/")`.
  Hand-edited CSV cells carry trailing spaces; 61 rows had a locus that was correct to the
  eye and unequal to the byte.
- **Rollups were unmatchable.** D-019 collapses a defect found on 3+ pages into one finding
  with `locus: {"url": null, "scope": "site"}`. The labeller works per page and records a
  URL. String-comparing those can only fail — 60 rows. `occurrences.examples` is truncated
  to 3 while `occurrences.pages` may be 5+, so example-membership is not a usable test
  either.

### Decision

**A prediction matches a gold row iff `check_id` is equal and the locus matches**, where a
prediction with a null locus is read as a site-level claim matching any gold locus on that
site for that check. Both evidence-text conditions are removed from the gate.

This is defensible *for this suite specifically* because each check emits at most one
envelope per locus — CHK-E-014, the only check with two gradable judgments about one page,
separates them with `subcheck`. So `(check_id, locus)` already identifies the claim
uniquely. There is no case where tool and labeller both point at check X on page Y and mean
different defects.

### What this costs, stated plainly

Precision now measures *"the check fired where the labeller flagged a defect"* — **not**
*"and for the same reason."* That is a real weakening, and it runs in exactly the direction
`PLAN.md` §5 warns about: we author both the checks and the gold labels, so every weakness
in the matching rule fails silently in our favour (SWE-Bench+: 31% of "successful" patches
passed on weak tests, a 3× inflation from grader leniency alone).

The mitigation is disclosure, not restoration. `score_dev.py` still computes **both** retired
conditions for every match and prints them under every precision figure as
`match quality: verbatim-grounded m/n, evidence-agrees m/n`. On the current corpus those
rates are **near-zero across the board** — which is the honest headline: the detections are
right, and essentially none of them are corroborated by evidence-text agreement with the
labeller. The number that benefits from the loosening always appears beside the measure of
how much loosening it took.

### Consequences

- `EVALS.md` §2 now states two conditions, with the removed one quoted in place and the
  reason given, so the rule's history is legible rather than rewritten.
- `EVALS.md` §1's claim that "precision much less so [exposed], because every match is
  separately verified verbatim against the snapshot" **was false after this change and has
  been corrected**. Both precision and recall are now exposed to single-labeller
  systematic misreading.
- §1's "100% of `PRESENT` labels must have their evidence string found verbatim in the
  snapshot" is relaxed to requiring evidence the labeller actually read. The literal form
  was never met by the gold data either — gold evidence is routinely a summary (`"144
  words"`, `"canonical.href is null"`) or blank.
- Gold data was **not** rewritten to fit the matcher. 13 of the 24 sites were labelled by
  another hand; silently editing their `locus_url` or `evidence` cells to raise our own
  score is the exact failure this decision is trying not to commit.
- **Still outstanding before any cut rule is acted on:** the 8-site test–retest pass
  (`EVALS.md` §1). The scorer prints cut-rule verdicts; they are not final until
  reproducibility is measured.

---

## D-029 — Two false-positive mechanisms fixed in CHK-D-006 and CHK-E-014; three sites voided for evidence mismatch

**Date:** 2026-09-10
**Status:** Applied — `entity_identity_checks.py`, `extract_page.py`, `harness/score_dev.py`

Stage E (D-028) put clean-site false-positive rate at 0.67 for both `CHK-D-006` and
`CHK-E-014` — each firing on two-thirds of the sites a labeller had marked clean for them.
Diagnosis found four distinct causes, only two of which were the checks' fault.

### CHK-D-006 — the definition regex accepted one sentence shape

The pattern required a relative clause or a participle from a four-word list:

```
\b(is|are)\s+(a|an|the)\s+\w+.{0,80}(that|which|providing|offering)
```

Tested against the exact sentences the labeller cited as their reason for `ABSENT`, it
rejected **every one**:

| Site | Sentence | Old | New |
| --- | --- | --- | --- |
| gohugo.io | "Hugo **is one of** the most popular open-source static site generators." | ✗ | ✓ |
| vitejs.dev | "Vite is a blazing fast frontend build tool **powering** the next generation…" | ✗ | ✓ |
| lwn.net | "LWN.net is a reader-supported news site **dedicated to** producing…" | ✗ | ✓ |
| docs.python.org | "This is the official documentation for Python 3.13." | ✗ | ✓ |
| *(control)* | "Acme is a company **that** builds widgets." | ✓ | ✓ |
| *(control)* | "It is a start." | ✗ | ✗ |

`gohugo.io` failed twice over — `is one of` was never accepted as a determiner. Replaced
with `\b(?:is|are)\s+(?:a|an|the|one\s+of|among)\b[^.!?]{12,}`: keep the copula, drop the
required continuation, keep a length floor so a bare "It is a start" still fails.

### CHK-D-006 — Organization JSON-LD could not reach the suppression

The check exempts pages carrying Organization JSON-LD, but only inspected pages with
`page_type in (home, about)`. On qonto.com, `/en/about` is classified **`page_type=
"product"`**, so **13 pages** carrying a complete Organization block (name, legalName,
sameAs, foundingDate) suppressed nothing. The markup was right and the page-type label was
wrong; a misfiled page is not evidence that identity is unstated. Suppression now scans all
sampled pages. Same classifier-misfiling family as the `archetype: "unknown"` problem that
forced `CHK-E-024` to `N/A` on four clearly-commercial sites during labelling.

### CHK-E-014 — hidden-by-CSS-class read as an unnamed control

The flagged "link with no accessible name" on www.smashingmagazine.com, on all 12 sampled
pages, was:

```html
<a rel="me" href="https://mastodon.social/@smashingmag" class="hidden"></a>
```

A Mastodon/IndieWeb identity-verification anchor: empty and hidden by design, never
encountered by a user — **and the exact construct `CHK-D-025` asks sites to add.** One check
was penalising what another rewards. Two narrow fixes in the collector: empty `rel="me"`
anchors are treated as identity metadata rather than controls, and `_is_hidden` learns a
short list of conventional `display:none` class names. `sr-only` / `visually-hidden` /
`screen-reader-text` are **deliberately excluded** — those are exposed to assistive tech, so
an unnamed control carrying one must keep failing.

### Three sites voided rather than fixed

Grading compares two verdicts, which is only meaningful if both sides saw the same evidence.
Two ways that failed here:

- **`tailscale.com` and `www.thalia.de` were audited with `pages: []`.** Every check
  necessarily stayed silent, so 52 gold rows were scoring against an audit that never
  happened.
- **`vitejs.dev` ships 1 frozen snapshot against 11 audited pages.** Its `CHK-E-014` "false
  positive" was never a tool error — the labeller had no way to see the page the finding was
  about.

`score_dev.degraded_reason()` now voids all cells for such a site and prints why. Fabricating
the missing evidence is not available; scoring against evidence one side never had is worse
than scoring nothing. **The underlying corpus gap is not fixed by this decision** — those
three sites need re-collection before they contribute anything.

### Result

| Check | Precision | Recall | Clean-site FP |
| --- | --- | --- | --- |
| CHK-D-006 | 0.57 → **1.00** | 0.73 → **0.55** | 0.67 → **0.00** |
| CHK-E-014 | 0.88 → **1.00** | 0.88 → **1.00** | 0.67 → **0.00** |
| CHK-D-025 | 0.50 → **1.00** | 0.67 → 0.67 | 0.11 → **0.00** |
| CHK-D-007 | 0.94 → 0.94 | 0.79 → **0.94** | 0.50 → 0.50 |

Checks tripping a cut rule: **12 → 7**.

**`CHK-D-006`'s recall fell from 0.73 to 0.55**, exactly the trade-off the widened pattern
was predicted to carry: a looser definition test marks more pages `ABSENT`, including some a
labeller called `PRESENT`. It stays above the 0.40 cut line. This is recorded rather than
buried — the fix bought precision with recall, and both numbers moved.

`CHK-D-007`'s FP rate of 0.50 is **untouched and expected**: Web Data Commons measured 44.1%
of domains carrying any structured data, so "no JSON-LD" is the open web's majority
condition. D-022 already capped its severity at `low` for this reason. That is a base-rate
fact, not a bug, and no code change should make it go away.

---

## D-030 — CHK-D-004's page-type exclusion gets a URL fallback; its three remaining disagreements go to adjudication rather than into a code change

**Date:** 2026-09-10
**Status:** Applied — `content_engagement_checks.py`, `docs/evals/adjudication-queue.md`

`CHK-D-004` (thin main content) came out of the D-029 re-score at precision 0.69 / recall
1.00 / clean-site FP 0.44 — the last unexplained cut-rule trip, and the same shape D-006 and
E-014 had before diagnosis: perfect recall, poor precision. It finds every thin page the
labeller found, and also calls pages thin that the labeller did not.

Four false positives. **Only one was a check defect.**

### The defect: the exclusion is by page_type, so a misfiled page defeats it

`qonto.com/en/contact-form` is classified `page_type="product"`, so the
`{contact, login, home}` exclusion never applied and a contact form was reported as thin
content at 183 words. Identical to the bug D-029 fixed in `CHK-D-006`'s
Organization-JSON-LD suppression, and to the `archetype: "unknown"` misfiling that forced
`CHK-E-024` to `N/A` on four commercial sites during labelling. The classifier keeps being a
single point of failure for exclusions that are correct in every other respect.

Fixed with a narrow URL fallback (`_is_non_informational`), applied to both checks that use
the exclusion — `CHK-D-004` and `CHK-D-010`. Three pages corpus-wide match, all on one site.
Result: precision **0.69 → 0.75** (clears the cut line), FP **0.44 → 0.33**, recall
unchanged at 1.00.

### A discriminator that was tested and rejected

Every remaining false positive is an index or listing page — django module indexes, Smashing
Magazine author archives — so the obvious move was to detect index pages by link density and
exempt them. Measured before implementing:

| page | words | link-text ÷ words |
| --- | --- | --- |
| django `/el/3.1/_modules/` | 81 | 4.43 |
| smashing `/author/alan-cohen/` | 66 | 1.79 |
| adafruit `/product/1` | 135 | 1.81 |
| *(control)* smashing article | 2208 | 0.20 |
| *(control)* adafruit `/product/102` | 401 | 0.96 |

It appears to separate, and it does not: `page.links` is every link on the page including
site chrome, so the ratio rises whenever main text is short **for any reason**. It is a
restatement of thinness, not a detector of indexes — it would have suppressed
`adafruit/product/1`, a page that is genuinely thin. Rejected. Recorded because a
plausible-looking discriminator that fails on inspection is worth more in the log than in a
diff.

### The other three go to adjudication, not to code

- **django `_modules`** — the labeller's "387 words" and the extractor's "81" describe the
  same URL. The snapshot has 52 words in `<main>` and 577 in `<body>`; the page is a heading
  plus a list of module-name links. The disagreement is whether **link-label text counts as
  content**, which the check has never specified. That is a rubric gap, not a bug.
- **smashing `/author/*`** — the gold note spot-checks two long articles, neither of which is
  one of the three 66-word author-archive pages that fired.
- **adafruit `/product/1`** — 135 words against siblings at 292 and 401. Looks like a true
  positive labelled `ABSENT`.

All three are logged in `docs/evals/adjudication-queue.md` under `EVALS.md` §1's
disagreement-finder provision: **a queue for human adjudication, never a label, never an
input to an agreement statistic.** Nothing was written into `gold-labels-dev.csv`.

Continuing to loosen `CHK-D-004` until it agreed with these rows would be tuning the product
to fit questionable gold data — D-028's failure mode pointed the other way, and it would
surface as an *improved* score. The check is left where the evidence supports leaving it.

### Consequence

`CHK-D-004`'s FP rate of 0.33 **still trips the 0.15 cut rule** and is not resolved by this
decision. Whether it is a check to cut or three labels to correct depends on the adjudication
above, which is a human call, and on the test-retest that gates every cut verdict anyway. If
the ruling is that index pages are navigational rather than thin, **lwn.net's own gold rows
need revisiting for consistency** — they currently label calendar and alert index pages
`PRESENT` on the opposite reading.

---

## D-031 — robots.txt gains RFC 9309 metacharacter support; CHK-D-010 stops judging pages it cannot read; a circularity in the model-authored gold rows is exposed

**Date:** 2026-09-10
**Status:** Applied — `robots_parser.py`, `content_engagement_checks.py`,
`docs/evals/adjudication-queue.md`

### CHK-D-001 — the parser did prefix matching and nothing else

`_root_allowed` tested `"/".startswith(rule)`. RFC 9309 §2.2.2 gives path patterns two
metacharacters — `*` for any run of characters, `$` to anchor at end of path — and the
parser implemented neither. The consequence was exact:

```
"/".startswith("/$")  ->  False
```

`Allow: /$` means *permit the root URL and nothing else*. bookshop.org uses precisely that
to open its root to seven named AI-retrieval agents (OAI-SearchBot, ChatGPT-User,
PerplexityBot, Claude-SearchBot, Claude-User, YouBot, DuckAssistBot) before falling back to
`Disallow: /` for everything deeper. The rule was never collected as a candidate, so only
`Disallow: /` remained and **CHK-D-001 — severity `critical` — reported the site as blocking
retrieval crawlers at root.** The labeller had already flagged this in their gold note; it
is now fixed rather than noted.

`_rule_matches_root` now handles `$` and `*`. Unit-tested: `/$` matches root, `/search$`
does not, `/*` matches, `/*.pdf$` does not, bare `/` and `""` unchanged.

**CHK-D-001: precision 0.67 → 1.00, FP 0.05 → 0.00.** It no longer trips any cut rule.

### CHK-D-010 — English-only detectors were asserting absence about German and Greek text

All three evidence-shape detectors are English by construction: `_DEFINITION_RE` wants
"is a/an/the", `_NUMBER_UNIT_RE`'s unit list is English words, `_COMPARISON_RE` wants
"than"/"vs"/"faster". On qonto.com's `/de-at` pages — text carrying `Ab 9 €/Monat` and
`2.000+ Integrationen` — none can match regardless of how evidence-dense the writing is, and
the check reported the pages as containing no definition, numeric fact or comparison. That is
a statement about the detector, not the page.

`CHK-D-010` now returns `not_determinable` for a page that *declares* a non-English `lang`.
Deliberately one-sided: a missing `lang` is treated as English rather than guessed at.

**CHK-D-010: FP rate 0.23 → 0.08** (under the cut line). **Recall 0.75 → 0.25** — see below,
because that number means something other than a regression.

### The recall drop is a circularity in the gold data, and it is ours

Two of `CHK-D-010`'s "true positives" were `www.heise.de` and `www.sacher.com`, both German,
both labelled `PRESENT` with the note *"N page(s) lack a definition/number/comparison
sentence"*. **Those rows were authored by a model earlier the same day, by running the same
English-only regexes.** They agreed with the check because they were produced by the bug the
check has just had removed. Fixing the check turned them into false negatives.

This is `EVALS.md` §1's no-model-authored-gold-label rule failing in the concrete rather than
in the abstract, and it is worth stating plainly: for those rows the measurement was scoring
a detector against a copy of itself. Both are queued for human re-labelling, along with a
recommendation to audit every model-authored row on the four non-English sites
(`heise.de`, `asahi.com`, `sacher.com`, `thalia.de`) for the same assumption.

`CHK-D-010` remains recommendation-only (Stage C) and still trips precision (0.50) and now
recall (0.25). **No further tuning was done.** Its remaining signal is dominated by gold-data
problems on a check that never reaches `findings[]`; tuning it against those rows would be
fitting the product to labels known to be unsound.

### Knock-on: CHK-D-002 on bookshop.org

With D-001 no longer firing there, `CHK-D-002`'s suppression lifts and it evaluates for the
first time — and fires. The site's own gold notes describe training-class crawlers blocked at
root with retrieval intact, which is the exact definition of a `CHK-D-002` `PRESENT`, yet the
row says `ABSENT`. It reads as a label set while assuming D-001 would suppress this check.
Queued for adjudication; **not** changed, and not worked around in code.
`CHK-D-002` precision therefore shows 0.67 in this run against a row that is probably wrong.

### Net

| Check | Precision | Recall | Clean-site FP |
| --- | --- | --- | --- |
| CHK-D-001 | 0.67 → **1.00** | 1.00 | 0.05 → **0.00** |
| CHK-D-010 | 0.50 | 0.75 → 0.25 † | 0.23 → **0.08** |
| CHK-D-002 | 1.00 → 0.67 ‡ | 1.00 | 0.00 |

† driven by two circular gold rows, not by detection getting worse.
‡ driven by one probably-wrong gold row that this fix made visible.

Three of the six cut-rule trips that remain now point at gold data rather than at code. The
test-retest pass (`EVALS.md` §1) gates all of them regardless.

---

## D-032 — CHK-E-015 and CHK-E-021 diagnosed; neither is a check defect, and the gold CSV's one-row-per-check schema is identified as a real limitation

**Date:** 2026-09-10
**Status:** Applied — `docs/evals/adjudication-queue.md`; **no check code changed**

The last two cut-rule trips with an unexamined cause. Both were diagnosed to the same
standard as D-029/D-030/D-031, and in both cases the check turned out to be right.

### CHK-E-015 — recall 0.00, and the schema is why

Its two false negatives (`franklinbbq.com`, `www.tartinebakery.com`) are `PRESENT` on the
strength of the **overflow sub-check**: a human resized to 375 px and saw a horizontal
scrollbar. `rendered` is empty for every site in this harness run, so that branch never
executes. The viewport-meta branch did run, correctly, and found nothing.

The finding underneath: **`CHK-E-015` has two sub-checks of different measurability, and the
gold CSV has one row per check.** Viewport meta is static and measurable; 375 px overflow is
rendered and unmeasurable corpus-wide. One label cannot honestly stand for both — `PRESENT`
is true of the site and unscoreable against the tool, `UNMEASURABLE` is true of the
measurement and throws away a real observation.

The analyser envelopes already carry a `subcheck` field (`CHK-E-014` uses it to keep its
static and contrast judgments apart). The gold worksheet does not. That asymmetry is a
schema limitation, not a labelling mistake, and it is now recorded as one.

### CHK-E-021 — the check is right and the label generalises

Gold says every homepage `<img>` carries explicit dimensions. **Verified: 25 homepage
images, 0 lacking dimensions — the note is accurate.** But the check counts across all 12
sampled pages, and 31 of the 32 offending elements sit on a single wallpaper-gallery post,
with 1 more on an author page. A gallery with 31 undimensioned images is precisely the
layout-shift case the check exists for.

Same shape as this site's `CHK-D-004` row: a correct observation about one page generalised
to a site whose problem is elsewhere.

### Why nothing was changed

Four consecutive diagnoses (D-029 through D-032) covered six checks. Three had genuine
defects and were fixed. `CHK-D-004`'s remainder, `CHK-D-002`, `CHK-D-010`'s recall,
`CHK-E-015` and `CHK-E-021` did not — they are gold-data and schema questions, and all are in
`docs/evals/adjudication-queue.md` with a suggested resolution and no label written.

The discipline being held here is the one `PLAN.md` §5 names: we author both the checks and
the gold labels, so the cheap move at every one of these forks is to adjust the check until
the disagreement disappears, and it would show up as a better score every time. Six of the
remaining trips point at labels rather than code. Saying so is the finding.

---

## D-033 — Phase 6: judge-driven fixes across collector, checks, and report shape; Stage E rescore flags two archetype-caused regressions

**Date:** 2026-09-12
**Status:** Applied — commit `a95207d`; open regressions handed to archetype workstream

### Context

The 2026-09-11 external judge review returned 8 confirmed code bugs (B-1 through B-8) and
20 design problems (D-1 through D-20) in `dist/eval-reports/JUDGE-FINDINGS.md`. The team
agreed a five-tier fix plan and dropped **B-4 (WAF / blocked-site detection)** per
`OFFICIALS-QA.md` §2.2 and Action #10 — blocked sites are out of scope; the tool's job is
to state that they are unreachable, not to fingerprint the challenge page.

### Decision

Phase 6 (commit `a95207d`) landed the plan across the collector, the three analyser
skills, the orchestrator, and the report schema. By tier:

- **Tier 1 — collector correctness.** `extract_page.py` gained the `unavailable_page()`
  helper, `final_url` plumbing (redirect targets are recorded, so a check that judges a
  URL judges the URL that was actually reached), aria-labelledby recognition (E-014 no
  longer flags labelled inputs), a `hidden inputs are skipped` rule (E-014 no longer flags
  CSRF tokens), and a date-extraction pass that covers month-first formats, JSON-LD
  `datePublished`, and URL segments. `sampling.py` gained `is_page_url()`, which stops
  the sampler emitting sitemap indexes and binary assets as pages — the root cause of the
  weebly `/guides` 404 and the mdn gzipped-child-sitemap findings that were reaching the
  reports as false positives.
- **Tier 2 — analyser false positives.** `entity_identity_checks.py` demoted `CHK-D-027`
  to recommendation-only and stopped it flagging brand-family variants as identity
  drift. `content_engagement_checks.py` exempts media / app / press pages from D-004,
  D-005, D-010; exempts versioned and localised URL variants from D-013; splits the
  E-014 action per violation and the E-022 action into `<main>` and skip-link cases;
  softens D-003's SSR wording so the recommendation stops reading as a fix.
  `crawl_access_checks.py` rewrites D-001 and D-002 openings so the action states intent
  before mechanism.
- **Tier 3 — report shape.** `compose_report.py` now emits **one finding per
  `(check_id, subcheck, sanitized_evidence)`** with an `instances[]` array recording each
  origin envelope. The rollup floor drops from 3 pages to 2 (a defect on two pages is a
  site-template defect, and calling it two findings is exactly the laundry-list failure
  D-1 named). Recommendations gain a real `locus` and `severity` carried from their
  originating envelope. A `checks_passed[]` array is added so the report states **what
  the audit verified**, not only what it found broken. The preamble now always states the
  static-HTML premise (D-19) and the archetype effect (D-3) in two sentences.
- **Tier 4 — wording.** `CHK-E-015`'s title tightened from a paragraph to a phrase.
  `DECLARED_LIMITATIONS` rewritten so LIM-01 through LIM-05 read as prose sentences
  rather than tokenised jargon. D-017 dropped the "exactly one h1" / "violates" phrasing
  in favour of what the rule actually measures.
- **Tier 5 — archetype classifier.** `page_classifier.py` gained URL-pattern signals
  (`_DOCS_HOST_RE`, `_NEWS_HOST_RE`, `_SHOP_HOST_RE`, path patterns for `/blog`,
  `/articles`, `/docs`, `/shop`), lowered the doc/news thresholds from 0.40 to 0.30, and
  added a `personal` archetype gated on ≥70% single-path-segment URLs (the typical
  personal-blog `/slug/` shape). Corpus-wide effect: `archetype: "unknown"` count fell
  from **30/39 → 16/39** across the dev + negative sets.

Report schema is documented in
`brand-ai-readiness-audit/skills/audit-orchestrator/references/report-schema.md`.

### Reason — how each tier answers the rubric

- **Tier 3 (D-1 rollup)** answers `OFFICIALS-QA.md` §3.1 — "the report is not a laundry
  list." One site-template defect is one finding; per-page detail lives in `instances[]`
  where a reader who needs the origins can find them without the summary being drowned.
- **Tier 4 (D-16 wording)** answers §3.5 — "recommendations, not fixes." An action that
  says *do X* is a fix; an action that says *narrow X to what actually needs it* is a
  recommendation, and Tier 4 rewrote the openings that had drifted into the former.
- **Tier 5 (D-3 archetype)** is the §3.3 differentiator the officials named explicitly.
  The archetype label was in the report already but was not visibly changing what the
  report said, which is what the officials flagged: a preamble line now names it and
  states what it meant for this audit, and the `recommendations_scoped_to` field on the
  preamble states plainly which vertical every action below is written for.

### Consequences — Stage E rescore

Rescored the dev set against the current `harness/out/dev/*.report.json` after Phase 6.
Only the checks whose numbers moved are shown; every other rate-eligible check stayed flat.

| Check | Precision | Recall | FP rate | FP count |
| --- | --- | --- | --- | --- |
| CHK-D-006 | 1.00 → 1.00 | 0.55 → 0.36 | 0.00 → 0.00 | 0 → 0 |
| CHK-D-007 | 0.94 → 0.92 | 0.94 → 0.75 | 0.50 → 0.50 | 1 → 1 |
| CHK-E-014 | 1.00 → 1.00 | 1.00 → 0.93 | 0.00 → 0.00 | 0 → 0 |
| CHK-E-024 | 1.00 → 0.60 | 0.50 → 0.75 | 0.00 → 0.25 | 0 → 2 |

Negative-control set: 15/15 reports schema-conformant, zero harness errors, zero
zero-page collections. Nine in-dimension check/site firings across six sites; the
D-026 baseline recorded seven known firings, so the aggregate worsened by two. The
baseline does not enumerate the seven, so attribution from the documentation alone is
unsafe. Current firing counts on the control set: D-007 ×2, E-014 ×2, E-022 ×2, D-009
×1, D-004 ×1, D-008 ×1. The three off-site-identity control checks — D-025, D-026,
D-027 — remain clean.

**Two regressions, both archetype-caused, both handed to the archetype workstream:**

1. **CHK-E-024, precision 1.00 → 0.60, +2 false positives.** The Tier 5 classifier now
   labels `plausible.io` and `lwn.net` as `news_editorial`, and E-024's downstream policy
   treats `news_editorial` as commercial-enough to demand trust signals. The right seam
   for the fix is not obvious from the numbers alone — narrowing E-024's archetype gate
   is one option; tightening the `news_editorial` rule to require a stronger
   commerce-negative signal is another. Which one lands depends on what the archetype
   workstream decides is the correct classification for those two sites.
2. **Personal-archetype exemption suppressed correct firings.** CHK-D-006 lost two true
   positives to the exemption; CHK-D-007 lost three (which drops its precision to 0.92
   despite no new FP, because the surviving denominator shrank); CHK-E-014 lost one to
   the media / app / press exemption. The `≥70% single-path-segment` gate that fires the
   `personal` label is too permissive on some of these sites — the site list behind each
   regression needs to be walked through against the human labels before the exemption is
   narrowed, and that is the workstream currently in flight.

Neither regression is a Phase 6 code defect on the check side: E-024 and the identity
checks are doing what they were told to do given the archetype they were handed. The
archetype label is the input that changed. Fix belongs there.

Downstream assumptions that Phase 6 leaves in place:

- The `personal` archetype exempts D-006, D-007, and D-025. When the archetype
  workstream tightens the `personal` rule, the exemption list does not need to change
  — sites that stop being labelled `personal` will resume firing those checks on their
  own.
- `unknown` means no archetype rule matched. Every archetype-conditioned check is
  suppressed rather than guessed at; the preamble now names this in plain English.
- `checks_passed[]` lists only checks that ran to a clean `absent`. A check that
  produced only `not_determinable` or `not_applicable` envelopes is not listed there:
  it was not measured, and stating otherwise would be the same failure mode LIM-05 is
  written against.

### Deliberately not addressed

- **WAF / challenge-page detection (judge finding B-4).** `OFFICIALS-QA.md` §2.2 puts
  blocked sites out of scope, and Action #10 says to stop investment in blocked-site
  handling. What looks like blocked-site handling in Phase 6 — the content-type and
  status gate on the sampler — is not: it fixes stale sitemap URLs on unblocked sites
  (weebly's `/guides` 404, mdn's gzipped child sitemaps) that were manufacturing false
  findings, and it never reads a page's body to decide whether that page is a challenge.
- **The two Stage E regressions above** are not addressed in this decision because the
  fix belongs upstream in the archetype workstream. When that lands, a new decision
  entry (D-034 or later) should record the archetype change, the fresh Stage E numbers
  for E-024 / D-006 / D-007 / E-014, and whether the exemption list on the check side
  needs any narrowing on top of the classifier change.

---

---

## D-034 — Archetype classification rebuilt as additive evidence scoring; four archetypes added; `brochure` fallback and bot walls no longer produce labels

**Date:** 2026-09-12
**Status:** Applied — `page_classifier.py` replaced, `procedure.md` §3, both
`BUNDLE-SCHEMA` copies, `report-schema.md` updated. **Not yet validated on a blind list.**
Supersedes the Tier 5 classifier changes recorded in D-033.

### What was found

An 84-site run of the shipped audit returned `unknown` for 51 sites (61%) and `brochure`
for 28. Almost every `brochure` was wrong — ebay.com, etsy.com, booking.com, linkedin.com
— because the rule `total <= 5 -> brochure` fires whenever *discovery* found five URLs,
which is what a JS-rendered homepage or an unexpanded sitemap index looks like. The
classifier could not tell "small site" from "we barely looked", and `unknown` on the
other 51 was mostly the same starvation: every archetype rule read only the inventory's
page_type proportions, which a starved inventory does not have.

A second defect surfaced later and matters more. The rules were a first-match cascade, so
they decided by *order*: a blind hold-out of 40 team-labelled sites scored the first
rewrite at 20 correct / 12 wrong / 0 unknown — every unknown removed, but eight of the
twenty became wrong labels, and precision-when-labelling was no better than v1's (62% vs
67%). Every miss had the same shape: a blog section made shops, an institution and two
personal blogs "news" because the news rule sat first; `personal` was unreachable because
its rule sat last; weak rules (two signup links, four institutional-looking paths) had no
counter-evidence guard; one rule read the stratified fetch sample as if it were the site.

### What was done

`page_classifier.py` now scores evidence additively. Each archetype accumulates weighted
evidence from five families — identity (4–6), affordances (2–4), inventory structure (≤ 4,
article share capped at 3), sampled content (≤ 2, discounted when the inventory does not
back it), vocabulary (≤ 3, core-term gated) — explicit counter-evidence subtracts, the top
score wins only with ≥ 1.0 margin, confidence is derived from strength and margin
(0.55–0.90), and `unknown` is returned both for insufficient evidence and for a near-tie
with both sides named. Fetched pages that are bot walls (a 200 "Access Denied"/captcha)
are dropped before any evidence is read. Same-origin links on fetched pages are merged
into the inventory before proportions are computed. Four archetypes were added —
`reference`, `institutional`, `marketplace`, `personal` — the last of which the analysers
already handled (`PERSONAL_ARCHETYPES`) but no rule ever produced. The other three are in
neither the commercial nor the personal set, so no existing suppression rule changes
behaviour. page_type gained plural/platform product paths, `category` (specified but
never implemented), section-word article paths, tutorial/kb/sdk docs paths, docs hosts,
and a segment-anchored `pricing` (the unanchored one matched `/news/gpu-pricing-…`, the
same defect fixed for `plans` in Stage C, 2026-09-04). Discovery in the harness samples
sitemap-index children by name diversity so `sitemap_products` is not skipped in favour
of six locale blog files. `classify_archetype` accepts an optional `hints` dict
(robots.txt text, sitemap URLs) and is otherwise signature-compatible.

No rule names a host. Every general signal was written after a *pattern* of failures,
not a site, and the test file (`harness/test_page_classifier_v2.py`, 42 cases) encodes
the patterns with synthetic sites.

### What it cost and what it measured

Reachable sites only (403/429/captcha hosts excluded, they yield nothing for any
classifier): original 84 — `unknown` 39 → 10 of 58 (4 explicit ties); fresh 90 —
38 → 10 of 54 (4 ties); the team-labelled 40 — v1 8 correct / 4 wrong / 22 unknown,
new 25 / 6 / 3 (74% accuracy, **81% precision when labelling**, confidence buckets
67% / 85% / 83% for < 0.7 / 0.7s / ≥ 0.8). Findings and severities are unchanged by
construction — the 26 checks are the same code; what moves is the archetype-gated layer
(CHK-E-024 evaluated on 17 sites instead of 2 in the earlier run) and the
`recommendations_scoped_to` wording.

The 40 were labelled blind before the scoring rewrite, but the rewrite was designed after
reading its failures, so it is now a calibration set. The unresolved item is therefore
the one `EVALS.md` §1 would demand anyway: **a new blind list, labelled before running,
scored with `harness/holdout_eval.py`**, targets ≥ 0.8 accuracy and ≥ 0.8 per-label
precision. If the < 0.7-confidence bucket is wrong more than ~30% of the time, raise
`_decide(min_score=…)` and accept more unknowns; do not add rules for sites. Also still
open: re-score the 24-site dev corpus (gold `archetype_expected` and the 8 pre-marked
`N/A` rows depend on archetype), and the known soft boundaries — creator platforms with
their own pricing page (marketplace vs saas), reference content on an `.edu` host, and
English-only vocabulary.


### Stage E rescore against D-034 (2026-09-12, dev corpus offline)

Ran `harness/run_audit.py --set dev --offline` on the 24-site dev corpus after promoting
the D-034 classifier, then `harness/score_dev.py`. Compared to D-033's post-Phase 6
numbers on the same four checks:

| Check | Before D-034 | After D-034 | Verdict |
| --- | --- | --- | --- |
| CHK-D-006 | 1.00 / 0.36 / 0.00 | 1.00 / 0.36 / 0.00 | unchanged |
| CHK-D-007 | 0.92 / 0.75 / 0.50 | 0.93 / 0.81 / 0.50 | recall +0.06 |
| CHK-E-014 | 1.00 / 0.93 / 0.00 | 1.00 / 0.93 / 0.00 | unchanged |
| CHK-E-024 | 0.60 / 0.75 / 0.25 | 0.60 / 0.75 / 0.25 | unchanged |

D-033's two named regressions (CHK-E-024 precision 0.60, D-006/D-007 recall drops from the
`personal`-archetype exemption) **did not close.** The classifier rebuild is a net win in
the aggregate — `unknown` fell from 22/24 to 9/24 on this corpus — but the seam that
drives those four checks' regressions is not the classifier's *design*; it is where its
specific labels disagree with the gold's `archetype_expected` column.

### Archetype vs `archetype_expected` on the dev corpus

Exact-match 8/24, `brochure`~`personal` close 2/24, safe `unknown` abstain 9/24,
confidently wrong 5/24. Precision-when-labelling 10/15 = **0.67**, below D-034's
own ≥ 0.80 target. The five wrong labels drive the four checks' surviving regressions:

| Site | Gold expected | Got | Downstream effect |
| --- | --- | --- | --- |
| plausible.io | saas_marketing | news_editorial | CHK-E-024 fires (gate is COMMERCIAL_ARCHETYPES, which includes news_editorial) — FP against gold ABSENT |
| qonto.com | saas_marketing | news_editorial | same shape — CHK-E-024 fires against gold ABSENT |
| www.fastmail.com | saas_marketing | news_editorial | gold PRESENT — the finding is a true positive labelled under the wrong archetype |
| www.tartinebakery.com | local_business | brochure | CHK-E-024 gate rejects `brochure`, so a gold-PRESENT case is silently missed |
| jvns.ca | brochure | news_editorial | opposite direction: a personal-shape site is treated as commercial, dragging D-006/D-007 into scope |

Pattern behind the wrong labels: a SaaS site's pricing/features/blog structure is being
scored the same shape as a magazine's — `pricing` alone is anchored, but the article
share still wins on some sites. The tartinebakery / jvns misses are the mirror of that
(one type of site is looking too editorial to the classifier, the other too personal).
None of the five involves a hostname the classifier is allowed to look at (§D-034 rule:
"no rule names a host"), so the fix belongs in general signal weights, not in a lookup.

### Discriminator that was tested and rejected

Narrowing CHK-E-024's own gate to `{ecommerce, saas_marketing, local_business}` — with a
new constant `E024_ARCHETYPES` — was tried:

| Check | With E024_ARCHETYPES narrowed | Delta |
| --- | --- | --- |
| CHK-E-024 | 0.50 / 0.50 / 0.25 | precision −0.10, recall −0.25 |

Reverted immediately. The reason it hurt is exactly what the D-033 diagnosis missed:
sites like `www.asahi.com` and `www.heise.de` are correctly `news_editorial` in the gold
**and** genuinely need CHK-E-024 to fire (gold PRESENT), so silencing E-024 on
news_editorial killed true positives while only three of the four FPs it removed were
actual FPs. The seam is in the classifier, not in E-024's downstream policy.

### Consequence — what changes next

The archetype workstream should treat the five wrong labels in the table above as the
smallest concrete driver set: any general signal change that flips those five without
touching the sixteen sites already correct or safe-`unknown` is a win. Once that lands,
rerun this same score and expect CHK-E-024 to recover (both new-FP sites disappear from
the commercial gate and one currently-missed TP starts firing) without any downstream
policy change.

The two `personal`-archetype exemption regressions (CHK-D-006 recall 0.36, CHK-D-007
recall 0.81) are the same shape from the opposite end: whether the exemption is right
depends on whether the human labellers agree with the classifier's `personal` calls on
`danluu.com` and `sive.rs`. Their gold `archetype_expected` is `brochure`, and the
labeller marked those D-006/D-007 rows `PRESENT` — so the labeller does NOT think a
personal-blog shape exempts the identity checks. Either the classifier should not label
those sites `personal`, or the analyser's `PERSONAL_ARCHETYPES` exemption should not
cover D-006/D-007. Recording as the second driver set.

Nothing about the report shape (D-033 Tier 3) or the wording changes (D-033 Tier 4) is
implicated by these numbers.

---

