---
name: audit-orchestrator
description: The entrypoint skill for the brand-ai-readiness-audit marketplace. Given a URL or domain, invokes site-evidence-collector once to gather the evidence bundle, then invokes all four analyser skills (crawl-access-audit, render-extractability-audit, entity-identity-audit, engagement-defect-audit) against the resulting bundle, and performs cross-skill suppression, root-cause deduplication, report assembly, and budget arbitration to produce a single structured audit report. This is the only skill in the marketplace the user invokes directly.
license: Apache-2.0
allowed-tools: []
---

# Audit Orchestrator

The entrypoint for the `brand-ai-readiness-audit` marketplace. Receives a URL or domain,
runs the full audit pipeline, and emits a single audit report.

**This skill declares no tools and makes no network requests.** All network access
happens inside `site-evidence-collector`. All four analysers are pure functions from the
evidence bundle to findings; the orchestrator is a pure function from those findings to a
report.

## When to use

This is the skill the user invokes. Any agent, given a website URL or domain to audit,
should invoke this skill (as listed in `marketplace.json` with `"entrypoint": true`).
Never invoke the four analyser skills or the collector directly for a live audit — this
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
- `limitations[]` — the four declared limitations (LIM-01…LIM-04) plus any
  `not_determinable` results caused by budget abandonment. Tells the reader what was
  and was not measured — never omitted silently.

## Procedure

Deterministic. Same input + same site state ⇒ same report, same ordering.

### Step 1 — Collect evidence

Invoke `site-evidence-collector` with `target` and `budget_s`. Receive the evidence bundle.

Inspect `bundle.budget.stages` immediately after collection. Record which stages were
abandoned (`abandoned: true`). A stage abandonment means all analyser checks that depend
on that stage's evidence will emit `not_determinable` — surface this in `limitations[]`
as "budget-constrained: {stage_name} was not completed; {N} checks could not be
evaluated."

### Step 2 — Run the four analysers

