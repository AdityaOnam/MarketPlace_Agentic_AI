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
    "access_state": "ok",
    "access_blocked_for": [],
    "access_partial_for": [],
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
  "checks_passed": [
    { "check_id": "CHK-D-001", "title": "Retrieval-time AI crawler blocked at root" },
    { "check_id": "CHK-D-008", "title": "Missing or cross-domain canonical tag" }
  ],
  "strengths": [
    { "id": "S-1", "detector": "sitemap_fresh", "evidence": "Sitemap inventory covers 6 page templates; its latest declared lastmod is 2026-09-01 (19 days old)." }
  ],
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

`preamble.notes` always contains two lines that state what the report is:

1. The static-HTML premise (D-19): the grading sandbox has no headless browser, so a
   check whose only evidence is rendered geometry reports `not_determinable`, not "no
   defect found". A reader needs that distinction stated in the report itself, not
   inferred from what is absent.
2. The archetype effect (D-3): the `archetype` label is not decoration -- it changes
   which checks run and how their actions are worded. This line names the archetype and
   states, in one sentence, what that label meant for THIS audit (personal sites are
   exempted from identity checks; documentation sites have version variants exempted from
   near-duplicate flagging; `unknown` means no vertical-specific handling was applied).
   OFFICIALS-QA §3.3 and Action #6 name archetype-specific interpretation as a rewarded
   differentiator; the note makes that visible.

A robots-blocked-crawler finding (D-001 present) prepends a third line stating that the
content findings describe content the blocked agents cannot currently reach.

`checks_passed[]` (D-18) lists the check IDs that ran to a clean `absent` and produced no
present finding -- what the audit *verified*, not just what it found broken. A check that
produced only `not_determinable` or `not_applicable` envelopes is not listed there: it was
not measured. A recommendation-only check is listed only when its envelope is `absent`;
when it emits a proactive recommendation (`present`), it appears only in
`recommendations[]` and never inflates the scored summary.

`strengths[]` records concise, mechanically verified positive signals and is distinct
from `checks_passed[]`: it does not invert defect checks or affect the score. Each entry
has a sequential `S-N` ID, a stable detector name, and one evidence line. The detectors
are: a sitemap with a declared last-modified date under 90 days old and more than five
represented page templates; an RSS/Atom `<link rel="alternate">` in the collected document
head; complete Person or Organization JSON-LD with `name` and `url`; self-referential,
same-domain canonicals on every successfully fetched sampled page (with at least two
pages); a well-formed robots.txt that permits at least one retrieval or hybrid crawler at
the root; and a Markdown representation already present in `pages[]`. Sitemap freshness
is not inferred when the bundle has no sitemap date, and the Markdown detector never
makes an additional request.

`summary.total_findings` counts only `findings[]` entries. Recommendations and
limitations are not findings and are not counted there.

`preamble.access_state` is a three-value flag introduced by Phase 9 (2026-09-14) so a
reader can distinguish the audit that successfully reached its sample from the audit
that could not. Values:

- **`ok`** — at least one sampled page was fetched with `extraction_ok`; the report's
  findings, strengths, and passed checks describe measurable evidence.
- **`partial_block`** — zero sampled pages were fetched but `robots.txt` was reachable;
  a perimeter/WAF or bot-management layer allows the automated crawler to see
  `robots.txt` but not any real page. The offending host appears in
  `access_partial_for`; `access_blocked_for` is empty.
- **`full_block`** — neither `robots.txt` nor any sampled page could be reached. The
  host appears in `access_blocked_for`; `access_partial_for` is empty.

