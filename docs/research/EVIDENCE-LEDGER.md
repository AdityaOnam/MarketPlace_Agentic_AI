# Evidence ledger

One row per shipped check. This is the audit trail that connects the literature to the
`SKILL.md` files, and the artifact that makes "detection accuracy" and "generalization"
arguable rather than asserted.

**Gate:** a check may not ship until its row is complete *and* at least one supporting
source is `VERIFIED` and has been hand-spot-checked (not merely reported by a research
agent). A row whose only support is `SEARCH-ONLY` is a lead, not a justification.

## Column definitions

| Column | Meaning |
| --- | --- |
| `CHK-ID` | Stable check identifier, `CHK-D-NNN` (discoverability) or `CHK-E-NNN` (engagement) |
| Owning skill | Which marketplace skill runs it |
| Mechanism | Round-2 appendix letter (A-F) + one line on the causal story |
| Sources | Paper IDs (`P-01.03`, `P-06.11`, …) supporting it |
| Evidence strength | CAUSAL / CORRELATIONAL / THEORETICAL — caps the severity ceiling |
| Observation | Exactly what is fetched/parsed, read-only, and the page budget |
| Evidence emitted | The quantitative sentence template that lands in the report |
| Severity rule | Deterministic mapping from measurement to critical/high/medium/low |
| FP guard | The condition under which the check must stay silent |
| Not-determinable | How inability to measure is reported, distinct from absence |
| Suggested action | What to change and how — mechanism-sound, non-expert actionable |
| Runtime | Approximate cost against the <5 min budget |
| Verified by hand | Initials + date of the human spot-check of the cited source |

## Severity ceiling rule

- **Critical:** Reserved for CAUSAL or HARD-MECHANICAL findings that directly block AI retrieval or user access.
- **High:** Allowed for CAUSAL, HARD-MECHANICAL, or well-supported CORRELATIONAL with large effect sizes and normative basis (e.g. Better Ads Standards).
- **Medium:** Ceiling for THEORETICAL/PRACTITIONER OBSERVATION or weak CORRELATIONAL findings. Also for normative issues that don't fully block access.
- **Low:** Appropriate for heuristics, extrapolated findings, and purely correlational checks with high variability.

**Evidence-strength vocabulary** (extends D-004; `NORMATIVE` recorded as D-011):

| Strength | Meaning | Ceiling |
| --- | --- | --- |
| `HARD-MECHANICAL` | Consequence is definitional, not statistical — the crawler is blocked, the content is absent from the response. No effect size needed. | critical |
| `CAUSAL` | Controlled experiment | critical |
| `NORMATIVE` | Violates a published, citable standard (WCAG success criterion, Better Ads Standard). The standard *is* the authority; we are not claiming a measured outcome. | high |
| `CORRELATIONAL` | Measured association at scale, replicated | high |
| `THEORETICAL` / `PRACTITIONER` | Mechanism plausible, outcome not measured | medium |
| Single-study or contested | One unreplicated source, or sources that disagree | low, **or proactive recommendation only** |

**Single-source rule.** A check whose support reduces to one unreplicated study may not be
emitted as a finding at any severity; it ships as a proactive recommendation until a second
independent source is verified. Applied to CHK-E-024.

**ID convention.** IDs are a single global sequence (`CHK-D-001`…`CHK-D-013`,
`CHK-E-014`…`CHK-E-024`, then `CHK-D-025`…`CHK-D-027`); the `D`/`E` letter denotes which
half of the brief the check serves, not a per-half counter. IDs are stable and never
reused — renumbering would invalidate every gold label keyed to them.

---

## Discoverability checks