Invoke in parallel (they are independent; none reads another's output):

1. `crawl-access-audit` — pass the full bundle; receive findings for CHK-D-001, D-002.
2. `render-extractability-audit` — pass the full bundle; receive findings for CHK-D-003,
   D-004, D-005, D-009, D-010, D-011, D-013.
3. `entity-identity-audit` — pass the full bundle; receive findings for CHK-D-006,
   D-007, D-008, D-012, D-025, D-026, D-027.
4. `engagement-defect-audit` — pass the full bundle; receive findings for CHK-E-014
   through CHK-E-024.

All 27 check envelopes are received. No analyser has seen another's output.

### Step 3 — Cross-skill suppression

Resolve dependencies that cross analyser boundaries. Each rule below: if the condition
is met, set the dependent finding's `state` to `"suppressed"` and add the suppressor's
check ID to its `suppressed_by` field.

**Rule O-1 — CHK-E-019 deferred to CHK-D-003 (the one genuinely cross-skill dependency):**
If CHK-D-003 is `present` (JS-render gap confirmed by `render-extractability-audit`)
**and** CHK-E-019 is also `present` (blank first paint confirmed by
`engagement-defect-audit`), they share the same root cause: a JavaScript-only site with
no static content. Suppress CHK-E-019 and carry it as a consequence in the deduplication
step (Step 4). Do not drop CHK-E-019; it is collapsed, not lost.

**Note on intra-skill suppressions already resolved:** Several suppression relationships
that ARCHITECTURE.md §4.3 describes as "cross-skill" are in fact already resolved inside
individual analysers by their own FP guards:
- CHK-D-002 yields to CHK-D-001: handled inside `crawl-access-audit` (the skill only
  evaluates CHK-D-002 if CHK-D-001 did not fire).
- CHK-D-010 yields to CHK-D-004: handled inside `render-extractability-audit` (CHK-D-010
  is suppressed when CHK-D-004 fires).

The orchestrator does not need to re-apply these — doing so would be redundant. The one
genuinely cross-skill suppression requiring orchestrator-level handling is O-1 above.

### Step 4 — Root-cause deduplication

A JS-only site with no static content will legitimately trip CHK-D-003, CHK-D-004,
CHK-D-005, and CHK-E-019 — four separate findings for one root cause. Reporting four
independent findings for one defect is a false-positive-shaped failure even though each
check is individually correct.

**JS-only dedup rule (O-2):** If all of the following fire as `present`:
- CHK-D-003 (JS-render gap: raw HTML has <50 words and no h1, rendered has ≥200 words)
- CHK-D-004 (thin main content: raw extraction <200 words)
- CHK-D-005 (absent/generic headings in extracted text)
- CHK-E-019 (blank first paint, suppressed in Step 3)

Collapse them into one finding with:
- `id`: the CHK-D-003 finding ID (it is the root cause)
- `title`: "JavaScript-only site — primary content invisible to non-rendering AI retrievers"
- `severity`: critical (HARD-MECHANICAL root; CHK-D-003's ceiling)
- `evidence`: combine the evidence strings from all four envelopes
- `consequences`: list CHK-D-004, D-005, E-019 as downstream consequences in the
  finding body (not as separate findings)
- `suggested_action`: implement SSR or SSG (the fix resolves all four simultaneously)

**When to apply:** Only when all four are simultaneously `present`. If CHK-D-003 fires
alone, or with only one of the others, report them independently — the co-occurrence
pattern is what establishes JS-only as the single root cause.

**General dedup principle:** For any other cluster of ≥3 findings that share an
immediately obvious single root cause (e.g., every heading check failing because the
entire site has no HTML structure), collapse similarly. Document the collapse in the
finding body. Do not collapse findings that merely have the same severity or mechanism.

### Step 5 — Separate findings from recommendations

After suppression and dedup:

- **Findings:** all envelopes with `state == "present"` that are not suppressed, not
  routed to recommendations, and not collapsed as consequences in Step 4.
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

### Step 6 — Assemble and emit the report

1. Sort `findings[]` by severity (`critical > high > medium > low`), then by check ID
   (ascending lexicographic) within each severity tier. This makes runs comparable.
2. Count `total_findings`, `critical`, `high`, `medium`, `low` from `findings[]` only.
   Recommendations and limitations are not counted in `summary`.
3. Emit the full report conforming to `references/report-schema.md`.

Full report schema (field definitions, required vs. optional, and example):
[`references/report-schema.md`](references/report-schema.md).

## What the orchestrator is, and what it is not

The orchestrator is not a concatenator. It owns four things no individual analyser can
do — cross-skill suppression, root-cause deduplication, report assembly under D-012, and
budget arbitration — because analysers are blind to each other by design.

The decomposition's value is tested by whether the orchestrator's cross-skill logic
actually fires. On a JS-only site, the O-1/O-2 dedup collapses four findings to one;
without the orchestrator, a user would receive a report with four separate findings for
one fix. That collapse is the orchestrator's tangible, non-decorative contribution.

If the suppression-necessity test (ARCHITECTURE.md §7) shows these rules never fire
across the dev corpus, the decomposition is decorative and the skills should be merged.
This is recorded honestly here rather than concealed.

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

## Checks at a glance — all 27 checks and their owners

| Analyser | Checks | Evidence |
| --- | --- | --- |
| `crawl-access-audit` | CHK-D-001, D-002 | `robots` |
| `render-extractability-audit` | CHK-D-003, D-004, D-005, D-009, D-010, D-011, D-013 | `pages`, `rendered`, `links` |
| `entity-identity-audit` | CHK-D-006, D-007, D-008, D-012, D-025, D-026, D-027 | `pages`, `anchors` |
| `engagement-defect-audit` | CHK-E-014 – E-024 | `pages`, `rendered` |

27 checks, disjoint. No check appears in two skills.

## False-positive discipline

The orchestrator's primary false-positive risk is in Step 4: over-aggressive deduplication
that collapses independent defects into one reported finding, causing real problems to
disappear from the report.

The guard: **only collapse when all listed co-occurrence conditions hold simultaneously.**
Two findings for two different root causes that happen to appear together on the same site
must be reported separately. When in doubt, report separately — the cost of one extra
finding is lower than the cost of hiding a real defect.

The secondary risk is in Step 3: failing to apply the O-1 suppression (leaving both
CHK-D-003 and CHK-E-019 as separate findings on a JS-only site). Both checks must be
`present` for the rule to apply. If only one fires, report it alone.
