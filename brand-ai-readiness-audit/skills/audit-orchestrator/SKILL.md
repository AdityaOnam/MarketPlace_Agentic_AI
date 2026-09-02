---
name: audit-orchestrator
description: The marketplace entrypoint. Given a website, runs site-evidence-collector once to gather a read-only evidence bundle, runs all four mechanism analysers (crawl-access-audit, render-extractability-audit, entity-identity-audit, engagement-defect-audit) against it, resolves the cross-skill dependencies and shared-root-cause duplicates the analysers cannot see across each other, and assembles the single structured audit report — findings with evidence and severity, prioritized suggested actions, proactive recommendations, and declared limitations. Use this skill, and only this skill, to run a full audit; the other five are invoked by it, not directly.
license: Apache-2.0
allowed-tools: []
---

# Audit Orchestrator

The marketplace's one entrypoint (`marketplace.json` marks it so). Given a URL or domain,
it produces the single audit report the brief requires. It declares no tools of its own —
every network request and every judgment happens inside the five skills it composes; this
skill's entire job is invocation order and composition.

## When to use

This is what a general agent invokes to audit a website. It is not meant to be invoked
standalone by name for a partial result — if you want just one mechanism's findings, invoke
that analyser directly against a bundle instead.

## Inputs

| Input | Required | Default |
| --- | --- | --- |
| `target` | yes | — a URL or bare domain, passed straight through to `site-evidence-collector` |
| `budget_s` | no | `300` |
| `max_static_pages` | no | `20` |
| `max_rendered_pages` | no | `3` |

## Output

One JSON audit report satisfying `round3-spec`'s required schema
(`site`, `audited_at`, `summary`, `findings[]`) plus three additions this marketplace's own
design requires (D-012): `recommendations[]`, `limitations[]`, and `degraded_stages[]`.
Full shape, the check-ID-to-title map, and the ID-assignment rule are in
[`references/report-schema.md`](references/report-schema.md).

## Procedure

1. **Collect once.** Invoke `site-evidence-collector` with `target` and the budget knobs.
   Exactly one bundle results; every analyser below reads it read-only.
2. **Run all four analysers against the bundle**, in any order — they are pure functions,
   blind to each other and to this step's order, by construction
   (`docs/ARCHITECTURE.md` §3). Collect every emitted envelope
   (`check_id`, `state`, `locus`, `evidence`, `severity`, `evidence_strength`,
   `suggested_action`, and `recommendation_only` where set).
3. **Frame access findings first.** If `crawl-access-audit` reports `CHK-D-001` present,
   note in the report preamble that downstream content findings describe content the
   blocked agent(s) will never reach — this doesn't suppress those findings (a human
   reader, or an unblocked assistant, still benefits from knowing about them), it
   contextualises them.
4. **Resolve cross-skill root causes.** Apply the dedup rule in
   [`references/composition-rules.md`](references/composition-rules.md) §1 to collapse a
   JS-only site's `CHK-D-003` + `CHK-D-004`/`CHK-D-005`/`CHK-E-019` co-occurrence on the
   same locus into one reported defect with the others attached as consequences, never as
   separate top-level findings.
5. **Assemble `findings[]`** from every envelope with `state == "present"` and no
   `recommendation_only` flag, using the title map and ID-assignment rule in
   `references/report-schema.md`. Order by severity (critical → high → medium → low), then
   `check_id` ascending, so repeated runs are comparable.
6. **Assemble `recommendations[]`** from every envelope with `recommendation_only: true`
   (currently only `CHK-E-024`), plus any check whose FP guard demoted it under the
   single-source rule at review time rather than at runtime.
7. **Assemble `limitations[]`** from the four declared, always-present limitations
   (`LIM-01`…`LIM-04` in `docs/research/EVIDENCE-LEDGER.md`) — these are structural, not
   site-specific, and are included in every report regardless of what was found.
8. **Assemble `degraded_stages[]`** from the bundle's `budget.stages[]` where
   `abandoned == true`, per `references/composition-rules.md` §3 — so a reader sees *why*
   a check reported `not_determinable` rather than assuming a bug.
9. **Compute `summary`** by counting `findings[]` only (never `recommendations[]` or
   `limitations[]`) by severity.
10. **Emit** the single report.

## Skill map

| Skill | Role | Reads |
| --- | --- | --- |
| `site-evidence-collector` | Gathers evidence; emits no findings | network |
| `crawl-access-audit` | Mechanism A (2 checks) | `robots` |
| `render-extractability-audit` | Mechanisms B, C (7 checks) | `pages`, `rendered`, `links` |
| `entity-identity-audit` | Mechanism D (7 checks) | `pages`, `anchors` |
| `engagement-defect-audit` | Mechanisms E, F (11 checks) | `pages`, `rendered` |
| `audit-orchestrator` (this skill) | Composes the above; emits no findings of its own | analyser outputs |

27 checks total, disjoint across the four analysers — see `docs/ARCHITECTURE.md` §5.

## A correction to `ARCHITECTURE.md` §4.3, made explicit here rather than left implicit

That section's "cross-skill suppression" list names three examples: `CHK-E-019` needs
`CHK-D-003`, `CHK-D-002` must yield to `CHK-D-001`, and `CHK-D-010` must yield to
`CHK-D-004`. Only the first is actually cross-skill. `CHK-D-001`/`CHK-D-002` are both owned
by `crawl-access-audit`, which already resolves that pair internally (its own procedure
step 4: "evaluate `CHK-D-002` only if `CHK-D-001` did not fire"). `CHK-D-004`/`CHK-D-010`
are both owned by `render-extractability-audit`, which resolves that pair internally the
same way. Neither reaches this skill as a cross-skill case at all — this skill will never
see both fire independently needing reconciliation, because the owning analyser already
picked one.

This is worth stating plainly rather than quietly re-implementing suppression this skill
doesn't need to do: `docs/ARCHITECTURE.md` §7's own falsification test 3 (suppression-
necessity) asks how often this skill's cross-skill suppression actually fires. The honest
answer, once the two false examples are set aside, is that it fires for exactly one pair —
`CHK-E-019`/`CHK-D-003` — which is real (the two skills are genuinely blind to each other
and genuinely compute the same underlying comparison), but narrower than §4.3 implies.

## False-positive discipline

This skill's only false-positive risk is composition-level, not detection-level: reporting
a JS-only site's single root cause as four unrelated defects would read as either padding
or an inflated severity count, which is exactly the false-positive-shaped failure
`docs/ARCHITECTURE.md` §4.3 names. The dedup rule in `references/composition-rules.md`
exists specifically to prevent that, and nothing else in this skill adjusts a severity or
suppresses a finding that its owning analyser didn't already decide to suppress or demote.