| CHK-ID | Owning skill | Mechanism | Sources | Evidence strength | Observation | Evidence emitted | Severity rule | FP guard | Not-determinable | Suggested action | Runtime | Verified by hand |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CHK-D-001 | marketplace_auditor | A — blocks retrieval-time AI crawlers from indexing | P-01.03, P-01.12 | HARD-MECHANICAL | robots.txt Disallow on root/homepage for GPTBot, PerplexityBot, etc. (1 URL) | `robots.txt line {N}: Disallow: / applies to {agent} (retrieval-time AI crawler).` | critical | IF only training crawlers blocked, emit CHK-D-002 instead. | `robots.txt is unavailable (HTTP {status})` | Remove or narrow the Disallow rule for {agent}. | very-low | — pending |
| CHK-D-002 | marketplace_auditor | A — blocks training-only crawlers | P-01.03, P-01.12 | CORRELATIONAL (low impact) | robots.txt Disallow on training crawlers (CCBot) when no retrieval block | `robots.txt blocks {agent} (a training-corpus crawler) but permits retrieval-time AI crawlers.` | low (informational) | IF CHK-D-001 fires, suppress. | Same as CHK-D-001 | If future parametric memory coverage matters, consider removing the block. | very-low | — pending |
| CHK-D-003 | marketplace_auditor | C — JS-rendering gap hides content from AI | P-04.08, P-04.02 (P-04.10 = lead only, not load-bearing) | HARD-MECHANICAL | Presence of primary content in raw HTML vs. rendered DOM (shared render pass) | `Homepage: raw HTTP fetch contains {raw} words of main text and {h1_raw} h1; rendered DOM contains {rend} words and {h1_rend} h1.` | **Definitional, not threshold-based:** high if raw HTML lacks an h1 *and* has <50 words of main text while the rendered DOM has ≥200 — the content is absent from what a non-rendering fetch receives, which needs no effect size. medium if h1 present but ≥60% of main text is render-only. low if 20-60% render-only. | Suppress if <20% gap or if noscript >50 words. | `Headless rendering did not complete.` | Implement SSR or SSG. | high (headless) | — pending |
| CHK-D-004 | marketplace_auditor | C — thin main content | P-04.08, P-04.09, P-01.10 | CORRELATIONAL | Word count of extracted main text < 200 (3-5 pages) | `Page {URL}: main-content extraction yielded {count} words after boilerplate removal.` | medium | Suppress on JS-SPAs if CHK-D-003 fired. Condition on archetype (exclude contact/login). | `Content could not be extracted.` | Add substantive, explicitly-stated content. | low | — pending |
| CHK-D-005 | marketplace_auditor | B/C — absent/generic headings hurt chunking | P-01.13, P-01.10, P-07.08 | THEORETICAL | h2/h3 absent on >500w pages, or generic headings (3-5 pages) | `Page {URL}: {words} words of body text with {h_count} descriptive subheadings.` | low | Exclude legal/FAQ/minimal archetypes. | `not_determinable` if extraction fails. | Add descriptive subheadings. | low | — pending |
| CHK-D-006 | marketplace_auditor | D — missing explicit entity definition | P-01.05, P-06.05, P-06.06, P-01.15 | CORRELATIONAL | Missing sentence with org name + category + function in first 300w (home/about) | `No sentence in the first 300 words explicitly names the organisation, its category, and its function.` | medium | Exclude if title has clear category or CHK-D-007 present. Gated on commercial/org. | `not_determinable` if JS-only. | Add clear declarative sentence naming category and function. | low | — pending |
| CHK-D-007 | marketplace_auditor | D — missing/incomplete Organization JSON-LD | P-06.01, P-06.02, P-01.15 | THEORETICAL / PRACTITIONER | Absence or missing required fields in @type: Organization (home) | `No Organization JSON-LD block found.` OR `Found but missing: {fields}.` | medium | Exclude personal/hobby sites. | `not_determinable` if injected via JS. | Add/complete JSON-LD Organization block. | low | — pending |
| CHK-D-008 | marketplace_auditor | B — duplicate content attribution risk | P-01.06, P-01.07 | CAUSAL | Missing or cross-domain rel=canonical (3-5 pages) | `Page {URL}: no rel=canonical found.` OR `canonical points to {other_domain}.` | medium | Pass if self-referential or valid pagination. | `Redirect chain too deep.` | Add consistent self-referential rel=canonical. | low | — pending |
| CHK-D-009 | marketplace_auditor | B — broken internal links | P-01.06, P-01.07 | THEORETICAL / CORRELATIONAL | 4xx/5xx status of internal links (up to 20 HEAD requests) | `Found {N} broken internal link(s).` | low | Exclude robots.txt blocked paths and fragment links. | `not_determinable` on bot 403. | Repair/remove links; add 301s. | medium | — pending |
| CHK-D-010 | marketplace_auditor | B/C — low extractable-evidence density | P-01.10, P-01.01, P-01.02 | CORRELATIONAL | No definitions, numbers with units, or comparisons across content pages (2-3 pages) | `None of the checked pages contain a definition, numerical fact, or comparison.` | medium | Exclude non-informational pages. Suppress if CHK-D-004 (thin content) fires. | `not_determinable` if extraction fails. | Add explicit definitions, numerical facts, or comparisons. | low | — pending |
| CHK-D-011 | marketplace_auditor | C — pronoun-saturated key claims | P-01.05, P-01.02, P-06.04 | THEORETICAL / HEURISTIC | >60% sentences start with pronoun w/o explicit antecedent (home/about) | `{pct}% of sentences use a pronoun as subject without a preceding explicit mention.` | low | Exclude narrative/blog pages. | `not_determinable` if extraction fails. | Ensure first occurrence of key claims explicitly names the subject. | low | — pending |
| CHK-D-012 | marketplace_auditor | D — missing date signal on time-sensitive content | P-06.08, P-06.09 | THEORETICAL | Missing date in body/meta on TIME-SENSITIVE pages (3-5 pages) | `Page {URL} (time-sensitive) has no detectable publication date.` | low | NEVER raise on EVERGREEN. Suppress if valid Last-Modified header present. | `not_determinable` if page type ambiguous. | Add visible date or article:published_time meta. | low | — pending |
| CHK-D-013 | marketplace_auditor | C — near-duplicate templated thin content | P-01.09, P-06.03 | CORRELATIONAL | Jaccard similarity >0.8 across >=3 pages (4-6 inner pages) | `Pages share {pct}% of word trigrams in their main content.` | low | Exclude legitimate variant pages or legal/ToS pages. | `not_determinable` if extraction fails. | Add unique content answering specific questions for that variant. | medium | — pending |
| CHK-D-025 | TBD (Phase 2) | D — no declared identity anchors, so cross-web corroboration has nothing to attach to | P-06.05, P-06.06, P-06.07, P-06.01 | CORRELATIONAL | `sameAs` array in Organization/Person JSON-LD, plus outbound identity-profile links in header/footer (home + about, static HTML) | `No sameAs declarations or outbound identity-profile links found on the homepage or about page.` | medium | Suppress on personal/hobby/portfolio archetype. Any one resolvable anchor passes. | `not_determinable` if both pages are JS-only and CHK-D-003 fired | Declare identity anchors: add `sameAs` to the Organization JSON-LD pointing at the organisation's authoritative external profiles (public knowledge base, official social accounts, industry or company registry). | very-low | — pending |
| CHK-D-026 | TBD (Phase 2) | D — declared anchors that don't resolve break the disambiguation chain | P-06.05, P-06.06, P-01.06 | HARD-MECHANICAL | Bounded HEAD on each declared anchor URL: max 8 URLs, 3 s timeout, max 3 redirects, one request per host | `{N} of {M} declared identity anchors did not resolve (statuses: {list}).` | high if all anchors fail; medium if some fail | 401/403/429 means bot-blocked, **not** broken — those are not-determinable, never findings. Requires ≥1 anchor to exist, else CHK-D-025 fires instead. | `not_determinable` per anchor on timeout, 401, 403, 429 | Repair or remove dead anchor URLs so every declared profile resolves. | low | — pending |
| CHK-D-027 | TBD (Phase 2) | D — self-inconsistent identity attributes actively defeat corroboration | P-06.03, P-06.05, P-01.05 | THEORETICAL | Compare organisation name, legal name, phone and postal address across JSON-LD, footer, and contact page (3 pages) | `Organisation name appears as {variants} across {N} locations.` | medium if name or legal-name conflict; low if only formatting variance | Suppress pure formatting differences (whitespace, punctuation, "Ltd" vs "Limited", international phone prefixes). Requires ≥2 observed instances. | `not_determinable` if fewer than 2 instances found | State one canonical form of the organisation name, legal name, phone and address, and use it identically in every location. | low | — pending |

