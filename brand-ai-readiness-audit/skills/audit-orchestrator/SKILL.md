---
name: audit-orchestrator
description: The entrypoint skill for the brand-ai-readiness-audit marketplace. Given a URL or domain, invokes site-evidence-collector once to gather the evidence bundle, then invokes all three analyser skills (crawl-access-audit, content-engagement-audit, entity-identity-audit) against the resulting bundle, and performs report assembly and budget arbitration to produce a single structured audit report. This is the only skill in the marketplace the user invokes directly.
license: Apache-2.0
allowed-tools: []
---

# Audit Orchestrator

The entrypoint for the `brand-ai-readiness-audit` marketplace. Receives a URL or domain,
runs the full audit pipeline, and emits a single audit report.

**This skill declares no tools and makes no network requests.** All network access
happens inside `site-evidence-collector`. All three analysers are pure functions from the
evidence bundle to findings; the orchestrator is a pure function from those findings to a
report.

## When to use

This is the skill the user invokes. Any agent, given a website URL or domain to audit,
should invoke this skill (as listed in `marketplace.json` with `"entrypoint": true`).
Never invoke the three analyser skills or the collector directly for a live audit — this
skill does that.

## Inputs

| Input | Required | Default |
| --- | --- | --- |
| `target` | yes | — a URL or bare domain (e.g. `example.com`) |
| `budget_s` | no | `300` — passed to the collector; hard ceiling for collection |

## Output

