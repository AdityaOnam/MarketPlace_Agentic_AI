# Audit report schema

The schema the orchestrator emits. `findings[]` is the required floor from
`round3-spec/SKILL.md §2`; `recommendations[]` and `limitations[]` are the extensions
defined in D-012.

---

## Top-level structure

```json
{
  "schema_version": "1.0.0",
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "preamble": {
    "access_blocked_for": [],
    "notes": [],
    "archetype": "ecommerce",
    "recommendations_scoped_to": "ecommerce"
  },
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 0,
    "not_determinable_count": 2,
    "recommendations_count": 3,
    "limitations_count": 2
  },
  "findings": [ ... ],
  "recommendations": [ ... ],
  "limitations": [ ... ],
  "degraded_stages": [ ... ],
  "meta_evaluation": {
    "checks_run": ["summary_reconciles", "severity_counts_reconcile", "finding_complete",
                    "no_duplicate_findings", "known_check_id", "prohibited_recommendation",
                    "limitations_present"],
    "passed": true,
    "warnings": []
  }
}
```

`summary.total_findings` counts only `findings[]` entries. Recommendations and
limitations are not findings and are not counted there.

`preamble.archetype` records the vertical the audit assumed, and
`recommendations_scoped_to` states plainly that every suggested action below was written
for that vertical — the archetype gates which checks ran at all and how each action is
worded, so a reader needs to know which one was assumed. `unknown` means no archetype
rule matched and every archetype-conditioned check was suppressed rather than guessed at.

`meta_evaluation` is the orchestrator's own self-check over the assembled report
(SKILL.md Step 7). `warnings` are advisory and are **never** silently corrected — a
report that quietly edits itself until its own audit passes is the exact failure mode
D-010 was written against, so a surviving warning is the system working.

---

## `findings[]` entry

Required per the spec (`round3-spec/SKILL.md §2`). Every entry is a detected defect.

```json
{
  "id": "F-001",
  "check_id": "CHK-D-001",
  "title": "Retrieval-time AI crawler blocked at root",
  "severity": "critical",
  "evidence": "robots.txt line 12: Disallow: / applies to GPTBot (retrieval-time AI crawler).",
  "locus": { "url": "https://www.example.com/robots.txt", "selector": null },
  "evidence_strength": "HARD-MECHANICAL",
  "suggested_action": {
    "summary": "Narrow the Disallow rule to paths that actually need protection rather than the site root. Remove the blanket Disallow: / for GPTBot.",
    "priority": "critical"
  }
}
```

### `occurrences` — present only on rolled-up findings

One site-template defect repeats on every page built from that template. Emitting it once
per page turns a report into a laundry list in which the single worst problem occupies
seventeen slots, which is fatal to the prioritisation the brief actually asks for. When a
defect is found on **3 or more** sampled pages, the orchestrator emits it once:

```json
{
  "id": "F-002",
  "check_id": "CHK-E-022",
  "severity": "medium",
  "evidence": "Site-wide: 17 sampled pages share this defect. missing <main> landmark. Violates structural conventions (WCAG 2.2 SC 1.3.1).",
  "locus": { "url": null, "scope": "site" },
  "occurrences": { "pages": 17, "examples": ["https://…/a", "https://…/b", "https://…/c"] }
}
```

Severity is the **worst** in the collapsed group, never an average — a defect is as serious
as its worst instance. Below 3 pages, findings stay itemised with their own `locus`, because
at one or two pages the defect is plausibly specific to those pages and the URL is
information the reader needs. See **D-019**.

No `consequences` field. An earlier design collapsed multi-check clusters into one root
finding carrying a `consequences` array; the one cluster this was built for (CHK-D-003 +
D-004 + D-005 + E-019 co-occurring) was proven unreachable by the suppression-necessity
test and removed as **D-016** — CHK-D-003/E-019 require the homepage's word count to be
<50 while CHK-D-005 requires it to be >500 on the same page, so all four can never be
`present` simultaneously. Findings therefore never carry `consequences`; the one real relationship between
CHK-D-003 and CHK-E-019 (the latter deferring to the former) is expressed entirely through
`state: "suppressed"` / `suppressed_by` on the deferred finding. It is applied in-skill by
`content-engagement-audit` as of **D-025**, not by the orchestrator — both checks are now
computed by the same analyser, so there is no cross-skill relationship left to express.

Findings are ordered: severity descending (`critical → high → medium → low`), then
`check_id` ascending within each tier.

---

## `recommendations[]` entry

Beyond-defect proactive improvements, and checks demoted to recommendation-only
(`CHK-D-010`, `CHK-D-011`, `CHK-D-013`, `CHK-E-021`, `CHK-E-024`). Not counted in
`summary.total_findings`.

`locus`/`severity` are carried through from the underlying envelope (added 2026-09-09):
D-012's schema is explicitly "a floor, not a ceiling," and without them Stage E's matching
rule (`EVALS.md` §2 — same check, same locus) has no locus to match against for any of
these five checks.

