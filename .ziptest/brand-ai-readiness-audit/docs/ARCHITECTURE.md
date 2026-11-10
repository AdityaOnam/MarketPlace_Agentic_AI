# Architecture — skill decomposition and composition contract

Resolves R-6. The ledger had pre-committed all checks to a single `marketplace_auditor`
by default; this document makes the decision deliberately. Recorded as **D-013**, revised
by **D-025** on 2026-09-04.

**This file is authoritative for check ownership.** The `Owning skill` column in
`research/EVIDENCE-LEDGER.md` is superseded by the skill map in §5.

---

## 1. The decision

**Five skills: one collector, three analysers, one entrypoint orchestrator.** Started as
six (one collector, four analysers, one orchestrator) under D-013; two of the four
analysers merged into `content-engagement-audit` under D-025 once §7's merge test had
real evidence behind it rather than an open question.

```
brand-ai-readiness-audit/
  marketplace.json
  skills/
    audit-orchestrator/        <- ENTRYPOINT: composes, emits the report
    site-evidence-collector/   <- the only skill permitted to touch the network
    crawl-access-audit/        <- mechanism A
    content-engagement-audit/  <- mechanisms B, C, E, F (merged 2026-09-04, D-025)
    entity-identity-audit/     <- mechanism D
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
  in one auditable place rather than being re-implemented across every analyser.
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

This section's history is the honest record of a claim that was tested down to what
survives, not a design that got smaller by accident. It originally claimed four things no
analyser could do. Two didn't survive contact with evidence and were removed; two remain.

1. **~~Cross-skill suppression~~ — retired 2026-09-04, D-025.** `CHK-E-019` (blank first
   paint) and `CHK-D-003` (render-gap) independently measure the same mechanism, so one
   used to defer to the other here (rule O-1) — the one genuinely cross-skill suppression
   this layer needed to do, per D-013's original design. §7's suppression-necessity test
   found, against the real 36-site dev+negative corpus, that O-1 never actually fired: the
   two checks never both reached `present` on the same real site. That result was the
   evidence for merging `render-extractability-audit` and `engagement-defect-audit` into
   `content-engagement-audit`; O-1 is now applied in-skill, inside that merged analyser's
   own `evaluate()`, the same way `CHK-D-004` already self-suppressed against `CHK-D-003`
   before the merge. There is no cross-skill suppression left for the orchestrator to do —
   `compose_report.py`'s `apply_suppression` function was removed accordingly.
2. **~~Deduplication of shared root causes~~ — removed, D-016.** The original design here
   claimed a JS-only site legitimately trips D-003, D-004, D-005 and E-019 together, and
   the orchestrator collapsed all four into one finding with the rest listed as
   consequences. Running §7's suppression-necessity test found this pattern is
   mathematically unreachable: D-003 and E-019 both require the homepage's raw
   `main_text_words < 50`, while D-005 requires `main_text_words > 500` on that same page
   before it evaluates at all. Those two thresholds cannot both hold for one page's word
   count, so the four-way collapse could never fire — not a corpus finding, a provable one
   from the check definitions. Removed from `compose_report.py`; §7 and `docs/DECISIONS.md`
   D-016 keep the full writeup rather than silently dropping the claim.
3. **Report assembly under D-012.** `findings[]` for defects only, with the severity summary
   counted from them; `recommendations[]` for beyond-defect proactive items and for checks
   demoted under the single-source rule; `limitations[]` for LIM-01…05 (D-014 added LIM-05
   for llms.txt). Stable ordering by severity then check ID, so runs are comparable.
4. **Budget arbitration and graceful degradation.** Deciding, from `budget`, which analysers
   run and what is reported as not-determinable when a stage was abandoned — including the
   no-headless-browser case (D-015), where the render stage is abandoned before it starts.

**What survives is items 3 and 4 — genuinely structural, independent of how many analysers
sit upstream.** Some layer has to sort findings, translate `budget.stages` into
`limitations[]`, and hold the report schema stable across runs; that layer is this one,
regardless of whether it composes three analysers' output or thirty. That is a narrower
claim than D-013 originally made, and it is the honest one.

### 4.4 Site-wide roll-up (D-019)

The orchestrator's second cross-cutting rule, added 2026-09-04 after the first contact with
real multi-page sites. One shared-template defect was emitting one finding per sampled page
— up to 17 findings for one fix. `roll_up_site_wide` groups findings by check, subcheck and
URL/integer-masked evidence, and collapses any group spanning ≥3 pages into a single finding
carrying `occurrences: {pages, examples[]}` at the group's worst severity.

It belongs here rather than in an analyser because it operates on the assembled output, but
note carefully what it is **not**: it groups findings *within* a check, so unlike O-1 it was
never evidence for keeping analysers split and was correctly not counted as such in §7's
merge test.

## 5. Skill map

| Skill | Mechanism | Checks | Evidence consumed |
| --- | --- | --- | --- |
| `crawl-access-audit` | A | CHK-D-001, D-002 | `robots`, `discovery` |
| `content-engagement-audit` | B, C, E, F | CHK-D-003, D-004, D-005, D-009, D-010, D-011, D-013, CHK-E-014 … E-022, E-024 | `pages`, `rendered`, `links` |
| `entity-identity-audit` | D | CHK-D-006, D-007, D-008, D-012, D-025, D-026, D-027 | `pages`, `anchors` |
| `site-evidence-collector` | — | none (emits no findings) | network |
| `audit-orchestrator` | — | none (emits no findings of its own) | analyser outputs |

26 checks, disjoint. No check appears in two skills. (27 were authored; CHK-E-023 was cut
on 2026-09-04 as D-018 — it could only read `rendered[]`, empty in every graded run, and
was already the most false-positive-prone check in the ledger.)

## 6. Why not fewer, why not more

**Why not one skill?** A single skill scores fully on composition per the brief, so this
needs a real answer. The honest one, revised after §7's merge test: the collector boundary
buys enforceable determinism and an enforceable budget regardless of analyser count, and
`crawl-access-audit` (reads a text file, emits hard-mechanical verdicts) and
`entity-identity-audit` (reads structured data and cross-page text, emits mostly
theoretical/practitioner-strength verdicts) remain genuinely different in evidence type and
severity semantics from `content-engagement-audit` and from each other. The pair that
*wasn't* genuinely different — `render-extractability-audit` and `engagement-defect-audit`
— **was tested and merged**, per §7. This is not a hypothetical anymore: one merge has
already happened on real evidence, which is the strongest argument that the remaining
three-way split isn't just taste — the axis that failed the test didn't survive it.

**Why not eight or ten?** Splitting `entity-identity-audit` into identity / canonical /
freshness, or splitting `content-engagement-audit` per WCAG criterion, would produce skills
that share the same evidence, the same severity semantics, and the same fix vocabulary.
That is the definition of padding, and now has a concrete illustration: it is exactly the
shape of split §7 found unjustified and reversed.

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

Test 3 is the one that would most embarrass this design, which is why it was written down
here rather than left to be discovered later. It did.

**Partial result, 2026-09-03 (D-016), ahead of any real corpus.** Phase 4 hadn't run yet —
there was no dev corpus — but part of Test 3 didn't need one: the JS-only four-way dedup
(§4.3's old point 2) turned out to be provably unreachable from the check definitions
alone (D-003/E-019 need `main_text_words < 50`, D-005 needs `> 500`, same page, mutually
exclusive), so it was removed rather than kept as an untested claim. That left exactly one
cross-skill rule, O-1 (E-019 defers to D-003). A synthetic-bundle run (5 hand-built
scenarios, not the dev corpus) found O-1 fires whenever the homepage is JS-only-shaped,
including under D-015's no-headless-browser sandbox condition — so the orchestrator was
not a pure concatenator, but its genuine cross-skill surface was smaller than originally
designed: one rule, not two. Left as an open question: whether one real rule is enough to
justify four analyser skills, versus folding `render-extractability-audit` and
`engagement-defect-audit` together since they're the only pair O-1 connects.

**Test 3, resolved on the real corpus, 2026-09-04 (D-025).** Phase 4's harness now exists
(`harness/`). `harness/ablation.py` ran leave-one-skill-out against the full 36-site
dev+negative corpus and, specifically, tested whether removing the skill that owns
`CHK-D-003` changes what `CHK-E-019` does anywhere. **On all 36 real sites, no.** The two
checks never both reached `present` on the same site — O-1's synthetic-scenario result
(5 hand-built cases, all fired) did not hold on real data. Test 3's answer is now
unambiguous rather than open: the orchestrator's cross-skill surface, once corpus-tested,
was zero.

**Test 1 (merge test), run the same day.** `render-extractability-audit` and
`engagement-defect-audit` merged into `content-engagement-audit`: their check functions
concatenated into one module, one `SKILL.md`, one `references/checks.md`, O-1 moved
in-skill. Re-run against all 42 available sites (dev, negative-control, adversarial) —
**every finding, every locus, every severity, byte-identical to the pre-merge two-skill
output**, because the merge changed no check logic, only which file it lives in. Schema
conformance unaffected (0 failures before, 0 after). Runtime unaffected — these are the
same Python function calls either way; the merge cannot move wall-clock time. **The
boundary bought nothing measurable, so it was merged for real** — this is the disjoint
partition that failed the test, not a hypothetical one, which is what makes §6's "why not
eight or ten" argument concrete rather than assumed.

**Test 2 (bundle-sufficiency) — held throughout, and re-checked mechanically 2026-09-04.**
No analyser script (`crawl_access_checks.py`, `content_engagement_checks.py`,
`entity_identity_checks.py`) imports any networking module — grepped, zero matches. This
was always structurally guaranteed by the collector boundary (§3); the merge changes
nothing about it, since `content-engagement-audit` inherits the same guarantee its two
predecessor skills already had.

**What this leaves.** `crawl-access-audit` and `entity-identity-audit` remain split from
`content-engagement-audit` and from each other on the strength of §6's evidence-type/
severity-semantics argument, which has not been tested the way O-1 was — there is no
known cross-skill dependency left to test between them, which is either confirmation they
are correctly separated or an untested assumption, depending on how much weight the
absence of a found dependency should carry. Recorded as open rather than resolved.

## 8. Manifest

```json
{
  "name": "brand-ai-readiness-audit",
  "version": "1.0.0",
  "skills": [
    { "id": "audit-orchestrator", "path": "skills/audit-orchestrator", "entrypoint": true },
    { "id": "site-evidence-collector", "path": "skills/site-evidence-collector" },
    { "id": "crawl-access-audit", "path": "skills/crawl-access-audit" },
    { "id": "content-engagement-audit", "path": "skills/content-engagement-audit" },
    { "id": "entity-identity-audit", "path": "skills/entity-identity-audit" }
  ]
}
```

Exactly one entrypoint. `site-evidence-collector` declares network tools; **no other skill
declares any**, which is how the read-only and budget guarantees are enforced rather than
promised.
