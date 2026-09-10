# Entity Identity Audit — per-check reference

Full detail for each of the seven checks owned by `entity-identity-audit`. For the
procedure summary, inputs, and false-positive discipline overview see the parent
[`SKILL.md`](../SKILL.md). Evidence strings, severity rules, FP guards, and suggested
actions below are copied directly from `docs/research/EVIDENCE-LEDGER.md` — they are not
re-derived here.

---

## CHK-D-006 — Missing explicit entity definition

**Mechanism:** D — A brand that does not explicitly name its category and function in
opening text cannot be correctly identified from that page alone. AI systems building
answers from fetched pages extract facts stated clearly; implied identity is missed.

**Evidence strength:** CORRELATIONAL  
**Severity ceiling:** medium

**Observation:** Inspect the first 300 words of `main_text` on pages where
`page_type ∈ {"home", "about"}`. Check whether a sentence exists that names all three:
the organisation (proper noun), its category (what type of entity it is), and its
function (what it does).

**Evidence emitted:**
```
No sentence in the first 300 words of {url} explicitly names the organisation,
its category, and its function.
```

**Severity rule:** medium if the pattern is absent on both home and about pages; low if
absent on one but present on the other.

**FP guard:**
- Suppress if the page `<title>` contains the organisation name plus a clear category
  descriptor (e.g. "Acme Corp — Cloud Storage Solutions").
- Suppress if CHK-D-007 fires with a complete Organization JSON-LD that includes
  `name`, `description`, and `@type` — the structured signal compensates.
- Suppress on `page_type ∉ {"home", "about"}`.
- Gated on commercial/organisational archetypes only. Suppress on `archetype ∈
  {"personal", "hobby"}`.

**Not-determinable:** emit `not_determinable` if `pages.status != "ok"` or if the
relevant page's `extraction_ok` is false (JS-only rendering gap; CHK-D-003 likely fired).

**Suggested action:** Add a clear declarative sentence in the first paragraph of the
homepage or about page naming the organisation, its category, and what it specifically
does. Example pattern: "[Name] is a [category] that [function]." Priority: medium.

**Runtime:** low (static text scan).

---

## CHK-D-007 — Missing or incomplete Organization JSON-LD

**Mechanism:** D — Organization structured data gives AI systems an unambiguous,
machine-readable signal of what the entity is. Absence means the entity can only be
identified from prose, which is harder to extract correctly and more easily confused with
same-named entities.

**Evidence strength:** THEORETICAL / PRACTITIONER  
**Severity ceiling:** low (was medium; capped since Stage C, 2026-09-04 — see D-022)

**Observation:** Inspect `structured_data.json_ld[]` on the homepage only (the shipped
`check_d007` reads `page_type == "home"` specifically, not `{"home", "about"}`). Look for
an entry with `@type == "Organization"` (or a subtype). If found, check `fields_present`
against the required set the code actually checks: `["name", "url"]`. **The `description`
field and the recommended-field tier (`logo`, `sameAs`, `contactPoint`) described in an
earlier version of this doc were never implemented in `check_d007` — this file previously
drifted from the code; corrected here, not a change in behaviour.**

**Evidence emitted:**
```
No Organization JSON-LD block found.
```
or
```
Found but missing: {sorted(missing_required)}.
```