```json
{
  "id": "R-001",
  "check_id": "CHK-E-024",
  "title": "Add trust signals to commercial pages",
  "rationale": "Commercial and news sites with visible contact information, HTTPS, and byline dates are easier for users and AI systems to assess as credible.",
  "mechanism": "E",
  "suggested_action": {
    "summary": "Add contact information, organisation name in footer, HTTPS, and byline dates on articles. (Proactive — not a confirmed defect.)",
    "priority": "low"
  },
  "locus": {"url": "https://example.com/pricing", "selector": null},
  "severity": "low",
  "route_reason": "single-source rule (D-004): supporting evidence is one unreplicated study."
}
```

---

## `limitations[]` entry

Declared limitations and budget-constrained not-determinable results.

```json
{
  "id": "L-001",
  "lim_id": "LIM-01",
  "title": "Cross-web corroboration not measured",
  "description": "Whether other sites agree with this brand's own facts requires a search or web-scale index API. No free, deterministic, rate-safe source exists. CHK-D-025/026/027 audit only the anchoring the site itself provides; actual cross-web corroboration was not and cannot be measured by this audit.",
  "affected_checks": ["CHK-D-025", "CHK-D-026", "CHK-D-027"]
}
```

For budget-constrained limitations (abandoned stages):

```json
{
  "id": "L-005",
  "lim_id": "BUDGET-render_pass",
  "title": "Render stage abandoned — render-dependent checks not evaluated",
  "description": "Stage 'render_pass' was abandoned after 74.9s (budget: 75s, 2/3 pages completed). The following checks could not be evaluated: CHK-D-003 (page 3), CHK-E-014 (contrast), CHK-E-015 (overflow), CHK-E-016, CHK-E-018, CHK-E-019. Results for these checks read as 'could not measure', not as 'no defect found'.",
  "affected_checks": ["CHK-D-003", "CHK-E-014", "CHK-E-015", "CHK-E-016", "CHK-E-018", "CHK-E-019"]
}
```

---

## The five declared limitations (always included)

These are always emitted, even if no budget stages were abandoned, because they describe
what the audit is structurally incapable or unwilling to do:

| ID | Title |
| --- | --- |
| LIM-01 | Cross-web corroboration not measured |
| LIM-02 | Name-collision detection not performed |
| LIM-03 | Current AI assistant citation status not queried |
| LIM-04 | Field engagement outcomes not observable |
| LIM-05 | llms.txt not recommended as a substantive fix (D-014) |

LIM-05 differs from LIM-01…04 in kind: it is not a capability gap but a declared policy
refusal (D-007), stated per D-014 so it reads as a deliberate position rather than an
omission — the officials confirmed recommending llms.txt is acceptable, so silence here
would look indistinguishable from having missed it.

Full descriptions are in `docs/research/EVIDENCE-LEDGER.md` under "Declared limitations."

---

## Check-ID → title map

`findings[].title` and `recommendations[].title` are filled from this fixed table, not
phrased ad hoc per run — a title generated fresh each time would break the byte-identical
comparability D-010's `pass^k` stability check needs across repeated runs on the same
bundle.

| Check | Title |
| --- | --- |
| CHK-D-001 | Retrieval-time AI crawler blocked at root |
| CHK-D-002 | Training-corpus crawler blocked, retrieval intact |
| CHK-D-003 | Primary content and h1 missing from raw HTML (JS-render gap) |
| CHK-D-004 | Thin main content |
| CHK-D-005 | Missing or generic subheadings |
| CHK-D-006 | No explicit organisation-definition sentence |
| CHK-D-007 | Missing or incomplete Organization JSON-LD |
| CHK-D-008 | Missing or cross-domain canonical tag |
| CHK-D-009 | Broken internal links |
| CHK-D-010 | Low extractable-evidence density |
| CHK-D-011 | Pronoun-saturated key claims |
| CHK-D-012 | Missing date on time-sensitive content |
| CHK-D-013 | Near-duplicate templated content |
| CHK-D-025 | No declared identity anchors |
| CHK-D-026 | Declared identity anchors do not resolve |
| CHK-D-027 | Inconsistent organisation identity attributes |
| CHK-E-014 | Machine-detectable accessibility violations |
| CHK-E-015 | Mobile viewport blocks zoom or overflows horizontally |
| CHK-E-016 | Tap targets below WCAG 2.2 minimum size |
| CHK-E-017 | Non-descriptive link text |
| CHK-E-018 | Content-blocking overlay present at load |
| CHK-E-019 | Blank first paint with no fallback |
| CHK-E-020 | Autoplaying media with sound |
| CHK-E-021 | Images/iframes missing dimensions (layout-shift cause) |
| CHK-E-022 | Missing landmark or heading structure |
| CHK-E-024 | Missing trust signals |

Every finding uses its check's fixed title from this table. There is no merged-finding
special case (see the `consequences` note above — D-016 removed the only rule that would
have produced one).
