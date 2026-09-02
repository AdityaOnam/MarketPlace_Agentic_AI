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
