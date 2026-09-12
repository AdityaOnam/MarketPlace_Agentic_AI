---
name: entity-identity-audit
description: Audit a website's entity identity signals — the explicit definitions, structured-data declarations, canonical links, freshness dates, identity anchors, and self-consistency of attributes that allow AI systems to correctly identify, distinguish, and corroborate a brand. Use as the mechanism-D analysis stage of a brand AI-readiness audit, after the evidence bundle has been collected by site-evidence-collector. This skill is the only analyser that reads the anchors section (the sole off-site evidence in the bundle). It deliberately cannot check actual cross-web corroboration or name collisions with other entities — see Declared Limitations below.
license: Apache-2.0
allowed-tools: []
---

# Entity Identity Audit

Mechanism D of the brief: *agreement across the web matters.* A fact repeated consistently
across many independent, easily-found sources is believed and repeated. A claim in only
one spot is fragile. When several things share a name, a system mixes them up unless
something clearly distinguishes one. How a brand is described across the wider web — not
just its own pages — shapes what assistants say.

**This skill declares no tools and makes no network requests.** It is a pure function from
an evidence bundle to findings. All fetching — including the bounded off-site HEAD checks
on declared anchor URLs — happened in `site-evidence-collector`.

## When to use

Invoked by `audit-orchestrator` with an evidence bundle. Handles thirteen checks in the
entity-identity concern: explicit entity definition (CHK-D-006), Organization JSON-LD
completeness (CHK-D-007), canonical URL hygiene (CHK-D-008), date freshness on
time-sensitive pages (CHK-D-012), declared identity anchors (CHK-D-025), anchor
reachability (CHK-D-026), identity-attribute self-consistency (CHK-D-027), and six
archetype-specific structured-data/feed checks (CHK-D-029–D-034).

## Inputs

Two sections of the evidence bundle:

| Section | Fields used |
| --- | --- |
| `pages[]` | `raw_html`, `main_text`, `page_type`, `structured_data`, `canonical`, `dates`, `outbound_profile_links`, `contact_signals`, `headings`, `url`, `status` |
| `anchors` | `status`, `declared[]`, `results[]` (the only off-site evidence in the bundle) |

Reads `pages` and `anchors`. Reads nothing else.

## Output

Finding envelopes for thirteen checks in the standard format defined in
`docs/ARCHITECTURE.md §4.2`. Checks emit an envelope even when clean (`state:
"absent"`) so the negative-control evaluation can distinguish "checked and clean" from
"never ran". CHK-D-029–D-034 are mutually archetype-gated: only the check matching the
site vertical evaluates, and schema absence is always recommendation-only.

## Procedure

