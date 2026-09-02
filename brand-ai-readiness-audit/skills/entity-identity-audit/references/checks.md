# Check reference — entity-identity-audit

Full per-check detail for the seven checks this skill owns. Sourced directly from
`docs/research/EVIDENCE-LEDGER.md`; if the two ever disagree, the ledger wins and this file
is stale.

---

## CHK-D-006 — Missing explicit entity definition

- **Mechanism**: D — without a plain declarative sentence naming what the organisation is,
  neither a machine reader nor a disambiguation system has an anchor fact to extract.
- **Strength**: `CORRELATIONAL`. Ceiling: `medium`.
- **Reads**: `pages[].main_text`, home and about pages, first 300 words.
- **Severity rule**: `medium` if no sentence in the first 300 words names the organisation,
  its category, and its function together.
- **Evidence**: `No sentence in the first 300 words explicitly names the organisation, its
  category, and its function.`
- **FP guard**: exclude if the page `<title>` already carries a clear category, or if
  `CHK-D-007` is present (structured data already states it machine-readably). Gate to
  commercial/organisational archetypes — a personal site has no equivalent obligation.
- **Not-determinable**: `pages.status != "ok"` for a JS-only page → `not_determinable`.
- **Action**: add one clear declarative sentence near the top of the homepage or about page
  naming the organisation, its category, and its function in plain text.
- **Runtime**: low.

## CHK-D-007 — Missing or incomplete Organization JSON-LD

- **Mechanism**: D — structured data is the machine-parseable form of the same identity
  claim; its absence forces every consumer to infer identity from prose.
- **Strength**: `THEORETICAL/PRACTITIONER`. Ceiling: `medium`.
- **Reads**: `pages[].structured_data.json_ld[]` on the homepage, filtering for
  `type == "Organization"`.
- **Severity rule**: `medium` if no `Organization` block exists, or one exists but is
  missing required fields (name, url; `sameAs` is separately graded under `CHK-D-025`).
- **Evidence**: `No Organization JSON-LD block found.` or `Found but missing: {fields}.`
- **FP guard**: exclude personal/hobby archetypes, which have no organisation to declare.
- **Not-determinable**: JSON-LD injected only via client-side JS and `rendered` was not
  consulted by this skill (it doesn't read `rendered[]` — a JS-injected block is reported
  `not_determinable`, not absent, if `pages[].extraction_ok` flags the page as JS-dependent).
- **Action**: add or complete an `Organization` JSON-LD block with at minimum `name` and
  `url`.
- **Runtime**: low.

## CHK-D-008 — Missing or cross-domain canonical

- **Mechanism**: B — a page with no canonical, or one pointing off-domain, risks having its
  content attributed to the wrong URL or the wrong site entirely, which is itself an
  identity-fragmentation problem: the same fact now has two possible homes.
- **Strength**: `CAUSAL`. Ceiling: `medium`.
- **Reads**: `pages[].canonical`, 3–5 sampled pages.
- **Severity rule**: `medium` if `canonical` is absent, or `cross_domain == true` without a
  clear syndication reason.
- **Evidence**: `Page {URL}: no rel=canonical found.` or `canonical points to
  {other_domain}.`
- **FP guard**: pass if `self_referential == true`, or if the cross-domain canonical is
  valid pagination/syndication (e.g. an AMP page correctly canonicalising to its full
  version).
- **Not-determinable**: redirect chain too deep to resolve a stable URL → `not_determinable`.
- **Action**: add a consistent, self-referential `rel=canonical` to every indexable page.
- **Runtime**: low.

## CHK-D-012 — Missing date signal on time-sensitive content

- **Mechanism**: D — a fact whose currency can't be judged (is this offer, event, or claim
  still true?) is one a cautious system should hesitate to repeat, and one a human can't
  trust either.
- **Strength**: `THEORETICAL`. Ceiling: `low`.
- **Reads**: `pages[].dates`, plus this skill's own `TIME-SENSITIVE`/`EVERGREEN`
  classification from `SKILL.md` step 2 (page_type, URL, `main_text` tense cues) — the
  bundle does not carry this label directly (`docs/BUNDLE-SCHEMA.md` Caveat 2).
