# 06 — The audit report: output-design Q&A

The report is what the rubric's *output design* line grades: *"a clear, structured,
actionable report (evidence + severity + prioritized actions) a non-expert could act on."*

Source of truth: `skills/audit-orchestrator/references/report-schema.md`.

---

### Q1. What is the required floor, per the contest?

**A.** Five things, and extra fields are explicitly allowed:

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": { "total_findings": 6, "critical": 1, "high": 2, "medium": 3 },
  "findings": [{
    "id": "F-001",
    "title": "...",
    "severity": "high",
    "evidence": "...",
    "suggested_action": { "summary": "...", "priority": "high" }
  }]
}
```

Per finding: `id`, `title`, `severity`, `evidence`, `suggested_action`. Per report: `site`,
`audited_at`, and a counts-by-severity `summary`.

### Q2. What does our report add beyond the floor?

**A.** `schema_version`, `preamble`, `recommendations[]`, `checks_passed[]`, `strengths[]`,
`limitations[]`, `degraded_stages[]`, `top_priorities[]`, `meta_evaluation`. Per finding:
`check_id`, `evidence_strength`, `locus`, `instances[]`, `occurrences`, `suppressed_by`.

### Q3. What goes in `preamble`?

**A.** `access_state`, `access_blocked_for[]`, `access_partial_for[]`, `notes[]`,
`archetype`, `recommendations_scoped_to`.

### Q4. What two lines does `preamble.notes` always contain?

**A.**
1. **The static-HTML premise** — the grading sandbox has no headless browser, so a check whose
   only evidence is rendered geometry reports `not_determinable`, **not "no defect found."** A
   reader needs that distinction stated in the report, not inferred from what is absent.
2. **The archetype effect** — the label is not decoration; it changes which checks run and how
   actions are worded. The note names the archetype and says in one sentence what it meant for
   *this* audit.

A third line is prepended when `CHK-D-001` is present, stating that the content findings
describe content the blocked agents cannot currently reach.

### Q5. Why does `summary` count only `findings[]`?

**A.** So proactive advice cannot inflate the severity counts. Recommendations and limitations
are not defects and are not counted there — that is D-012's whole purpose.

### Q6. What is the difference between `checks_passed[]` and `strengths[]`?

**A.** `checks_passed[]` lists check IDs that ran to a clean `absent` — what the audit
**verified**. `strengths[]` records mechanically verified **positive signals** that are not
the inverse of any defect check and do not affect the score. A check that produced only
`not_determinable` or `not_applicable` appears in neither: it was not measured.

### Q7. Which strength detectors exist?

**A.** A sitemap with a declared last-modified date under 90 days old and >5 represented page
templates; an RSS/Atom `<link rel="alternate">` in the collected head; complete Person or
Organization JSON-LD with `name` and `url`; `canonical_consistency` (self-referential
same-domain canonicals on **all** of ≥3 fetched pages) or `canonical_majority` (≥2/3 but not
all, with the ratio carried in the evidence string); a well-formed robots.txt permitting at
least one retrieval or hybrid crawler at root; and an existing Markdown representation.

### Q8. Why are `canonical_consistency` and `canonical_majority` named differently?

**A.** Deliberately — so the strength/recommendation contradiction filter does not suppress
legitimate `CHK-D-008` recommendations on the minority of pages that still lack a
self-referential canonical. A shared name would have let a partial strength silence a real
finding.

### Q9. How does `top_priorities[]` rank items?

**A.** Three classes: (1) verified retrieval-access / static-content availability failures
(D-001, D-002, D-003); (2) directly evidenced identity, canonical and detail-data defects
(D-006–D-008, D-012, D-025–D-034); (3) page-local heuristics and generic structure. **Only
class-1 and class-2 items lead the report.** A report with nothing in those classes returns
an **empty array** rather than promoting a heuristic to fill three slots. Within a class the
tie-break is evidence strength → severity → sampled coverage → check ID — all deterministic,
all rooted in fields the check already emitted, and each entry names its class as its
`reason` so the ordering is auditable.

### Q10. Why does `top_priorities[]` add nothing new?

**A.** Because it is a *view*, not a second judgement. It draws items by ID from the existing
lists and rewrites no severities. A prioritiser that could invent items would be a second,
unaudited analyser.

### Q11. What does `access_state` distinguish?

**A.** `ok` — at least one sampled page fetched. `partial_block` — robots.txt reachable but
zero pages fetched, i.e. a perimeter/WAF layer. `full_block` — nothing reachable at all.

### Q12. Why doesn't a blocked site produce a critical finding about the block?

**A.** The officials placed bot-blocked sites out of scope for further audit investment. So
the access-state preamble field is the entire signal: the report is honest that the site was
unreachable, and the DOM/link-dependent checks are **excluded from `checks_passed[]`** so no
reader can mistake "we did not measure these" for "these passed cleanly." A
`BUDGET-degraded_stages` limitation is always appended when access is anything but `ok`.

### Q13. Why are titles taken from a fixed table rather than phrased per run?

**A.** A title generated fresh each run would break the byte-identical comparability that
repeated-run stability measurement needs. All 32 titles live in the check-ID → title map in
`report-schema.md`, mirrored by `CHECK_TITLES` in code.

### Q14. Why do `recommendations[]` entries carry `locus` and `severity`?

**A.** Added 2026-09-09: without them, the evaluation's matching rule (same check, same
locus) has no locus to match against for any of the five recommendation-only checks. D-012's
schema is explicitly "a floor, not a ceiling."

### Q15. Why does a recommendation have both a top-level `summary` and a nested one?

**A.** They carry the same string. The top-level field exists so a consumer walking
`recommendations[]` for a headline can read it without descending into `suggested_action`. A
recommendation whose source envelope produced no action is **dropped** before shipping and
logged as an `empty_recommendation` warning — the report never carries an empty summary.

### Q16. Why is there no `consequences` field?

**A.** An earlier design collapsed multi-check clusters into one root finding carrying a
`consequences` array. The one cluster it was built for — `CHK-D-003` + `D-004` + `D-005` +
`E-019` co-occurring — was **proven unreachable**: D-003 and E-019 both require the
homepage's main text <50 words, while D-005 requires >500 on the same page. Removed as D-016.
The one real relationship left is expressed entirely through `state: "suppressed"` /
`suppressed_by`.

### Q17. What do the `limitations[]` entries look like?

**A.** Two shapes. A declared limitation carries `id`, `lim_id` (LIM-01…05), `title`,
`description`, `affected_checks[]`. A budget-constrained one carries
`lim_id: "BUDGET-<stage>"` and names the stage, the elapsed vs budgeted seconds, and the
checks that could not be evaluated — with the sentence *"Results for these checks read as
'could not measure', not as 'no defect found'."*

### Q18. Why is LIM-05 different in kind from LIM-01…04?

**A.** LIM-01 through 04 are **capability gaps**. LIM-05 is a **declared policy refusal** —
we could recommend `llms.txt` and choose not to, on measured evidence. Stated per D-014 so it
reads as a deliberate position rather than an omission.

### Q19. What are the nine meta-evaluation checks?

**A.** `summary_reconciles`, `severity_counts_reconcile`, `finding_complete`,
`no_duplicate_findings`, `known_check_id`, `prohibited_recommendation`,
`contradicted_by_strength`, `empty_recommendation`, `checks_passed_reconcile`,
`limitations_present`.

### Q20. Which of them are hard-drop gates and what do they drop?

**A.** Four. `prohibited_recommendation` (removes an action containing banned advice or a
banned statistic, logging `gate_dropped_action`); `contradicted_by_strength` (removes a
recommendation whose check is already covered by an active strength detector);
`empty_recommendation` (removes one whose summaries are both empty);
`checks_passed_reconcile` (drops a pass entry for a check that also appears in findings or
recommendations, so a check ID can never contradict itself). **Everything else is a warning,
never a silent correction.**

### Q21. Does the meta-evaluation ever overturn a finding?

**A.** No. It explicitly *"does not re-judge any finding — the analysers own that, and this
step has no authority to overturn them."* It checks internal coherence and prohibited wording
only.

### Q22. What does a real finding look like?

**A.** From the evaluation corpus, unedited:

```json
{
  "id": "F-001",
  "check_id": "CHK-D-001",
  "title": "Retrieval-time AI crawler blocked at root",
  "severity": "critical",
  "evidence_strength": "HARD-MECHANICAL",
  "state": "present",
  "locus": { "url": null, "selector": null },
  "evidence": "robots.txt line 120: Disallow: / applies to Applebot (retrieval-time AI crawler). robots.txt line 180: Disallow: / applies to ChatGPT-User …",
  "suggested_action": {
    "summary": "Narrow the Disallow rule to the paths that actually need protection rather than the site root for: Applebot, ChatGPT-User, Claude-SearchBot, Claude-User, Claude-Web, Meta-ExternalFetcher, OAI-SearchBot, Perplexity-User, PerplexityBot.",
    "priority": "critical"
  },
  "suppressed_by": []
}
```

Note what the action does: it names the exact agents and the exact line, and it recommends
**narrowing** the rule rather than removing the file. That is what "the fix maps to the
finding" means in practice.

### Q23. What does a recommendation look like?

```json
{
  "id": "R-001",
  "check_id": "CHK-E-021",
  "title": "Images/iframes missing dimensions (layout-shift cause)",
  "rationale": "714 image(s)/iframe(s) lack explicit width/height or aspect-ratio, so content reflows during load.",
  "suggested_action": {
    "summary": "Add width/height attributes or CSS aspect-ratio to reserve layout space before the resource loads. (Proactive — not a confirmed defect.)",
    "priority": "low"
  }
}
```

The parenthetical *"(Proactive — not a confirmed defect.)"* is not decoration — it is the
visible half of the recommendation-only rule.