---

## Engagement checks

| CHK-ID | Owning skill | Mechanism | Sources | Evidence strength | Observation | Evidence emitted | Severity rule | FP guard | Not-determinable | Suggested action | Runtime | Verified by hand |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CHK-E-014 | marketplace_auditor | E — machine-detectable WCAG failures | P-07.06, P-07.07, P-04.11 | HARD-MECHANICAL / NORMATIVE | Missing lang, missing alt, empty links/buttons, unlabelled inputs, low contrast (3-5 pages) | `Page {URL}: {N} accessibility violation(s) of type {type}.` | high (a-e), medium (f contrast) | `alt=""` is correct for decorative. | `not_determinable` for contrast on JS-SPA. | Standard WCAG fixes per violation type. | low | — pending |
| CHK-E-015 | marketplace_auditor | E — viewport blocking | P-07.15, P-07.01, WCAG 1.4.4 | HARD-MECHANICAL / NORMATIVE | Missing viewport meta, user-scalable=no, max-scale<2, horizontal overflow (2-3 pages) | `Missing viewport meta` / `disables user zoom` / `horizontal scroll` | high for zoom block; medium for missing meta / overflow | Exclude desktop-only sites. Exclude minimum-scale=1. | `not_determinable` for overflow if headless fails. | Add standard viewport meta; remove zoom blocks; fix responsive CSS. | low/high | — pending |
| CHK-E-016 | marketplace_auditor | E — small tap targets | P-07.15, WCAG 2.2 | NORMATIVE | Standalone targets < 24x24 CSS px (1-2 pages) | `{N} standalone interactive elements are below WCAG 2.2 SC 2.5.8 minimum.` | medium | Exclude inline text links and spaced targets. | `not_determinable` if headless fails. | Increase target size or padding to >= 24x24 px. | high (headless) | — pending |
| CHK-E-017 | marketplace_auditor | E — non-descriptive anchor text | P-07.12, WCAG 2.4.4, P-07.06 | NORMATIVE / THEORETICAL | >10% of links use "click here", "read more", etc. (2-3 pages) | `{N} links ({pct}%) have non-descriptive anchor text.` | medium | Exclude aria-labeled links. | n/a | Use descriptive link text. | low | — pending |
| CHK-E-018 | marketplace_auditor | C/E — content-blocking overlay at load | P-07.09, P-07.11 | HARD-MECHANICAL / NORMATIVE | Fixed/absolute element with z-index >= 999 covering >= 50% viewport + body scroll lock (2-3 pages) | `An overlay covering ~{pct}% of viewport with scroll-lock is present at load.` | high | Suppress COOKIE-CONSENT / AGE-GATE. | `not_determinable` for scroll-triggered modals. | Trigger overlays via user interaction; remove scroll-lock. | low | — pending |
| CHK-E-019 | marketplace_auditor | C/E — blank first paint | P-07.10, P-04.10, P-07.02 | HARD-MECHANICAL / CAUSAL | JS-rendering gap (CHK-D-003) >= 0.5 + no noscript fallback + no skeleton | `Homepage: plain HTTP fetch yielded {words} words; no loading indicator or noscript present.` | high | Suppress if noscript >50w or skeleton UI present. | `not_determinable` if headless fails. | Implement SSR/SSG or meaningful loading state. | low (shared) | — pending |
| CHK-E-020 | marketplace_auditor | E — autoplaying media with sound | WCAG 2.2 SC 1.4.2 (Audio Control); P-07.09 = supporting only | NORMATIVE | `<video autoplay>` or `<audio autoplay>` without `muted`, and no pause/stop control (2-3 pages) | `{N} video/audio element(s) autoplay with sound and no pause/stop mechanism (WCAG 2.2 SC 1.4.2).` | medium | `video autoplay muted` is fine. | `not_determinable` if added via JS dynamically. | Add `muted` to video; remove autoplay from audio. | low | — pending |
| CHK-E-021 | marketplace_auditor | E — structural CLS causes (missing dimensions) | P-07.01, P-07.02 | THEORETICAL | `<img>`/`<iframe>` without width+height/aspect-ratio (2-3 pages) | `{N} image(s)/iframe(s) lack explicit width/height or aspect-ratio, so content reflows during load.` | medium if ≥10 affected elements across ≥2 pages; otherwise low. **Never higher** — the reflow is mechanical but the engagement harm is unevidenced (domain 07: Google's own threshold documentation states CLS has no perception research behind it). Framed as a defect per D-008, not as an engagement prediction. | Require N>=3. Exclude responsive `<picture>` tags. | `not_determinable` for CSS-computed dimensions. | Add width/height attributes or CSS aspect-ratio. | low | — pending |
| CHK-E-022 | marketplace_auditor | E — missing landmark/heading integrity | P-07.05, P-07.06, P-04.11 | NORMATIVE / PRACTITIONER | Missing `<main>`, multiple/zero `<h1>`, heading skips (3-5 pages) | `Violation: {description}. Violates structural conventions.` | high (no h1), medium (skips/missing main) | Exclude skips on user-generated content pages. | n/a | Add `<main>`, ensure exactly one `<h1>`, fix heading skips. | low | — pending |
| CHK-E-023 | marketplace_auditor | E — ad/promo density >30% on mobile | P-07.09 | CORRELATIONAL / NORMATIVE | Ad element area >30% in 375px viewport (1-2 pages) | `First viewport: ~{pct}% of visible area occupied by advertisements.` | medium | Suppress if no ads detected site-wide. | `not_determinable` if headless fails. | Reduce ad density; move ads below fold. | high (headless) | — pending |
| CHK-E-024 | marketplace_auditor | E — missing trust signals | P-07.13, P-06.11 (both unverified at time of review) | CORRELATIONAL, single-study | Missing contact info, org name, HTTPS, or byline dates on commercial/news sites (2-3 pages) | `Commercial site: no detectable {signal}.` | **Not emitted as a finding.** Ships as a proactive recommendation only (D-004: single, unreplicated support). Promote to a `low` finding only if P-07.13 is hand-verified. | ONLY apply to commercial/service/news. Exclude personal/hobby. | `not_determinable` for HTTPS timeout. | Add contact info, org name in footer, HTTPS, bylines. | low | — pending |

---

## Declared limitations (reported, never silently omitted)

Things the brief's appendix names as mechanisms that we cannot measure within the
constraints. Each is emitted in the report as an explicit limitation with its reason —
omitting them silently would misrepresent the audit's coverage.

| ID | Mechanism | Why not measurable | How it is reported |
| --- | --- | --- | --- |
| LIM-01 | D — actual agreement across the wider web about the brand's facts | Requires a search or web-scale index API. No free, deterministic, rate-safe source exists; domain 08 confirmed no public dataset of AI-assistant citations exists either. | `not_determinable`, with the note that CHK-D-025/026/027 audit only the *anchoring the site itself provides* for that corroboration |
| LIM-02 | D — whether the brand name is confused with a same-named entity elsewhere | Same. Detecting a name collision needs a corpus of other entities. | `not_determinable`, with CHK-D-027 covering self-consistency as the site-side half |
| LIM-03 | B — whether the brand is currently cited by any assistant | Prohibited by D-006: visibility is a distribution across runs, prompts and time; live querying breaks determinism, runtime and reproducibility | Stated in the report preamble; never claimed either way |
| LIM-04 | E — field engagement outcomes (bounce, dwell, scroll, conversion, task success) | Not observable read-only; requires analytics or user testing (D-008) | `not_determinable` where the gap is itself actionable, otherwise omitted per D-008 |

## Runtime budget and the shared render pass

**One headless render per sampled page, never one per check.** Four checks previously each
implied their own render, which alone would exceed the 5-minute budget. They are consumers
of a single shared artifact set, not triggers.

**Render pass:** at most **3 pages** (homepage + 2 archetype-representative pages),
rendered once each. Each render emits one artifact set: rendered DOM, computed styles,
element geometry, and viewport captures at 375 px and desktop widths.

| Consumer | Reads from the shared artifact |
| --- | --- |
| CHK-D-003 (JS-render gap) | rendered DOM vs. the already-fetched raw HTML |
| CHK-E-014 (contrast subcheck) | computed styles |
| CHK-E-015 (horizontal overflow) | 375 px geometry |
| CHK-E-016 (tap targets) | element geometry |
| CHK-E-018 (blocking overlay) | geometry + computed z-index/scroll-lock |
| CHK-E-019 (blank first paint) | rendered DOM vs. raw (shares CHK-D-003's comparison) |
| CHK-E-023 (ad density) | 375 px geometry |

Everything else runs on static HTML and costs no render.

**Budget against the 300 s cap:**

| Stage | Budget | Notes |
| --- | --- | --- |
| robots.txt + sitemap + page discovery | 15 s | |
| Static fetches (≤20 pages, polite, concurrent) | 45 s | Feeds all static checks |
| Shared render pass (3 pages) | 75 s | 25 s/page ceiling, hard timeout |
| Internal link HEAD checks (≤20) | 25 s | CHK-D-009 |
| Off-site anchor HEAD checks (≤8) | 20 s | CHK-D-026; one request per host |
| Analysis, scoring, composition | 40 s | |
| **Subtotal** | **220 s** | |
| Reserve | 80 s | Slow origins, redirect chains, retries |

**Degradation rule:** if the render pass exceeds its ceiling, it is abandoned and every
consumer above emits `not_determinable` with the reason — never a finding inferred from
static HTML alone. A partial report that says what it couldn't measure beats a complete
report that guessed.

## Review — 2026-09-02

Phase 1b review of the 24 checks. The ledger is in good shape: FP guards and
not-determinable paths are present on every row, suppression logic is wired between
related checks (D-002 defers to D-001; E-019 shares D-003's render), and the rejected list
correctly enforces D-007 and D-008. The following must be resolved before Phase 3.

### R-1 — Hand-verification was never done (blocking)
All 24 rows were marked `Verified by hand: AGY (2026-09)` by the AI tool that authored
them. That column exists to record a **human** spot-check of the cited source (D-003); a
tool certifying its own sourcing defeats the control, and is the exact
grading-in-our-own-favour failure D-010 was written against. All rows reset to
`— pending`. A person must open at least one cited source per check before it ships.

### R-2 — SEARCH-ONLY dependencies — **RESOLVED 2026-09-02**
Resolved without needing to verify the sources, by removing their load-bearing role:
- **CHK-D-003** no longer depends on a magnitude threshold drawn from P-04.10. Its severity
  rule is now *definitional* — raw HTML lacking an h1 and carrying <50 words of main text
  while the rendered DOM has ≥200 means the content is absent from what a non-rendering
  fetch receives. That needs no effect size. P-04.10 is demoted to a lead.
- **CHK-E-019** inherits the corrected comparison.
- **CHK-E-024** drops out of `findings[]` entirely under the new single-source rule; it
  ships as a proactive recommendation until P-07.13 is hand-verified.
- **CHK-E-014 / CHK-E-022** keep verified co-support (P-07.06, P-07.07) and are unaffected.

### R-3 — Severity ceiling widened — **RESOLVED 2026-09-02**
`NORMATIVE` is now a defined evidence strength with a `high` ceiling, recorded as **D-011**,
alongside a single-source rule and the full strength vocabulary above. **CHK-E-020** is
re-grounded on WCAG 2.2 SC 1.4.2 (Audio Control) rather than on a single study's effect
size, and demoted to `medium`. **CHK-E-021** now carries one coherent strength label
(`THEORETICAL`), is graded medium/low by element count, and is explicitly capped — its
reflow is mechanical but its engagement harm is unevidenced.

### R-7 — Minor items — **RESOLVED 2026-09-02**
- ID numbering: documented as a deliberate single global sequence rather than renumbered.
  IDs are stable and never reused, since gold labels will be keyed to them.
- `CORPUS.md`: dev gold labels raised 20 → **24** (D-010's floor); negative controls raised
  24 → **27** for the new off-site dimension.
- Schema home for `low` findings and proactive recommendations settled as **D-012**:
  `findings[]` keeps defects only, with a sibling `recommendations[]` and `limitations[]`.

### R-2 (original finding) — Five checks rest partly on SEARCH-ONLY sources
D-003: search-only sources are leads, not justifications.

| Check | Search-only source | Status |
| --- | --- | --- |
| CHK-D-003 (JS-render gap) | P-04.10 | Has verified co-support (P-04.08, P-04.02) — but P-04.10 is the only source specific to the *gap magnitude*, and this check is our most expensive. **Verify P-04.10 or re-derive the threshold.** |
| CHK-E-019 (blank first paint) | P-04.10, P-07.10 | Inherits the same dependency. |
| CHK-E-014 (WCAG failures) | P-04.11 | Verified co-support (P-07.06, P-07.07) carries it. Low risk. |
| CHK-E-022 (landmark/heading) | P-04.11 | Same. Low risk. |
| CHK-E-024 (trust signals) | P-06.11 | Single support, and it is search-only. **Demote or verify.** |

### R-3 — Severity ceiling was silently widened
The rule as written adds a `NORMATIVE` strength category that D-004 does not define. This
is defensible — WCAG conformance is normative rather than empirical, and shouldn't be
forced into a correlational box — but it is a change to a settled decision and needs to be
recorded as its own decision rather than absorbed into the ledger.

Two rows exceed what their evidence supports:
- **CHK-E-020** (autoplay with sound) sits at `high` on a single source (P-07.09). D-004
  caps single-source, non-replicated support at `low` or proactive-only. Demote to
  `medium` at most.
- **CHK-E-021** (structural CLS causes) is labelled `THEORETICAL / HARD-MECHANICAL`, which
  is incoherent — missing dimensions causing shift is mechanical, but the *harm* is
  precisely what domain 07 found unevidenced (Google's own documentation states CLS has no
  perception research behind it). Pick one label and cap at `medium`.

### R-4 — Headless rendering is not budgeted — **RESOLVED 2026-09-02**
Fixed by the "Runtime budget and the shared render pass" section above: one render per
sampled page (max 3), seven checks declared as consumers of a single artifact set, a 220 s
subtotal against the 300 s cap with 80 s reserve, and a degradation rule that emits
`not_determinable` rather than inferring from static HTML when the render is abandoned.
Original finding follows.
Four checks are marked `high (headless)` or `low/high`: CHK-D-003, CHK-E-015, CHK-E-016,
CHK-E-023. If each triggers its own render, the 5-minute budget is gone. These must be
declared as consumers of **one shared render pass per sampled page**, the way CHK-E-019
already is (`low (shared)`). Until that is explicit, the runtime column understates cost.

### R-5 — Off-site checks are entirely absent — **RESOLVED 2026-09-02**
Fixed by adding CHK-D-025 (no declared identity anchors), CHK-D-026 (declared anchors that
don't resolve — the only genuinely *off-site* fetch in the audit, bounded to 8 HEAD
requests, one per host), and CHK-D-027 (identity attributes self-inconsistent across the
site's own pages). What remains unmeasurable — actual cross-web agreement and same-name
collisions — is now declared as LIM-01 and LIM-02 above and reported rather than omitted.
Note the honest scope: these audit *the anchoring the site itself provides* for
corroboration, not corroboration itself. Original finding follows.
The rejected list drops the Wikidata presence check (external API), external brand-mention
frequency, and cloaking detection. Each rejection is individually reasonable. The
cumulative effect is that **we now have zero off-site checks** — every one of the 24 is
observed on the site's own pages.

The handout's appendix D is explicit that this matters: agreement across independent
sources drives what assistants repeat, mistaken identity is a named failure mode, and "how
a brand is described across the wider web — not just on its own pages — shapes what
assistants say about it." CHK-D-006 (explicit entity definition) and CHK-D-007
(Organization JSON-LD) cover only the on-site half of disambiguation.

This is the largest gap in the current design. Options: accept it and say so explicitly in
the report's own limitations; add a cheap read-only off-site signal (sameAs links,
declared social/knowledge-graph profiles, and their reachability are all observable from
the site's own markup without a search API); or report off-site corroboration as
`not_determinable` with the reason stated. Doing nothing silently is the one option that
costs us on the rubric.

### R-6 — Composition decided by default — **RESOLVED 2026-09-02**
Phase 2 decision made deliberately and recorded as **D-013**, with full rationale in
[`../ARCHITECTURE.md`](../ARCHITECTURE.md): six skills — `site-evidence-collector` (sole
holder of network tools), four mechanism analysers, and `audit-orchestrator` as entrypoint.
**ARCHITECTURE.md §5 is now authoritative for check ownership; the `Owning skill` column
below is superseded and retained only as history.** Original finding follows.
All 24 rows name `marketplace_auditor` as the owning skill, so the ledger has already
committed to a single monolithic skill. A single well-built skill scores fully on the
composition rubric line, so this may well be right — but it should be Phase 2's decision,
made against ablation-testability, not a placeholder that hardened.

### R-7 — Minor
- Engagement checks are numbered `CHK-E-014`…`CHK-E-024`, continuing the discoverability
  sequence rather than starting at `CHK-E-001`. Harmless, but the column spec says
  otherwise; leave it or renumber once, not twice.
- `CORPUS.md` says gold labels are needed on only 20 dev sites, but D-010's floor is ~24
  for a usable precision interval (±7.4 pp at ρ=0.2). Either raise to 24 or accept
  reporting counts rather than rates on dev.
- The report schema still has no decided home for `low`-severity findings or for
  beyond-defect proactive recommendations. Six checks currently emit `low`.

## Rejected checks

- AI-text detection
- Lighthouse SEO score
- Field Core Web Vitals verdict
- Wikidata presence check (external API)
- Cloaking detection
- Scroll depth / bounce rate / dwell time
- Reading-grade / Flesch scores
- Aesthetic quality checks
- External brand-mention frequency
- Recommending llms.txt