- **Severity rule**: `low` if a page classified `TIME-SENSITIVE` has no
  `dates.meta_published`, no `dates.visible_dates`, and no usable
  `headers['last-modified']`.
- **Evidence**: `Page {URL} (time-sensitive) has no detectable publication date.`
- **FP guard**: **never raise on a page classified `EVERGREEN`.** Suppress if a valid
  `Last-Modified` header is present even without a visible date.
- **Not-determinable**: page-type genuinely ambiguous between evergreen and time-sensitive
  (no page_type, no URL pattern, no tense cue) → `not_determinable` rather than guessing.
- **Action**: add a visible publication date or an `article:published_time` meta tag to
  every time-sensitive page.
- **Runtime**: low.

## CHK-D-025 — No declared identity anchors

- **Mechanism**: D — without any declared external profile, there is nothing for the wider
  web to corroborate against, and nothing to distinguish this entity from a same-named one.
- **Strength**: `CORRELATIONAL`. Ceiling: `medium`.
- **Reads**: `pages[].structured_data.json_ld[].fields_present` (looking for `sameAs`) and
  `pages[].outbound_profile_links`, home + about, static HTML only.
- **Severity rule**: `medium` if zero anchors are declared across both sources.
- **Evidence**: `No sameAs declarations or outbound identity-profile links found on the
  homepage or about page.`
- **FP guard**: suppress on personal/hobby/portfolio archetype. **Any one anchor that
  resolves in `CHK-D-026` passes this check** regardless of how many were declared.
- **Not-determinable**: both home and about are JS-only and `CHK-D-003` fired (from
  `render-extractability-audit`, read via the orchestrator, not directly) →
  `not_determinable`. If this skill runs standalone without that cross-skill context, treat
  a JS-only page with `extraction_ok == false` as `not_determinable` for this check.
- **Action**: declare identity anchors — add `sameAs` to the Organization JSON-LD pointing
  at the organisation's authoritative external profiles (public knowledge base, official
  social accounts, industry or company registry).
- **Runtime**: very-low.

## CHK-D-026 — Declared anchors that don't resolve

- **Mechanism**: D — a declared anchor that 404s or times out is worse than none: it invites
  a corroboration attempt that fails, actively breaking the disambiguation chain rather than
  simply not offering one.
- **Strength**: `HARD-MECHANICAL`. Ceiling: `high`.
- **Reads**: `anchors.results[]` (bounded HEAD checks already run by the collector: max 8
  URLs, one per host).
- **Severity rule**: `high` if all declared anchors fail to resolve; `medium` if some do.
- **Evidence**: `{N} of {M} declared identity anchors did not resolve (statuses: {list}).`
- **FP guard**: **`resolved: null` (401/403/429) means bot-blocked, not broken — never
  counted as a failure.** Only runs if `CHK-D-025` did not fire (requires ≥1 declared
  anchor to exist).
- **Not-determinable**: per-anchor, on timeout or a 401/403/429 status — reported
  individually, not folded into the failure count.
- **Action**: repair or remove dead anchor URLs so every declared profile actually resolves.
- **Runtime**: low (reads collector output; the network cost was already spent there).

## CHK-D-027 — Self-inconsistent identity attributes

- **Mechanism**: D — an entity that states its own name, address, or phone number
  differently in different places on its own site actively defeats corroboration, since even
  a system that finds all the instances can't tell which is canonical.
- **Strength**: `THEORETICAL`. Ceiling: `medium`.
- **Reads**: organisation name, legal name, phone, and postal address from
  `pages[].structured_data` (JSON-LD), `pages[].contact_signals` (footer), and a dedicated
  contact page, requiring ≥2 observed instances of the same attribute before comparing.
- **Severity rule**: `medium` if organisation name or legal name conflicts across
  instances; `low` if only formatting varies.
- **Evidence**: `Organisation name appears as {variants} across {N} locations.`
- **FP guard**: suppress pure formatting differences — whitespace, punctuation, "Ltd" vs.
  "Limited", international phone-number prefix notation. These are not inconsistencies.
- **Not-determinable**: fewer than 2 instances of the attribute found anywhere on the site
  → `not_determinable` (nothing to compare).
- **Action**: pick one canonical form of the organisation name, legal name, phone number,
  and address, and use it identically everywhere it appears on the site.
- **Runtime**: low.