One audit report JSON conforming to the schema in `references/report-schema.md`. Top-level
structure (see schema for full field definitions):

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 0
  },
  "findings": [ ... ],
  "recommendations": [ ... ],
  "limitations": [ ... ]
}
```

- `findings[]` — detected defects only, ordered by severity (critical first) then check
  ID. Each entry satisfies the required schema from `round3-spec/SKILL.md §2`.
- `recommendations[]` — proactive improvements and single-source-demoted checks
  (e.g., CHK-E-024). Not counted in `summary.total_findings`.
- `limitations[]` — the five declared limitations (LIM-01…LIM-05, D-014 added LIM-05 for
  llms.txt) plus any `not_determinable` results caused by budget abandonment. Tells the
  reader what was and was not measured — never omitted silently.

## Procedure

Given the same input and the same site state, this pipeline is built to produce the same
report with the same ordering. **That is a design goal in service of reproducibility — so
two runs can be compared, and so the evaluation harness can hold results still long enough
to measure them — not a requirement imposed on the audit.** A live website is not a fixed
object; content changes, origins vary their responses, and a stage can be abandoned on one
run and complete on the next. Where run-to-run variation is possible the report says so
(`degraded_stages`, `not_determinable`) rather than presenting a partial run as a stable
one.

### Step 1 — Collect evidence

Invoke `site-evidence-collector` with `target` and `budget_s`. Receive the evidence bundle.

Inspect `bundle.budget.stages` immediately after collection. Record which stages were
abandoned (`abandoned: true`). A stage abandonment means all analyser checks that depend
on that stage's evidence will emit `not_determinable` — surface this in `limitations[]`
as "budget-constrained: {stage_name} was not completed; {N} checks could not be
evaluated."

### Step 2 — Run the three analysers

Invoke in parallel (they are independent; none reads another's output):

1. `crawl-access-audit` — pass the full bundle; receive findings for CHK-D-001, D-002.
2. `content-engagement-audit` — pass the full bundle; receive findings for CHK-D-003,
   D-004, D-005, D-009, D-010, D-011, D-013, CHK-E-014 through E-022, E-024.
3. `entity-identity-audit` — pass the full bundle; receive findings for CHK-D-006,
   D-007, D-008, D-012, D-025, D-026, D-027, and the vertical-schema family CHK-D-029
   (ecommerce Product/Offer), CHK-D-030 (SaaS SoftwareApplication/pricing), CHK-D-031
   (local business Postal/OpeningHours), CHK-D-032 (news NewsArticle provenance),
   CHK-D-033 (reference dataset/code archive), CHK-D-034 (documentation TechArticle).

All 32 check envelopes are received. No analyser has seen another's output. The
`compose_report.CHECK_TITLES` dictionary is the authoritative list; if the counts here
and there disagree, the dictionary wins.

### Step 3 — Cross-skill suppression: none remains (D-025)

Before 2026-09-04 this step applied rule O-1 — CHK-E-019 deferred to CHK-D-003 — because
those two checks lived in different, mutually-blind analysers
(`render-extractability-audit`, `engagement-defect-audit`). The leave-one-skill-out
ablation (`harness/ablation.py`) found O-1 never actually changed CHK-E-019's outcome on
any of 36 real sites, which was the evidence behind merging those two skills into
`content-engagement-audit` (**D-025**). Now that one `evaluate()` call computes both
checks, O-1 is applied **in-skill**, last, inside `content_engagement_checks.evaluate()` —
see that skill's `SKILL.md` step 10 — the same way `CHK-D-004` already self-suppressed
against `CHK-D-003`, and `CHK-D-010` against `CHK-D-004`, before the merge ever happened.

**There is no longer a cross-skill suppression rule for the orchestrator to apply.** The
three remaining analysers (`crawl-access-audit`, `content-engagement-audit`,
`entity-identity-audit`) are disjoint in the checks they own and do not need any
reconciliation once their envelopes arrive here. This step is kept in the numbering,
empty, so its absence is a documented decision rather than a silent gap — the next
finding that turns out to need cross-analyser reconciliation is exactly the case that
would populate it again.

### Step 4 — No root-cause cluster-dedup (D-016)

An earlier version of this skill collapsed CHK-D-003, CHK-D-004, CHK-D-005, and CHK-E-019
into one finding when all four fired together on a JS-only homepage, on the theory that a
JS-only site legitimately trips all four and reporting four findings for one defect is a
false-positive-shaped failure. **Running the suppression-necessity test from
`ARCHITECTURE.md` §7 found that pattern can never occur:** CHK-D-003 and CHK-E-019 both
require the homepage's raw `main_text_words < 50` to fire, while CHK-D-005 requires
`main_text_words > 500` on that same page before it evaluates at all — two thresholds that
cannot both hold for one page's own word count. The four-way collapse was therefore dead
code, provably so from the check definitions rather than something that needed a corpus
to discover, and was removed (`dedup_js_only_cluster` no longer exists in
`scripts/compose_report.py`).

**What is not lost:** CHK-D-004 (thin content) already self-suppresses on the homepage
whenever CHK-D-003 fires (`content_engagement_checks.py`'s `check_d004`, using
`d003_result`), so the "four findings for one defect" failure this step was written to
prevent was already being prevented one layer down, independent of anything the
orchestrator does. The one real cross-analyser relationship this section originally
described — CHK-E-019 deferring to CHK-D-003 — is no longer the orchestrator's concern at
all: since D-025 merged the two checks' owning skills, that suppression is now applied
in-skill (see Step 3). Full writeup: **D-016** and **D-025** in `docs/DECISIONS.md`.

### Step 5 — Separate findings from recommendations

After suppression:

- **Findings:** all envelopes with `state == "present"` that are not suppressed and not
  routed to recommendations.
- **Recommendations (proactive):**
  - CHK-E-024 (trust signals): routes here because `envelope.route == "recommendations"`
  - Any finding with `state == "absent"` that the analyser flagged as worth noting
    proactively (e.g., a check that passed marginally).
  - Any beyond-defect improvement the orchestrator identifies (e.g., if structured data
    exists but lacks recommended fields, a proactive note on enhancement).
- **Suppressed findings:** drop from `findings[]` (already handled); do not surface
  in recommendations either.
- **Limitations:** collect all `not_determinable` envelopes. Group by reason. One
  `limitations[]` entry per distinct reason (e.g., one entry for "render stage
  abandoned" covering all affected checks, not one per check).

### Step 5b — Roll up site-wide defects (D-019)

Before ordering anything, collapse findings that describe **one defect repeated across
pages**. Group by check ID, subcheck, and the evidence string with URLs and integers
masked; where a group covers **2 or more** sampled pages, emit one finding with
`occurrences: {pages, examples[]}`, `locus.scope = "site"`, and the group's **worst**
severity. The first affected page's URL is preserved on the rolled-up finding so the
reader still has a click-through (Phase 9 item A). Per-page findings a rollup already
covers are dropped from the itemised list (Phase 9 item U).

This exists because a site template is shared: one unnamed link in a header, or one missing
`<main>` in a layout, otherwise produces one finding per page — seventeen findings for one
fix on a twenty-page sample. Every one of them is true, and the report is still wrong,
because a reader cannot tell seventeen problems from one problem seen seventeen times.
Ordering cannot fix a list in which one defect holds seventeen of the slots.

### Step 6 — Assemble the report

1. Sort `findings[]` by severity (`critical > high > medium > low`), then by check ID
   (ascending lexicographic) within each severity tier. This makes runs comparable.
2. Count `total_findings`, `critical`, `high`, `medium`, `low` from `findings[]` only.
   Recommendations and limitations are not counted in `summary`.
3. Record the site's vertical in `preamble.archetype` / `preamble.recommendations_scoped_to`
   — see "Recommendations are vertical-specific" below.
4. Assemble the full report conforming to `references/report-schema.md`.

### Step 7 — Meta-evaluate the report before emitting it

A light self-check over the assembled report. It does **not** re-judge any finding — the
analysers own that, and this step has no authority to overturn them. It checks that the
report is internally coherent and that nothing prohibited reached the wording:

| Check | What it catches |
| --- | --- |
| `summary_reconciles` | `summary.total_findings` disagreeing with `len(findings)` |
| `severity_counts_reconcile` | severity buckets not summing to the finding count |
| `finding_complete` | a finding missing `id`, `title`, `severity`, `evidence` or `suggested_action` |
| `no_duplicate_findings` | the same check reported twice for one locus — for CHK-E-019/CHK-D-003 specifically, meaning `content-engagement-audit`'s in-skill O-1 suppression failed to fire |
| `known_check_id` | a `check_id` outside the 32 reaching the report |
| `prohibited_recommendation` | any D-007 banned recommendation or statistic in an action string (llms.txt as a fix, citation-outcome promises, above-the-fold rules, reading-grade targets, Lighthouse-100, the 3-second bounce myth, the 9.2mm tap-target figure, …). Phase 9 item C hardened this into a hard-drop gate: an offending recommendation is removed from `recommendations[]` and the meta_evaluation warning `gate_dropped_action` records what was cut, so the drop stays auditable. |
| `contradicted_by_strength` | (hard-drop, Phase 9 item P) a recommendation whose check_id is already covered by an active strength detector — dropped from `recommendations[]`, recorded as a warning. |
| `empty_recommendation` | (hard-drop, Phase 9 item B) a recommendation whose top-level and nested summary strings are both empty — dropped from `recommendations[]`, recorded as a warning. |
| `checks_passed_reconcile` | (hard-drop, Phase 10 item W) a check that appears in both `checks_passed[]` and `findings[]`/`recommendations[]` — the pass entry is dropped so the same check_id never contradicts itself. |
| `limitations_present` | LIM-01…05 not all present |

Results go in a `meta_evaluation` block on the report (`checks_run`, `passed`, `warnings`).

**Hard-drop gates (Phase 9–10)** — a small, enumerated set of gates removes an offending
recommendation or pass entry from the final report and records the removal as a warning.
Everything else is reported as a warning, never silently corrected. Quietly rewriting a
report so its own self-check passes is precisely the grading-in-our-own-favour failure
D-010 exists to prevent; the hard-drop gates are the only exception, and each one keeps
an audit trail in `meta_evaluation.warnings`.

Full report schema (field definitions, required vs. optional, and example):
[`references/report-schema.md`](references/report-schema.md).

## Recommendations are vertical-specific

**Every suggested action this report emits is scoped to the site's vertical, and the
report says which one it assumed** (`preamble.archetype`). This is not cosmetic: the
archetype decides which checks run at all — a personal or portfolio site is exempt from
the identity-anchor and Organization-markup checks, a non-commercial site from trust
signals, a documentation site from the product/offer expectations an ecommerce site is
held to — and it decides how each surviving action is worded. "Add a canonical tag" means
something different on a 10,000-SKU catalogue with faceted URLs than on a six-page
brochure site, and the action text reflects that.

When the archetype cannot be established, it is recorded as `unknown` and every
archetype-conditioned check is suppressed rather than evaluated against a guess. Guessing
a vertical activates suppression rules written for a different kind of site, which is a
worse failure than declining to judge.

## What makes these recommendations more than issue → fix lookup

A baseline checklist maps a detected issue to its textbook remedy. This marketplace does
three things that lookup cannot: it **caps each action's urgency at the strength of the
evidence behind it** (a WCAG violation is stated as a standards violation, never as a
conversion claim); it **conditions wording on the site's vertical and page type** rather
than emitting one-size-fits-all advice; and it **refuses the fashionable advice a
checklist would confidently emit** — llms.txt as a substantive fix, citation guarantees,
above-the-fold rules — with that refusal enforced mechanically in Step 7, not merely
promised, and stated visibly rather than left unaddressed (D-014).

## What the orchestrator is, and what it is not

The orchestrator's history here is a record of claims that were tested and, twice,
partly retracted — which is the honest way to run a suppression-necessity test, not a
failure of the architecture. It originally claimed three things no individual analyser
could do: cross-skill suppression, report assembly under D-012, and budget arbitration.

The suppression-necessity test (`ARCHITECTURE.md` §7) removed two of the three claims in
sequence, as real evidence accumulated:

1. **Root-cause deduplication** (a fourth original claim) was found provably unreachable
   from the check definitions alone, before any real corpus existed, and removed as
   **D-016**.
2. **Cross-skill suppression** — rule O-1 — survived D-016's synthetic-scenario test (5
   hand-built cases, all fired correctly) but did not survive contact with the real
   36-site dev+negative corpus: `harness/ablation.py` found CHK-D-003 and CHK-E-019 never
   both fired `present` on the same real site, so the rule never actually activated in
   practice. That result was the evidence for **D-025**, which merged the two checks'
   owning skills — O-1 is now applied in-skill (see Step 3), and there is no cross-skill
   suppression left for the orchestrator to own at all.

**What is left, and is real:** report assembly (severity ordering, the site-wide rollup of
D-019, meta-evaluation) and budget arbitration. Both are structurally necessary regardless
of how many analysers exist upstream — some layer has to sort, dedupe-by-page, and
translate `budget.stages` into `limitations[]`, and that layer is this one. Recorded
honestly rather than inflated, exactly as this section has done at each retraction.

## Budget arbitration

After Step 1, before emitting the report:

- Read `bundle.budget.stages` for any stage with `abandoned: true`.
- For each abandoned stage, identify which checks depend on it (see the runtime budget
  table in `docs/research/EVIDENCE-LEDGER.md` and the shared-render-pass consumer list).
- Verify those checks emitted `not_determinable` (they should; if they did not, override
  to `not_determinable` with reason "stage abandoned; analyser should have reported
  not_determinable").
- Add one `limitations[]` entry per abandoned stage: "Stage '{name}' was abandoned
  after {actual_s}s (budget: {budget_s}s). The following checks could not be evaluated:
  {check_list}. Results for these checks read as 'could not measure', not as 'no defect
  found'."

This makes `not_determinable` results readable as "couldn't measure," not as bugs or
as passing verdicts.

## Executable checks

`scripts/compose_report.py` implements steps 3–6 — `compose_report(site, audited_at,
all_envelopes, bundle) -> report`. The check-ID-to-title map and `F-NNN`/`R-NNN` ID
assignment are both deterministic functions of the sorted finding set, verified by
running the same input twice and diffing the output.

## Checks at a glance — all 32 checks and their owners

| Analyser | Checks | Evidence |
| --- | --- | --- |
| `crawl-access-audit` | CHK-D-001, D-002 | `robots` |
| `content-engagement-audit` | CHK-D-003, D-004, D-005, D-009, D-010, D-011, D-013, CHK-E-014 – E-022, E-024 | `pages`, `links` |
| `entity-identity-audit` | CHK-D-006, D-007, D-008, D-012, D-025, D-026, D-027, and the vertical-schema family D-029 – D-034 | `pages`, `anchors` |

32 checks, disjoint. No check appears in two skills — three analyser skills, one
entrypoint, one collector: five skills total in the marketplace. `compose_report.py`'s
`CHECK_TITLES` dictionary is authoritative for the set; this table restates it for
readers. (The `rendered[]` evidence category from earlier drafts is not populated in
the grading sandbox per OFFICIALS-QA §1.1; every check either derives its evidence
from static HTML or emits `not_determinable`.)

## False-positive discipline

With Step 3 empty (D-025) and Step 4's cluster-dedup rule gone (D-016), the orchestrator's
own false-positive surface is now limited to Step 5b's site-wide rollup (grouping findings
that are not actually the same defect) and Step 7's meta-evaluation itself producing a
false warning. The O-1 suppression risk described in earlier versions of this section —
failing to defer CHK-E-019 to CHK-D-003 — is now `content-engagement-audit`'s to get
right, not the orchestrator's; see that skill's own false-positive discipline section.
