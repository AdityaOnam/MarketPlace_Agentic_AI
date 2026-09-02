# Architecture — skill decomposition and composition contract

Resolves R-6. The ledger had pre-committed all checks to a single `marketplace_auditor`
by default; this document makes the decision deliberately. Recorded as **D-013**.

**This file is authoritative for check ownership.** The `Owning skill` column in
`research/EVIDENCE-LEDGER.md` is superseded by the skill map in §5.

---

## 1. The decision

**Six skills: one collector, four analysers, one entrypoint orchestrator.**

```
brand-ai-readiness-audit/
  marketplace.json
  skills/
    audit-orchestrator/        <- ENTRYPOINT: composes, resolves, emits the report
    site-evidence-collector/   <- the only skill permitted to touch the network
    crawl-access-audit/        <- mechanism A
    render-extractability-audit/  <- mechanisms B, C
    entity-identity-audit/     <- mechanism D
    engagement-defect-audit/   <- mechanisms E, F
  README.md
```

## 2. Why this axis, and not another

The rubric rewards "genuine separation of concerns" and punishes padding. Three axes were
considered.

**By page type** (home / product / article / contact) — rejected. Checks would be
duplicated across skills, and D-009 already requires page-type conditioning *within* each
check. This would smear one concern across every skill.

**By pipeline stage** (fetch → parse → judge) — rejected as the primary axis. It cuts every
mechanism into three pieces, so no skill can be reasoned about or reused on its own, and a
finding's evidence would be assembled across three boundaries.

**By mechanism, with I/O extracted** — chosen. The brief's own appendix (A–F) is the task's
ontology, and each mechanism has a genuinely different evidence type, failure mode, and
severity semantics. The one deviation from a pure mechanism split is pulling network I/O
into its own skill, for the reason in §3.

## 3. The collector is the load-bearing boundary

`site-evidence-collector` is the only skill allowed to make a network request. Everything
else is a pure function from an evidence bundle to findings.

This is the design decision that does the most work:

- **It enforces the runtime budget structurally.** R-4 required one shared headless render
  pass across seven checks. If each analyser could fetch, that constraint would be a
  convention that any future check could silently break. Here it is impossible to break —
  analysers have no network tool declared.
- **It makes the analysers deterministic and unit-testable.** Same bundle in, same findings
  out, with no network variance. This is what makes D-010's `pass^k` stability at k=5
  achievable at all.
- **It localises every guardrail.** robots.txt compliance, rate limiting, page caps,
  timeouts, the no-authenticated-areas rule, and the bounded off-site HEAD checks all live
  in one auditable place rather than being re-implemented four times.
- **It matches how the eval works.** D-010 grades against frozen snapshots; a snapshot *is*
  a bundle. The analysers run identically against a live collection or a fixture.

## 4. Composition contract

### 4.1 Collector output — the evidence bundle

One JSON document. Analysers receive it read-only and may not extend it.

| Section | Contents |
| --- | --- |
| `site` | canonical host, resolved origin, redirect chain |
| `robots` | robots.txt body, parse result, per-agent rules, fetch status |
| `discovery` | sitemap presence and entries, page inventory, archetype label per page |
| `pages[]` | per page: final URL, status, headers, raw HTML, extracted main text, page-type label |
| `rendered[]` | for ≤3 sampled pages: rendered DOM, computed styles, element geometry, 375 px and desktop captures |
| `links` | internal link inventory with HEAD statuses (≤20) |
| `anchors` | declared identity anchors with HEAD statuses (≤8, one per host) |
| `budget` | per-stage wall-clock, and which stages were abandoned |

Every section carries a status of `ok`, `partial`, or `unavailable` with a reason. An
analyser seeing anything but `ok` for the evidence a check needs must emit
`not_determinable` — never infer.

### 4.2 Analyser output — the finding envelope

Each analyser returns a flat list. No analyser sees another's output, so none can suppress
across a boundary.

```json
{
  "check_id": "CHK-D-003",
  "state": "present | absent | not_determinable | not_applicable",
  "locus": { "url": "...", "selector": "..." },
  "evidence": "verbatim string present in the bundle",
  "severity": "critical | high | medium | low",
  "evidence_strength": "HARD-MECHANICAL | CAUSAL | NORMATIVE | CORRELATIONAL | THEORETICAL",
  "suggested_action": { "summary": "...", "priority": "..." },
  "suppressed_by": ["CHK-D-001"]
}
```

`absent` and `not_applicable` are reported, not dropped — the negative-control eval needs
to distinguish "checked and clean" from "never ran".

### 4.3 What the orchestrator actually does

