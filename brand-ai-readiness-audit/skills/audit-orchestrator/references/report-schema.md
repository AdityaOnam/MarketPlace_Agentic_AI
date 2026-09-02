# Report schema — audit-orchestrator

The final report this skill emits. Satisfies `round3-spec`'s required schema exactly
(`site`, `audited_at`, `summary`, `findings[]` with `id`/`title`/`severity`/`evidence`/
`suggested_action` on every entry) and adds the three top-level arrays **D-012** requires:
`recommendations[]`, `limitations[]`, plus `degraded_stages[]` from
`composition-rules.md` §3. Extra fields are explicitly permitted by the handout ("a floor,
not a ceiling").

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "preamble": {
    "access_blocked_for": [],
    "notes": []
  },
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3,
    "low": 0
  },
  "findings": [
    {
      "id": "F-001",
      "check_id": "CHK-D-003",
      "title": "Primary content and h1 missing from raw HTML (JS-render gap)",
      "severity": "critical",
      "evidence": "Homepage: raw HTTP fetch contains 12 words of main text and 0 h1; rendered DOM contains 812 words and 1 h1.",
      "evidence_strength": "HARD-MECHANICAL",
      "locus": { "url": "https://example.com/" },
      "consequences": [
        { "check_id": "CHK-D-004", "evidence": "..." }
      ],
      "suggested_action": {
        "summary": "Implement server-side rendering or static generation so primary content and the h1 are present in the initial HTTP response.",
        "priority": "critical"
      }
    }
  ],
  "recommendations": [
    {
      "check_id": "CHK-E-024",
      "summary": "Add visible contact information, an organisation name in the footer, HTTPS, and byline dates.",
      "priority": "low",
      "rationale": "Commonly cited as a trust signal for commercial/news content, but resting on single-study support (docs/research/EVIDENCE-LEDGER.md) — shipped as a recommendation, not a scored finding, under the single-source rule.",
      "mechanism": "E"
    }
  ],
  "limitations": [
    {
      "id": "LIM-01",
      "mechanism": "D",
      "reason": "Actual agreement across the wider web about the brand's facts requires a search or web-scale index API; no free, deterministic, rate-safe source exists.",
      "note": "CHK-D-025/026/027 audit only the anchoring the site itself provides for that corroboration, not corroboration itself."
    },
    { "id": "LIM-02", "mechanism": "D", "reason": "Detecting a same-name collision with an unrelated entity requires a corpus of other entities.", "note": "CHK-D-027 covers only self-consistency, the site-side half." },
    { "id": "LIM-03", "mechanism": "B", "reason": "Live-querying a generative engine would break determinism, the 5-minute budget, and reproducibility (D-006).", "note": "Never claimed either way; this audit measures retrievability and correctness of what the site exposes, not observed citation outcomes." },
    { "id": "LIM-04", "mechanism": "E", "reason": "Field engagement outcomes (bounce, dwell, scroll, conversion, task success) are not observable read-only.", "note": "Reported not_determinable where the gap is itself actionable (D-008)." }
  ],
  "degraded_stages": []
}
```

`limitations[]` is always exactly these four entries, verbatim, on every run — they are
structural, not discovered per-site. `preamble.access_blocked_for` lists any agent named by
a fired `CHK-D-001`; `preamble.notes` carries the framing sentence from
`composition-rules.md` §2 when that applies.

## Check-ID → title map

The 27 checks' human-readable titles, used to fill `findings[].title` and
`recommendations[]` entries. Kept here, not re-derived at run time, so wording is stable
across runs (needed for D-010's `pass^k` comparability).

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
| CHK-E-023 | Mobile ad density exceeds Better Ads threshold |
| CHK-E-024 | Missing trust signals |

## ID assignment

`findings[].id` is `F-{NNN}`, zero-padded to 3 digits, assigned **after** sorting: severity
`critical` → `high` → `medium` → `low`, then `check_id` ascending within a severity tier.
Assign IDs in that final order, starting at `F-001`. This makes `id` a pure function of
the sorted finding set, not an artifact of analyser invocation order — required for two
independent runs against the same bundle to produce byte-identical reports (D-010's
determinism requirement).

## What never appears in `findings[]`

- Any envelope with `state` other than `present`.
- `CHK-E-024`, regardless of state (`recommendation_only: true` always routes it to
  `recommendations[]`).
- Any check merged into another as a `consequences[]` entry under
  `composition-rules.md` §1 — it appears there, nested, not as a sibling top-level finding.

## `summary` counting rule

Count only `findings[]` entries by their own `severity` — a merged finding's
`consequences[]` are not separately counted, and `recommendations[]`/`limitations[]` never
contribute to `summary` at all. `total_findings` is the length of `findings[]`.