On either block state the report deliberately does NOT add a new critical finding
about the block itself. OFFICIALS-QA §2.2 places bot-blocked sites out of scope for
further audit investment (Action #10), so the access-state preamble field is the
entire signal we ship: the report is honest that the site was unreachable, and the
DOM/link-dependent checks (E-014, E-015, E-022, D-003, D-009, E-018, E-019, E-021)
are excluded from `checks_passed[]` so no reader can mistake "we did not measure
these" for "these passed cleanly". A `BUDGET-degraded_stages` limitation is always
appended when access is anything other than `ok`.

`preamble.archetype` records the vertical the audit assumed, and
`recommendations_scoped_to` states plainly that every suggested action below was written
for that vertical — the archetype gates which checks ran at all and how each action is
worded, so a reader needs to know which one was assumed. Values: `ecommerce`,
`saas_marketing`, `news_editorial`, `documentation`, `local_business`, `brochure`,
`reference`, `institutional`, `marketplace`, `personal`, `unknown`. `unknown` means the
evidence was insufficient or a near-tie between two archetypes (the collector records
which), and every archetype-conditioned check was suppressed rather than guessed at.

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

### `instances[]` — always present, one entry per origin envelope

Every finding carries an `instances[]` array recording each origin: the per-page locus
and the per-page evidence text (which names elements by count/type -- '3 img with missing
alt', '1 button with no accessible name'). Even a single-page finding gets a one-entry
`instances[]` array so the shape is consistent for downstream consumers.

This is the additive half of D-1 and how D-13 (name the elements) is met inside a
static-HTML audit: the *evidence text* on each instance names the elements at page
granularity. A CSS selector for each element would require the check itself to emit one,
which most checks do not.

### `occurrences` — present when the defect spans ≥2 pages

One site-template defect repeats on every page built from that template. Emitting it once
per page turns a report into a laundry list in which the single worst problem occupies
seventeen slots, which is fatal to the prioritisation the brief actually asks for. When a
defect is found on **2 or more** sampled pages, the orchestrator emits it once:

```json
{
  "id": "F-002",
  "check_id": "CHK-E-022",
  "severity": "medium",
  "evidence": "Site-wide: 17 sampled pages share this defect. missing <main> landmark. Violates structural conventions (WCAG 2.2 SC 1.3.1).",
  "locus": { "url": null, "scope": "site" },
  "occurrences": { "pages": 17, "examples": ["https://…/a", "https://…/b", "https://…/c"] },
  "instances": [
    { "locus": {"url": "https://…/a"}, "evidence": "Page https://…/a: missing <main> landmark…", "severity": "medium" }
  ]
}
```

Severity is the **worst** in the collapsed group, never an average — a defect is as
serious as its worst instance. At a single page, the finding keeps its original `locus`
and `evidence` unchanged; the `instances[]` array still records the origin envelope, but
no `occurrences` block is added. See **D-019** and the D-1 tightening on 2026-09-12.

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
  "summary": "Commercial and news sites gain credibility with visible contact information, organisation name in the footer, HTTPS, and byline dates on articles.",
  "rationale": "Commercial and news sites with visible contact information, HTTPS, and byline dates are easier for users and AI systems to assess as credible.",
  "mechanism": "E",
  "suggested_action": {
    "summary": "Commercial and news sites gain credibility with visible contact information, organisation name in the footer, HTTPS, and byline dates on articles.",
    "priority": "low"
  },
  "locus": {"url": "https://example.com/pricing", "selector": null},
  "severity": "low",
  "route_reason": "single-source rule (D-004): supporting evidence is one unreplicated study."
}
```

`summary` at the top level mirrors `suggested_action.summary`. Both fields carry the same
string; the top-level field exists so consumers walking `recommendations[]` for a headline
can read it without descending into the nested `suggested_action` object. A recommendation
whose source envelope produced no `suggested_action` is dropped before the report ships
and logged as an `empty_recommendation` meta-evaluation warning — the report never
carries a recommendation with an empty `summary`.

---

### Archetype-specific schema recommendations (CHK-D-029–D-034)

Only the check matching `preamble.archetype` evaluates; the other five emit
`not_applicable` and appear in neither the report nor `checks_passed[]`. These checks
never create scored findings. When expected data is absent or incomplete, they create one
ordinary `recommendations[]` entry with the sampled-page locus. When the required data is
present and well formed, they emit `absent` and therefore appear in `checks_passed[]`.

| Check | Archetype | Passing evidence |
| --- | --- | --- |
| CHK-D-029 | `ecommerce` | Complete Product/Offer JSON-LD on sampled product pages |
| CHK-D-030 | `saas_marketing` | SoftwareApplication or priced Offer data on the homepage/pricing page |
| CHK-D-031 | `marketplace` | Complete Event, ItemList, or JobPosting data on a listing page |
| CHK-D-032 | `news_editorial` | NewsArticle `headline`, `datePublished`, `author.name` on sampled articles plus an RSS/Atom head link |
| CHK-D-033 | `personal` family | Named Person data, RSS/Atom head link, and consistent sampled article authorship |
| CHK-D-034 | `reference` / `institutional` | SoftwareSourceCode or DataCatalog data when a code/data archive is detected |

The RSS/Atom detector reads already-collected `raw_html`; it makes no additional request.

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
| CHK-D-029 | Product and offer data for ecommerce pages |
| CHK-D-030 | Software and pricing data for SaaS pages |
| CHK-D-031 | Listing data for marketplace pages |
| CHK-D-032 | Article provenance and feed discovery for news sites |
| CHK-D-033 | Author identity and feed discovery for personal sites |
| CHK-D-034 | Repository or dataset data for code and data archives |
| CHK-E-014 | Machine-detectable accessibility violations |
| CHK-E-015 | Mobile viewport meta missing or restricting user zoom |
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