**Severity rule (Stage C, D-022):** `low` in both firing cases — no block at all, or a
block missing `name`/`url`. **Why capped, not left at medium:** fired on 26 of 34 real
dev/negative-control sites; Web Data Commons Oct 2024 measured only 44.1% of 37.4M domains
carrying *any* structured data at all, so absence is the open web's majority condition, not
a differentiated signal (D-009's base-rate-conditioning rule, enforced in code). Still a
real, directly actionable defect, so it stays in `findings[]` rather than being demoted to
`recommendations[]` the way `CHK-E-021`/`CHK-D-010` were in the same pass.

**FP guard:**
- Suppress on `archetype ∈ {"personal", "hobby", "portfolio"}`.
- A `Person` JSON-LD block with `name` and `url` is acceptable for personal/creator sites;
  do not flag as missing Organization.
- If Organization JSON-LD is injected via JavaScript only and CHK-D-003 fired (JS-render
  gap), emit `not_determinable` — the structured data exists but is invisible to
  non-rendering fetchers.

**Not-determinable:** If `pages.status != "ok"` or `extraction_ok` is false on all
home/about pages.

**Suggested action:** Add an `@type: Organization` JSON-LD block to the homepage
(or `<head>` on every page) with at minimum `name`, `url`, and `description`. Add `logo`
(as `ImageObject`), `sameAs` (identity anchors), and `contactPoint` where applicable.
Ensure it is present in the raw HTML, not injected after JS load. Priority: medium.

**Runtime:** low (static structured-data scan).

---

## CHK-D-008 — Missing or cross-domain canonical URL

**Mechanism:** B — A missing `rel=canonical` or one pointing to a different domain
attributes content to the wrong origin, allowing scrapers and AI systems to attribute
the page's facts to another site, diluting or misdirecting citations.

**Evidence strength:** CAUSAL  
**Severity ceiling:** medium (causal, but the harm is attribution dilution, not a hard
block)

**Observation:** Inspect `canonical` on each fetched page (3–5 pages across `pages[]`).
Check `canonical.href` for presence, self-referentiality (`canonical.self_referential`),
and cross-domain status (`canonical.cross_domain`).

**Evidence emitted:**
```
Page {url}: no rel=canonical found.
```
or
```
Page {url}: rel=canonical points to {canonical.href} on a different domain
({canonical.cross_domain}).
```

**Severity rule:**
- Missing canonical on ≥2 pages: medium
- Cross-domain canonical (points off-site): medium per affected page
- Missing on exactly 1 page: low

**FP guard:**
- Pass if `canonical.self_referential == true` — this is the correct pattern.
- Pass if the cross-domain canonical is a valid alternate-domain consolidation for the
  same brand (e.g., www redirects to non-www and canonical matches). Check whether the
  canonical target host is in the same redirect chain in `site.redirect_chain`.
- Pass on pagination canonicals that point to the first page in a series — standard
  SEO practice.

**Not-determinable:** If the page's redirect chain is too deep to resolve or the
`pages.status` for that page is not `ok`.

**Suggested action:** Add a consistent self-referential `<link rel="canonical"
href="{page_url}">` in the `<head>` of every page. If a cross-domain canonical is
intentional, verify it points to the brand's own authoritative domain. Priority: medium.

**Runtime:** low (static HTML parse).

---

## CHK-D-012 — Missing date signal on time-sensitive pages

**Mechanism:** D — AI systems use publication and modification dates to assess
content freshness and to decide whether to cite a page for time-sensitive facts.
A time-sensitive page with no detectable date appears stale or undated, reducing its
reliability signal.

**Evidence strength:** THEORETICAL  
**Severity ceiling:** low

**Observation:** For each page classified as **time-sensitive** by the procedure in
`SKILL.md §2`, inspect `dates.meta_published`, `dates.meta_modified`,
`dates.visible_dates`, and `headers.last-modified`. A page passes if any one of these
is non-null and plausible (a date within the last 5 years; future dates are suspicious
and treated as absent).

**Evidence emitted:**
```
Page {url} (classified time-sensitive: {reason}) has no detectable publication date
in body, meta tags, or Last-Modified header.
```

**Severity rule:** low (THEORETICAL evidence strength cap; the harm is reduced
freshness signal, not a hard block).

**FP guard:**
- **NEVER raise on evergreen pages.** The time-sensitivity classification (step 2 of
  the SKILL.md procedure) is the primary guard. When in doubt, classify as evergreen.
- Suppress if a valid `Last-Modified` HTTP header is present (recorded in
  `headers.last-modified`), even if no visible date exists — the header serves the same
  freshness signal for crawlers.
- Suppress on `page_type ∈ {"contact", "legal", "pricing", "login"}` unconditionally.

**Not-determinable:** If the page type is genuinely ambiguous after applying the
classification heuristics, emit `not_determinable` with the note "page temporal
sensitivity could not be determined" rather than guessing.

**Suggested action:** Add a visible publication date or `article:published_time` meta
tag to article, documentation, FAQ, and news pages. Update it on meaningful revisions.
Include `datePublished` and `dateModified` in any JSON-LD block for the page. Priority: low.

**Runtime:** low (static date field inspection).

---

## CHK-D-025 — No declared identity anchors

**Mechanism:** D — `sameAs` links and outbound profile links are the mechanism by which
a site tells AI systems "these external profiles describe the same entity." Without any
declared anchors, the brand cannot participate in cross-web corroboration — there is
nothing for an AI to match against external sources.

**Evidence strength:** CORRELATIONAL  
**Severity ceiling:** medium

**Observation:** On pages where `page_type ∈ {"home", "about"}`, inspect:
- `structured_data.json_ld[].fields_present` for `"sameAs"` on any Organization/Person block
- `outbound_profile_links[]` (footer or header links pointing to external profile hosts:
  LinkedIn, GitHub, Wikipedia, Wikidata, Crunchbase, industry registries, official social
  accounts)

Any one resolvable anchor (either type) is sufficient to pass.

**Evidence emitted:**
```
No sameAs declarations or outbound identity-profile links found on the homepage or
about page. The site provides no declared anchors for cross-web identity corroboration.
```

**Severity rule:** medium if zero anchors of either type are found on both home and
about pages.

**FP guard:**
- Suppress on `archetype ∈ {"personal", "hobby", "portfolio"}` — for individuals,
  declared anchors may be intentionally absent for privacy.
- Any one resolvable anchor — even a single outbound profile link in the footer — passes
  the check. This is a low bar deliberately: the check addresses total absence, not
  coverage.

**Not-determinable:** If both home and about pages are JS-only and CHK-D-003 fired
(structured data and outbound links would be invisible to the static fetch).

**Suggested action:** Declare identity anchors: add a `sameAs` array to the
Organization JSON-LD block pointing at authoritative external profiles (public knowledge
base entry, official social accounts, industry or company registry, professional body
profile). Also include the profile URLs as plain links in the footer or about page for
crawlers that do not execute JavaScript. Priority: medium.

**Runtime:** very-low (static structured-data and link scan).

---

## CHK-D-026 — Declared identity anchors do not resolve

**Mechanism:** D — A `sameAs` link or profile anchor that returns 404 or 410 means the
brand once had an external identity anchor that is now broken. This actively misleads AI
systems: they follow the declared link, find nothing, and the disambiguation chain fails.

**Evidence strength:** HARD-MECHANICAL  
**Severity ceiling:** high

**Observation:** Reads the `anchors` section of the bundle — the only off-site evidence
in the bundle. Inspect `anchors.results[]`. For each entry:
- `resolved: true` → passes
- `resolved: false` → broken anchor (404, 410, or similar definitive failure)
- `resolved: null` → bot-blocked (401, 403, 429) → **not-determinable, never a finding**

**Evidence emitted:**
```
{N} of {M} declared identity anchors did not resolve (statuses: {list_of_statuses},
URLs: {list_of_urls}).
```

**Severity rule:**
- All anchors fail to resolve: high
- Some anchors fail, others resolve: medium
- All anchors resolve: `absent` (clean)
- Requires CHK-D-025 to have found at least one declared anchor; if no anchors exist,
  CHK-D-026 emits `not_applicable`.

**FP guard:**
- **401, 403, 429 → `not_determinable` per anchor, never a finding.** The bundle
  encodes this as `resolved: null`. The check must test `result.resolved === false`,
  not `result.resolved != true`.
- The bundle uses `note: "bot_blocked_not_broken"` on 401/403/429 results; surface this
  note in the `not_determinable` evidence string.
- A single failing anchor when others resolve is medium, not high.

**Not-determinable:** If `anchors.status != "ok"` (off-site anchor check was abandoned
due to budget exhaustion or network failure). Also `not_determinable` per-anchor when
`resolved: null`.

**Suggested action:** Repair or remove dead anchor URLs so every declared profile
resolves. If a social or knowledge-base profile was deleted, update or remove the `sameAs`
entry and the footer link. Priority: high (if all anchors fail) / medium (if some fail).

**Runtime:** low (reads pre-computed HEAD results from `anchors`; no new network calls).

---

## CHK-D-027 — Identity attributes self-inconsistent across pages

**Mechanism:** D — When the same organisation's name, legal name, phone, or postal
address appears in different forms across its own pages, AI systems cannot confidently
pick the canonical form. Self-inconsistency actively degrades the entity-resolution
signal, making it easier to confuse this brand with another.

**Evidence strength:** THEORETICAL  
**Severity ceiling:** medium (name or legal-name conflict) / low (other attribute variance)

**Observation:** Compare across all fetched pages the following fields from
`contact_signals` and `structured_data.json_ld[]`:
- `org_name` / JSON-LD `name`
- JSON-LD `legalName` (if present)
- `phone`
- `postal_address`

Collect all distinct non-null values for each attribute. Requires ≥2 observed instances
of an attribute to emit a finding.

**Evidence emitted:**
```
Organisation name appears as {N} distinct variants across {M} pages:
{variant_list}. A consistent name is required for accurate entity resolution.
```
or, for address/phone:
```
{attribute} appears in {N} distinct forms across {M} pages: {variant_list}.
```

**Severity rule:**
- Name or `legalName` conflict (after normalization): medium
- Phone or postal-address conflict only: low
- No conflict found: `absent`

**FP guard (critical — most FP risk in this check):**
- **Suppress pure formatting differences:** strip whitespace, punctuation, and common
  legal-entity suffixes before comparing. "Example Ltd" == "Example Limited" ==
  "Example, Ltd." — these are not conflicts.
- Legal suffix normalization: Ltd / Limited / LLC / L.L.C. / Inc / Incorporated /
  Corp / Corporation / GmbH / S.A. / B.V. are equivalent.
- International phone-number prefix differences (+1 vs 001 vs (country code)) are not
  conflicts.
- Suppress if fewer than 2 instances of the attribute are found (cannot compare).

**Not-determinable:** If fewer than 2 pages were successfully fetched, or if
`extraction_ok` is false for all relevant pages.

**Suggested action:** State one canonical form of the organisation name, legal name,
phone, and postal address, and use it identically in every location: JSON-LD blocks,
footer, contact page, and any schema.org markup. Generate them from a single source of
truth (e.g., a CMS global variable) to prevent drift. Priority: medium (name conflict) /
low (contact detail variance).

**Runtime:** low (static field comparison across pages).