1. **Gate on evidence.** Before evaluating any check, inspect the status of the bundle
   sections it needs:
   - If `pages.status != "ok"` (or a specific page's `status != "ok"`), that page is
     excluded from all checks. If no pages are available, emit all page-dependent checks
     as `not_determinable` with `pages.reason`.
   - If `anchors.status != "ok"`, emit CHK-D-026 as `not_determinable` with
     `anchors.reason`.
   - Never infer from absent or partial evidence.

2. **Classify pages as evergreen vs. time-sensitive (required for CHK-D-012).**
   The bundle does not carry a temporal-sensitivity label; this skill derives one per page
   from the available signals. A page is classified **time-sensitive** if *any two* of the
   following hold:
   - `page_type` ∈ `{"article", "documentation", "faq"}` **and** the URL contains a year
     pattern (`/YYYY/`, `?year=YYYY`, etc.)
   - `dates.meta_published` or `dates.visible_dates` is non-empty
   - The first 200 words of `main_text` contain ≥3 past-tense verbs or temporal adverbs
     ("announced", "released", "last week", "yesterday", "in Q1")
   A page is **evergreen** otherwise. CHK-D-012 must never fire on evergreen pages.

3. **Evaluate the thirteen checks** (D-006–D-027 detail is in `references/checks.md`):
   - CHK-D-006 — Explicit entity definition in opening text
   - CHK-D-007 — Organization/Person JSON-LD completeness
   - CHK-D-008 — Canonical URL hygiene
   - CHK-D-012 — Date signal on time-sensitive pages
   - CHK-D-025 — Declared identity anchors exist
   - CHK-D-026 — Declared anchors resolve (reads `anchors` section)
   - CHK-D-027 — Identity attributes self-consistent across pages
   - CHK-D-029 — Product/Offer data on ecommerce product pages
   - CHK-D-030 — SoftwareApplication/Offer data on SaaS home or pricing pages
   - CHK-D-031 — Event/ItemList/JobPosting data on marketplace listing pages
   - CHK-D-032 — Complete NewsArticle data and RSS/Atom discovery for news sites
   - CHK-D-033 — Person data, RSS/Atom discovery, and byline consistency for personal sites
   - CHK-D-034 — SoftwareSourceCode/DataCatalog data for reference/institutional archives

4. **Apply false-positive guards** before emitting any finding. See the check-level
   guards in `references/checks.md`. Do not emit a finding you cannot suppress correctly.

5. **Emit** envelopes for all applicable checks. `absent` and `not_applicable` are emitted,
   not dropped.

## Executable checks

`scripts/entity_identity_checks.py` implements all thirteen checks plus the
`classify_time_sensitivity()` function SKILL.md step 2 describes —
`evaluate(bundle) -> list[envelope]`. Legal-entity-suffix normalization (Ltd/Limited/
LLC/Inc/Corp/GmbH/etc.) is implemented for CHK-D-027's false-positive guard, not just
described.

## Checks at a glance

| Check | Reads | Evidence strength | Severity | FP guard |
| --- | --- | --- | --- | --- |
| CHK-D-006 | `pages` (home, about) | CORRELATIONAL | medium | Suppress if title has clear category, or CHK-D-007 present |
| CHK-D-007 | `pages` structured_data | THEORETICAL/PRACTITIONER | medium | Suppress on personal/hobby archetypes |
| CHK-D-008 | `pages` canonical | NORMATIVE; CAUSAL with sampled duplicate URL variants | medium | Pass if self-referential or valid pagination canonical |
| CHK-D-012 | `pages` dates + page_type + text | THEORETICAL | low | NEVER raise on evergreen; suppress if Last-Modified header present |
| CHK-D-025 | homepage/shared chrome + linked about/contact sameAs and profile links | CORRELATIONAL | medium | Suppress on personal/hobby/portfolio archetype |
| CHK-D-026 | `anchors` results | HARD-MECHANICAL | high/medium | 401/403/429 = bot-blocked = not_determinable, never a finding |
| CHK-D-027 | homepage/shared footer + linked about/contact identity fields | THEORETICAL | medium/low | Suppress pure formatting differences (punctuation, "Ltd" vs "Limited") |
| CHK-D-029 | ecommerce product pages + JSON-LD | NORMATIVE/PRACTITIONER | recommendation-only | Applies only to ecommerce; requires complete Product/Offer data |
| CHK-D-030 | SaaS home/pricing pages + JSON-LD | NORMATIVE/PRACTITIONER | recommendation-only | Applies only to saas_marketing |
| CHK-D-031 | marketplace listing pages + JSON-LD | NORMATIVE/PRACTITIONER | recommendation-only | Applies only to marketplace |
| CHK-D-032 | news article JSON-LD + head feed links | NORMATIVE/PRACTITIONER | recommendation-only | Applies only to news_editorial; requires provenance fields and feed discovery |
| CHK-D-033 | Person/article JSON-LD + head feed links | NORMATIVE/PRACTITIONER | recommendation-only | Applies only to personal-family sites; compares sampled article authors |
| CHK-D-034 | reference/institutional archive pages + JSON-LD | NORMATIVE/PRACTITIONER | recommendation-only | Runs only when code/data archive evidence is present |

Full per-check evidence strings, severity rules, FP guards, not-determinable paths, and
suggested actions: [`references/checks.md`](references/checks.md).

## Declared limitations

Two things that mechanism D names as important but that this skill deliberately cannot
check:

**LIM-01 — Actual cross-web corroboration.** Whether other sites agree with this brand's
own facts requires a search or web-scale index API. No free, deterministic, rate-safe
source exists. CHK-D-025/026/027 audit only *the anchoring the site itself provides* for
that corroboration; they do not measure whether corroboration has actually occurred.

**LIM-02 — Name-collision detection.** Detecting whether the brand name is confused with
a same-named entity elsewhere requires a corpus of other entities. CHK-D-027 covers the
site-side half (self-consistency) but cannot detect external collision.

Both limitations are surfaced by the orchestrator in the report's `limitations[]` array
so the reader understands what was and was not measured. They are never omitted silently.

## False-positive discipline

The three highest false-positive risks in this skill:

1. **CHK-D-012 on evergreen pages.** The time-sensitivity classification exists precisely
   to prevent this. When classification is ambiguous, bias toward evergreen (i.e., stay
   silent) rather than toward time-sensitive.

2. **CHK-D-026 treating bot-blocks as broken anchors.** HTTP 401, 403, and 429 mean
   the server rejected the HEAD request, not that the resource does not exist. The bundle
   encodes this as `resolved: null` (distinct from `false`). Always check for `null` before
   emitting a finding.

3. **CHK-D-027 flagging legitimate name variants.** "Example Ltd" vs "Example Limited" is
   not a conflict. The guard is: suppress unless the name roots diverge after stripping
   punctuation, case, and common legal-entity suffixes (Ltd/Limited/LLC/Inc/Corp/GmbH).