This is where the "not padding" case is won or lost. The orchestrator is not a
concatenator; it owns four things no analyser can:

1. **Cross-skill suppression.** Real dependencies cross boundaries. `CHK-E-019` (blank
   first paint, engagement) is only meaningful given `CHK-D-003`'s render comparison
   (extractability). `CHK-D-002` must yield to `CHK-D-001`. `CHK-D-010` must yield to
   `CHK-D-004`. Because analysers are blind to each other, resolving these is structurally
   the orchestrator's job.
2. **Deduplication of shared root causes.** A JS-only site legitimately trips D-003, D-004,
   D-005 and E-019. Reporting four findings for one defect is a false-positive-shaped
   failure even though each check is individually correct. The orchestrator collapses these
   to the root cause and lists the rest as consequences.
3. **Report assembly under D-012.** `findings[]` for defects only, with the severity summary
   counted from them; `recommendations[]` for beyond-defect proactive items and for checks
   demoted under the single-source rule; `limitations[]` for LIM-01…04. Stable ordering by
   severity then check ID, so runs are comparable.
4. **Budget arbitration and graceful degradation.** Deciding, from `budget`, which analysers
   run and what is reported as not-determinable when a stage was abandoned.

## 5. Skill map

| Skill | Mechanism | Checks | Evidence consumed |
| --- | --- | --- | --- |
| `crawl-access-audit` | A | CHK-D-001, D-002 | `robots`, `discovery` |
| `render-extractability-audit` | B, C | CHK-D-003, D-004, D-005, D-009, D-010, D-011, D-013 | `pages`, `rendered`, `links` |
| `entity-identity-audit` | D | CHK-D-006, D-007, D-008, D-012, D-025, D-026, D-027 | `pages`, `anchors` |
| `engagement-defect-audit` | E, F | CHK-E-014 … E-024 | `pages`, `rendered` |
| `site-evidence-collector` | — | none (emits no findings) | network |
| `audit-orchestrator` | — | none (emits no findings of its own) | analyser outputs |

27 checks, disjoint. No check appears in two skills.

## 6. Why not fewer, why not more

**Why not one skill?** A single skill scores fully on composition per the brief, so this
needs a real answer. The honest one: the collector boundary buys enforceable determinism
and an enforceable budget, and the four analysers have genuinely different evidence types
and severity semantics — `crawl-access-audit` reads a text file and emits hard-mechanical
verdicts; `engagement-defect-audit` reads rendered geometry and emits mostly normative ones.
Merging them would put a `NORMATIVE`-ceiling concern and a `critical`-ceiling concern behind
one set of instructions. **If the ablation in §7 fails to justify a boundary, we merge it.**

**Why not eight or ten?** Splitting `entity-identity-audit` into identity / canonical /
freshness, or splitting engagement per WCAG criterion, would produce skills that share the
same evidence, the same severity semantics, and the same fix vocabulary. That is the
definition of padding.

## 7. How this decomposition can be falsified

D-010's leave-one-skill-out ablation is necessary but **weak on its own**: any disjoint
partition passes it, because removing any skill removes its checks and recall drops
mechanically. Stating that plainly matters more than claiming a test we haven't earned.

Three sharper tests:

1. **Merge test.** For each adjacent pair, merge them and re-run the full eval. If precision,
   stability and runtime are unchanged, the boundary bought nothing — merge it for real.
2. **Bundle-sufficiency test.** Each analyser must run to completion on the bundle alone,
   with the network disabled. Any analyser that needs a fetch has the wrong boundary.
3. **Suppression-necessity test.** Count how often the orchestrator's cross-skill
   suppression and dedup actually fire across the dev corpus. If they never fire, the
   orchestrator *is* a concatenator and the decomposition is decorative.

Test 3 is the one that would most embarrass this design, which is why it is written down
here rather than discovered later.

## 8. Manifest

```json
{
  "name": "brand-ai-readiness-audit",
  "version": "1.0.0",
  "skills": [
    { "id": "audit-orchestrator", "path": "skills/audit-orchestrator", "entrypoint": true },
    { "id": "site-evidence-collector", "path": "skills/site-evidence-collector" },
    { "id": "crawl-access-audit", "path": "skills/crawl-access-audit" },
    { "id": "render-extractability-audit", "path": "skills/render-extractability-audit" },
    { "id": "entity-identity-audit", "path": "skills/entity-identity-audit" },
    { "id": "engagement-defect-audit", "path": "skills/engagement-defect-audit" }
  ]
}
```

Exactly one entrypoint. `site-evidence-collector` declares network tools; **no other skill
declares any**, which is how the read-only and budget guarantees are enforced rather than
promised.
