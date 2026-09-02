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
  "limitations": [ ... ]
}
```

`summary.total_findings` counts only `findings[]` entries. Recommendations and
limitations are not findings and are not counted there.

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
  },
  "consequences": []
}
```

Optional field `consequences` (added by orchestrator dedup in Step 4): an array of
`check_id` strings for checks that were collapsed into this finding as downstream
consequences.

Findings are ordered: severity descending (`critical → high → medium → low`), then
`check_id` ascending within each tier.

---

## `recommendations[]` entry

Beyond-defect proactive improvements, and checks demoted under the single-source rule
(CHK-E-024). Not counted in `summary.total_findings`.

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
  "description": "Stage 'render_pass' was abandoned after 74.9s (budget: 75s, 2/3 pages completed). The following checks could not be evaluated: CHK-D-003 (page 3), CHK-E-014 (contrast), CHK-E-015 (overflow), CHK-E-016, CHK-E-018, CHK-E-019, CHK-E-023. Results for these checks read as 'could not measure', not as 'no defect found'.",
  "affected_checks": ["CHK-D-003", "CHK-E-014", "CHK-E-015", "CHK-E-016", "CHK-E-018", "CHK-E-019", "CHK-E-023"]
}
```

---

## The four declared limitations (always included)

These are always emitted, even if no budget stages were abandoned, because they describe
what the audit is structurally incapable of measuring:

| ID | Title |
| --- | --- |
| LIM-01 | Cross-web corroboration not measured |
| LIM-02 | Name-collision detection not performed |
| LIM-03 | Current AI assistant citation status not queried |
| LIM-04 | Field engagement outcomes not observable |

Full descriptions are in `docs/research/EVIDENCE-LEDGER.md` under "Declared limitations."
