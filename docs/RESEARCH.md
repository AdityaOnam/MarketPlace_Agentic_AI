# Research — mechanism-anchored signals

Field-research output for Phase 1. **No site names, brands, or site-specific selectors.**
Each entry must trace to a mechanism in the Round-2 appendix (A–F, see
[`round3-spec`](../.claude/skills/round3-spec/SKILL.md#8-round-2-background-concepts-the-mechanisms-to-reason-from))
and must be expressible as a deterministic, read-only check on an arbitrary site.

Entry template — copy this per signal:

```
### R-00N — <short signal name>
Half:        discoverability | engagement
Mechanism:   A/B/C/D/E/F — one line on why this matters to a machine
Signal:      the observable, site-agnostic thing we look for
Check:       deterministic, read-only procedure (inputs, page cap, timeout)
Evidence:    the exact quantitative sentence the finding will emit
Severity:    critical | high | medium | low  + the rule that assigns it
FP guard:    the condition under which this must NOT be raised
Not-measurable: how we report inability to measure, distinct from absence
Fix:         what to change and how — mechanism-sound, actionable by a non-expert
Beyond-fix:  optional proactive improvement this suggests even when the check passes
```

---

## Discoverability signals

### R-001 — AI-crawler blocked by robots.txt (retrieval-time agents)

Half:        discoverability
Mechanism:   A — a crawler that cannot enter cannot read the page; blocking retrieval-time
             agents (GPTBot, PerplexityBot, etc.) directly prevents an AI assistant from
             citing or representing the site at answer time.
Signal:      The `robots.txt` file contains `Disallow` rules for user-agent strings
             corresponding to known retrieval-time AI crawlers (GPTBot, PerplexityBot,
             ClaudeBot-Web, BingBot when used for AI Answer) that would block the home
             page or main content paths.
Check:       Fetch `/robots.txt` (single HTTP GET, 5 s timeout). Parse all `User-agent`
             / `Disallow` rule pairs. Classify each blocked agent as RETRIEVAL-TIME
             (known to fetch pages at answer time) or TRAINING-ONLY (known to be used
             only for corpus collection). For any RETRIEVAL-TIME agent with `Disallow: /`
             or `Disallow: /*` apply to the homepage path, emit the finding.
             Page budget: 1 URL (robots.txt only).
Evidence:    "robots.txt line NNN: `Disallow: /` applies to user-agent GPTBot (a
             retrieval-time AI crawler). Pages on this domain cannot be fetched when an
             AI assistant searches for this brand at answer time."
Severity:    critical — hard mechanical consequence: if the rule fires, the page is not
             fetched; no effect size is needed. D-004 causal/hard-mechanical ceiling.
FP guard:    (1) Do NOT raise if all blocked agents are training-only crawlers
             (e.g., CCBot alone) — per P-01.12, blocking training crawlers has near-zero
             measured effect on general knowledge. (2) Do NOT raise if robots.txt syntax
             is valid and the block appears intentional (no contradicting Allow rules
             nearby, or site is news/media where AI-content restrictions are common
             policy). In that case: report as an observation with severity = low and
             framing "deliberate restriction detected; if AI discoverability is desired,
             review this rule." (3) Never flag robots.txt absence as a defect; absence
             means no rules apply.
Not-measurable: If robots.txt returns a non-200 status or times out, emit
             `not_determinable`: "robots.txt is unavailable (HTTP NNN); crawler access
             rules could not be assessed."
Fix:         Remove or narrow the `Disallow` rule for the specific retrieval-time agent
             (e.g., change `Disallow: /` under `User-agent: GPTBot` to `Disallow:
             /admin/`). Confirm the change with a robots.txt validator before deploying.
Beyond-fix:  After unblocking, add an explicit `Allow: /` rule for retrieval-time agents
             to make intent clear and to over-ride any wildcard `User-agent: *` blocks.
             Consider adding `Sitemap:` directive to help crawlers discover key pages.
Sources:     P-01.03 (Longpre et al., arXiv 2407.14933, VERIFIED) — longitudinal audit of
             consent signals; P-01.12 (Fan et al., arXiv 2504.06219, COLM 2025, VERIFIED)
             — data compliance gap study distinguishing retrieval-time from training crawlers.

---

### R-002 — AI-crawler blocked by robots.txt (training-only agents) — informational

Half:        discoverability
Mechanism:   A — training-corpus crawlers (CCBot, Google-Extended) determine which content
             enters future model weights; blocking them affects parametric memory over time
             but has near-zero effect on retrieval-augmented answers today (P-01.12: DCG
             close to 0% for general knowledge domains).
Signal:      The `robots.txt` blocks training-only AI crawlers (CCBot, Google-Extended,
             etc.) with no corresponding retrieval-time block.
Check:       Same parse as R-001. Classify each blocked agent. If any TRAINING-ONLY agent
             is blocked and no RETRIEVAL-TIME agent is blocked: emit informational finding.
             Page budget: 1 URL (shares the robots.txt fetch with R-001).
Evidence:    "robots.txt blocks CCBot (a training-corpus crawler) but permits retrieval-
             time AI crawlers. Content remains available to AI assistants at answer time.
             Parametric model memory will not update from this domain."
Severity:    low — training-corpus exclusion has near-zero measured DCG for general
             knowledge (P-01.12); correlational at most. D-004 caps at low.
FP guard:    Do NOT raise if the block is on all crawlers including retrieval-time ones
             (R-001 already fires and is the dominant finding). Do NOT raise for paywalled
             content, legally-sensitive content (health, legal), or sites whose ToS
             explicitly restricts scraping.
Not-measurable: Same as R-001 if robots.txt unavailable.
Fix:         If future parametric memory coverage matters, remove the training-crawler block.
             If the block is deliberate copyright policy, no action is needed and this
             finding should be dismissed.
Beyond-fix:  None — this is an informational note only. Do not recommend any affirmative
             action; the site owner's deliberate policy is a legitimate choice.
Sources:     P-01.03 (arXiv 2407.14933, VERIFIED); P-01.12 (arXiv 2504.06219, VERIFIED).

---

### R-003 — JS-rendering gap: primary content invisible to AI crawlers

Half:        discoverability
Mechanism:   C — content assembled only after JS execution is structurally invisible to
             any program that reads the raw HTTP response without rendering. AI crawlers
             (GPTBot, CCBot, PerplexityBot) are documented to not execute JavaScript.
Signal:      The no-JS raw HTTP response body contains substantially fewer extractable
             text tokens than the headless-rendered DOM for the same page — indicating
             that significant content (including the primary value proposition) is only
             present after JS execution.
Check:       (1) Fetch the homepage with a plain HTTP GET (no JS). Extract main-content
             text using a boilerplate-removal tool (per P-04.09). Count tokens.
             (2) Fetch the same URL through a headless browser. Extract main content.
             Count tokens. (3) If rendered_tokens > raw_tokens × 1.5 (i.e., rendered
             has >50% more content), compute the fraction of rendered text absent from
             raw. If the absent fraction includes keywords from the <title> or <h1>, flag
             as high severity; otherwise medium.
             Page budget: 1 page headless render + 1 plain GET (homepage or key page).
             Timeout: 60 s for headless render.
Evidence:    "Homepage: plain HTTP fetch yielded NNN tokens of main content; headless
             render yielded MMM tokens (X% more). The missing content includes [sampled
             phrase from rendered-only text]. AI crawlers that do not execute JavaScript
             will see only the plain-fetch content."
Severity:    high if the plain-fetch content is < 30% of rendered content and the page's
             <title>/<h1> is absent from plain fetch; medium if content is present but
             supplementary material is missing. D-004 hard-mechanical: if content is
             invisible to non-rendering crawlers, that is a causal consequence.
FP guard:    (1) Do NOT raise for lazy-loaded images (images are not text content).
             (2) Do NOT raise if the raw HTML contains a `<noscript>` block with
             substantive main content. (3) Do NOT raise if the difference is < 20% and
             both versions contain the primary value proposition. (4) If robots.txt blocks
             all AI crawlers (R-001 fired), this check is redundant: report as
             not_determinable.
Not-measurable: If headless render times out or fails, emit `not_determinable`: "headless
             rendering did not complete within the time budget; JS-rendering gap could not
             be assessed."
Fix:         Implement server-side rendering (SSR) or static-site generation (SSG) so that
             the primary value proposition — the organisation's name, what it does, and key
             facts — are present in the initial HTTP response body. Frameworks like Next.js,
             Nuxt, or Gatsby provide SSR without removing client-side interactivity.
Beyond-fix:  Add `<noscript>` fallback text for critical above-fold content. Enable
             Google's "Inspect URL" tool in Search Console to confirm Googlebot sees the
             full page content.
Sources:     P-04.10 (JS rendering gap, SEARCH-ONLY — mechanism well-established across
             Google dev docs and practitioner experiments; no peer-reviewed study verified);
             P-04.08 (Lai et al., arXiv 2404.03648, KDD 2024, VERIFIED — HTML simplification
             shows page-representation quality dominates model size); P-04.02 (Deng et al.,
             arXiv 2306.06070, NeurIPS 2023, VERIFIED — raw HTML too large; filtering needed).

---

### R-004 — Low extractable-text density: thin main content

Half:        discoverability
Mechanism:   C — the more explicitly and unambiguously a fact is stated in plain, readable
             text, the more likely it is extracted correctly. A page with little extractable
             text after boilerplate removal has little to work with.
Signal:      After boilerplate removal (main-content extraction), a content page yields
             fewer than ~200 words of unique body text — indicating that the substantive
             content is either missing, entirely JS-rendered (see R-003), or crowded out
             by boilerplate.
Check:       Fetch the page with plain HTTP GET. Apply main-content extraction (per P-04.09
             Trafilatura or equivalent). Count words in extracted text. For pages with a
             content-bearing archetype (blog/article, documentation, product detail,
             service page), flag if extracted word count < 200. Skip for contact, 404, and
             single-action pages.
             Page budget: 3–5 pages (home + 2–4 inner content pages), static fetch only.
Evidence:    "Page [URL]: main-content extraction yielded NNN words after boilerplate
             removal. AI retrieval systems drawing from this page have very little text to
             quote or attribute."
Severity:    medium — correlational (absorption requires content; P-01.10 shows high-
             influence pages are longer). D-004 caps correlational at high, but here the
             effect is per-page rather than a hard block. Medium is appropriate.
FP guard:    (1) Do NOT raise on JS-heavy SPAs without first checking the rendering gap
             (R-003); a thin raw-fetch result on an SPA is a rendering issue, not a
             content issue. (2) Do NOT raise on archetype-inappropriate pages:
             contact pages, privacy policies, landing pages with a single CTA, and
             deliberately minimal portfolio/one-page sites. (3) Condition on page type per
             D-009.
Not-measurable: If main-content extraction returns an extraction error or the page
             requires login, emit `not_determinable`.
Fix:         Add substantive, explicitly-stated content to the page: define what the
             product or service does in the first paragraph; include key factual claims
             (numbers, categories, use cases) as body text rather than images or video.
Beyond-fix:  Structure the page with descriptive `<h2>`/`<h3>` subheadings so that each
             content block is independently quotable. This also helps chunking systems
             retain context across page fragments (P-01.13).
Sources:     P-04.08 (arXiv 2404.03648, VERIFIED — HTML simplification; content richness
             matters); P-04.09 (Barbaresi, ACL 2021, VERIFIED — Trafilatura validated for
             main-content extraction); P-01.10 (Zhang Kai et al., arXiv 2604.25707, VERIFIED
             — high-influence pages are longer and richer in extractable evidence).

---

### R-005 — Missing or generic heading structure: content not independently quotable

Half:        discoverability
Mechanism:   B/C — AI assistants fetch pages and build answers from what those pages say.
             Pages with descriptive headings survive fragmentation into retrieval chunks
             better than pages with generic or absent headings; each section is independently
             quotable. Generic headings ("Overview", "Learn More", "Solutions") carry no
             context if a retrieval chunk starts at the heading.
Signal:      Content pages have zero `<h2>`/`<h3>` subheadings under a large word count
             (>500 words), or all heading texts are single generic words with no content-
             carrying terms.
Check:       Fetch page (static HTTP GET). Parse heading hierarchy: `<h1>`, `<h2>`,
             `<h3>`. For each content page: (a) if word count > 500 and heading count
             (h2+h3) = 0: flag; (b) if all h2/h3 text ≤ 12 characters or all match a
             generic-word list ("Overview", "Learn more", "Features", "Why us", "Benefits",
             "More", "Contact"): flag.
             Page budget: 3–5 pages, static fetch only.
Evidence:    "Page [URL]: NNN words of body text with 0 descriptive subheadings. Retrieval
             systems chunking this page will produce fragments with no topic context."
Severity:    low — the chunking-to-page-authoring transfer is our extrapolation (P-01.13
             studies chunker design, not page authoring directly); D-004 caps this
             theoretical/practitioner observation at medium, but given that it is an
             extrapolation, low is the honest assignment.
FP guard:    (1) Do NOT raise on archetype-inappropriate pages: legal pages, privacy
             policies, single-section FAQ pages, and deliberately minimal pages are
             correctly structure-free. (2) Do NOT raise if a long page uses `<strong>` or
             `<p>` lead-in sentences as effective section markers — only flag genuine absence
             of any sectioning signal. (3) Condition on page type per D-009.
Not-measurable: If main content cannot be extracted (login, JS-only), emit
             `not_determinable`.
Fix:         Add descriptive `<h2>` subheadings to each major topic block, front-loaded
             with the content-bearing term (e.g. "Enterprise pricing tiers" not "Pricing").
             Each `<h2>` section should be independently understandable if read alone.
Beyond-fix:  Restructure content so each `<h2>` section answers a specific question likely
             to be searched. This provides information scent (P-07.12) and makes the page
             a stronger source in retrieval-augmented generation (P-01.13).
Sources:     P-01.13 (Merola & Singh, arXiv 2504.19754, ECIR 2025, VERIFIED — RAG chunking
             and context loss); P-01.10 (arXiv 2604.25707, VERIFIED — structured pages show
             higher citation influence); P-07.08 (Nielsen/NNg F-pattern, VERIFIED — scanning
             behaviour supports front-loaded headings).

---

### R-006 — Missing explicit entity definition: organisation not self-identifying

Half:        discoverability
Mechanism:   D — agreement across the web matters; entities that are clearly named and
             categorised in their own text are easier to link to knowledge graphs and
             less likely to be confused with same-name entities (mistaken identity failure).
Signal:      The site's main content pages do not contain a sentence that explicitly names
             the organisation, states its category (industry/sector), and states its primary
             function — the AIS interpretability-gate equivalent for entity identity.
Check:       Fetch the About/Home page (static GET). Extract main content. Search for
             sentences matching: [explicit org name] + [category word: company, platform,
             agency, service, tool, etc.] + [function verb or noun]. If no such pattern
             found in the first 300 words of main content, flag.
             Page budget: 1–2 pages (home + about, if both exist).
Evidence:    "No sentence in the first 300 words of main content explicitly names the
             organisation, its category, and its function. AI extraction systems may
             fail to anchor this entity to a known category."
Severity:    medium — mechanism-level link to entity disambiguation (P-06.05, P-06.06),
             supported by structured-data and KG literature; correlational. D-004 caps
             at high, but the observable check is a heuristic pattern-match, so medium.
FP guard:    (1) Do NOT raise if the organisation is in the `<title>` tag with a clear
             category descriptor ("Acme — Enterprise Software"). (2) Do NOT raise if an
             Organization schema.org block with `name`, `description` and `knowsAbout` is
             present and complete (R-007 covers that). (3) Do NOT raise on personal blogs
             or portfolio pages where the entity type is evident from context.
Not-measurable: If extraction fails (JS-only, login wall), emit `not_determinable`.
Fix:         Add a clear declarative sentence near the top of the About and Home pages:
             "[Organisation name] is a [category] that [primary function]." This sentence
             should survive being read out of context without any surrounding page to
             resolve pronouns or antecedents.
Beyond-fix:  Extend the definition to include the geographic jurisdiction (country/city)
             and the founding year. This anchors the entity against same-name entities in
             different locations or eras, reducing name-collision risk (P-06.10).
Sources:     P-01.05 (Rashkin et al., arXiv 2112.12870, VERIFIED — AIS stage-1
             interpretability gate); P-06.05 (BLINK, EMNLP 2020, VERIFIED — entity
             disambiguation requires description anchor); P-06.06 (ReFinED, arXiv 2207.04108,
             VERIFIED — entity type is primary disambiguation signal); P-01.15 (Varga,
             arXiv 2606.21595, VERIFIED — entity name ambiguity finding, single study).

---

### R-007 — Absent or incomplete Organization schema markup

Half:        discoverability
Mechanism:   D — machine-readable entity identity (schema.org) is the site-side lever for
             being correctly represented by knowledge-graph-anchored systems. A well-formed
             Organization block lets extraction systems associate the domain with a typed,
             named entity.
Signal:      The site has no `<script type="application/ld+json">` block with `@type:
             Organization` (or a subtype such as LocalBusiness, Corporation), OR such a
             block exists but is missing required fields (`name`, `url`) or has null/empty
             values for `description` or `logo`.
Check:       Fetch home page (static GET). Parse `<head>` and inline `<script
             type="application/ld+json">` blocks. Check for `@type` values in the
             Organisation hierarchy. If found, validate: `name` non-null, `url` non-null,
             `description` non-null. If not found: flag absence. If found but fields
             missing: flag incompleteness.
             Page budget: 1 page (home page).
Evidence:    (Absent) "No Organization JSON-LD block found on the home page."
             (Incomplete) "Organization JSON-LD found but missing fields: [list]. These
             fields are required for knowledge-graph extraction."
Severity:    medium — the base rate is that 55.88% of domains carry no structured data at
             all (P-06.01 WDC Oct 2024: 16.5M of 37.4M domains). Absence is unremarkable
             at the population level; absence on a commercial site where identity matters
             is a missed opportunity. D-009 requires conditioning on site type: apply only
             to sites with commercial, service, or organisation intent. Evidence is
             theoretical/practitioner; D-004 caps at medium.
FP guard:    (1) Do NOT raise on personal blogs, purely informational pages, or minimal-
             by-design sites (portfolio/one-pager archetype). (2) Do NOT raise for missing
             optional fields (contactPoint, sameAs, foundingDate) — only required fields
             (`name`, `url`) justify a finding; optional fields produce a proactive
             recommendation only. (3) Per D-009: condition on archetype.
Not-measurable: If the page is JS-only and JSON-LD is injected client-side, flag as
             `not_determinable`: "structured data could not be assessed on a JS-rendered
             page; a headless render would be required."
Fix:         Add a JSON-LD Organization block to the `<head>` of the home page and every
             canonical page. Minimum required: `@context`, `@type`, `name`, `url`,
             `description`. Recommended: `logo`, `contactPoint`, `sameAs` (links to
             authoritative profiles such as LinkedIn, Wikidata, Companies House).
Beyond-fix:  Add `sameAs` links to authoritative external knowledge bases (Wikidata,
             official company registry). This is the site-side lever for KG anchoring
             (P-01.15, P-06.05) and reduces long-tail hallucination risk (P-06.07).
Sources:     P-06.01 (WDC Oct 2024, webdatacommons.org, VERIFIED — 44.12% domain coverage,
             base-rate calibration); P-06.02 (Web Almanac 2024, httparchive.org, VERIFIED
             — schema adoption trends); P-01.15 (arXiv 2606.21595, VERIFIED — KG anchoring
             for entity visibility).

---

### R-008 — Missing canonical URL signal: attribution risk from duplicate content

Half:        discoverability
Mechanism:   B — pages that get picked to be cited tend to be easy to reach and easy to
             quote. Duplicate or syndicated copies dilute attribution. The Tow Center study
             (P-01.06) found AI engines systematically cited syndicated copies (Yahoo News,
             AOL) over originals, and over 60% of responses were incorrect overall.
Signal:      Key pages lack a `<link rel="canonical">` tag, or the canonical URL is not
             self-referential and consistent across the site, indicating unresolved
             duplicate/syndicated content.
Check:       Fetch 2–3 key content pages (static GET). Parse `<head>` for `<link
             rel="canonical" href="...">`. Verify: (a) tag exists, (b) it matches the
             requested URL (or the expected normalised form — trailing slash / www /
             https), (c) it is not a different-domain URL that would indicate the site
             acknowledges it is syndicated content. Flag if absent or pointing off-domain
             unexpectedly.
             Page budget: 3–5 pages.
Evidence:    (Absent) "Page [URL]: no rel=canonical found. Duplicate copies of this
             content may be cited by AI systems in preference to this page."
             (Cross-domain) "Page [URL]: rel=canonical points to [other-domain URL].
             This page defers attribution to another domain."
Severity:    medium — the attribution failure is causal at the mechanism level (P-01.06,
             Tow Center, VERIFIED) but the site-side fix has correlational rather than
             proven causal effect on AI citations. D-004 caps at high for causal; we use
             medium because the direct effect of canonical on AI citations (vs. traditional
             search) is not yet experimentally demonstrated.
FP guard:    (1) Do NOT raise if canonical is self-referential and matches the fetched URL
             (normalising www, scheme, trailing slash). (2) Do NOT raise on purposeful
             cross-site canonicals in known syndication setups — only flag when the
             cross-domain canonical is unexpected given the site's apparent identity.
             (3) Do NOT raise on pagination rel=canonical patterns that are valid.
Not-measurable: If the page returns a redirect chain to a canonical URL, follow it (up to
             5 hops) and check the final URL.
Fix:         Add `<link rel="canonical" href="https://[domain]/[path]/">` to every page's
             `<head>`. Ensure HTTPS, consistent www/non-www, and consistent trailing-slash
             policy across the whole site. Set up 301 redirects from non-canonical
             variations so there is a single reachable URL for each page.
Beyond-fix:  Audit for syndicated copies of key content pages appearing on third-party
             domains; request canonicals or takedowns where the content is republished
             without attribution back to this domain.
Sources:     P-01.06 (Jaźwińska & Chandrasekar, CJR Tow Center, VERIFIED — over 60%
             AI response errors; syndicated copies cited over originals); P-01.07 (Zhang
             et al., arXiv 2512.09483, VERIFIED — LLM search draws from a partly different
             pool than traditional search).

---

### R-009 — Broken internal links: citation instability risk

Half:        discoverability
Mechanism:   B — pages easy to reach are more likely to be picked. Broken links signal
             an unstable URL structure; AI search engines citing a URL that returns 404
             are contributing to citation errors. P-01.06 found over 50% fabricated or
             broken URLs on some engines; the site cannot control engine hallucination but
             can control its own link integrity.
Signal:      Internal links (same-domain `<a href>` pointing to pages on this site) return
             4xx or 5xx HTTP status codes.
Check:       Fetch 3–5 pages (static GET). Parse all `<a href>` pointing to the same
             domain. Sample up to 20 unique internal link destinations and issue HEAD
             requests (with 10 s timeout each). Count 4xx and 5xx responses. If any 4xx
             found, flag.
             Page budget: 3–5 pages for link discovery + up to 20 HEAD requests.
Evidence:    "Found N broken internal link(s): [URL list]. An AI assistant citing one of
             these paths would direct users to a dead page."
Severity:    low — the Tow Center finding (P-01.06) establishes that broken/fabricated
             citations are common, and stable URLs reduce the risk; but the causal link
             from fixing a 404 to reducing citation errors is indirect. D-004 caps at low
             for this indirect chain.
FP guard:    (1) Do NOT raise if the only 404s are on pages explicitly excluded by
             robots.txt. (2) Do NOT raise for redirect chains that resolve successfully
             (follow up to 5 hops, pass if the final response is 2xx). (3) Do NOT raise
             on `#fragment` links (client-side navigation). (4) Rate-limit HEAD requests
             to avoid triggering bot detection.
Not-measurable: If HEAD requests are blocked (403, bot protection), emit `not_determinable`
             for those specific URLs.
Fix:         Repair or remove the broken links. Implement 301 redirects for URLs that
             have moved permanently. Set up regular crawl-based link checking as a
             maintenance practice.
Beyond-fix:  Implement a consistent URL structure (no dates in paths for evergreen content)
             that is stable across site migrations and CMS changes.
Sources:     P-01.06 (Tow Center, VERIFIED — broken/fabricated citation URLs common);
             P-01.07 (arXiv 2512.09483, VERIFIED — LLM search source-pool analysis).

---

### R-010 — Low extractable-evidence density: no definitions, numbers, or comparisons

Half:        discoverability
Mechanism:   B/C — AI assistants pick sources whose pages are easy to read and easy to
             quote a clear fact from. High-influence pages (P-01.10) are longer, more
             structured, and richer in definitions, numerical facts, comparisons, and
             procedural steps. Any of these is observable read-only.
Signal:      Content pages aimed at informing or converting (product, service, feature,
             FAQ, documentation) have no extractable definitions ("X is a …"), no
             numerical facts with units (measurements, counts, percentages with context),
             and no comparison structure (tables, "versus" sections, attribute lists).
Check:       Fetch 2–3 content pages (static GET). Extract main content. Apply heuristic
             detection: (a) definition sentence: first occurrence of "[Subject] is a
             [category]" or "[Subject] allows/enables [object]"; (b) numerical fact: any
             numeric token with a unit (%, $, ms, GB, users, years) in a declarative
             sentence; (c) comparison: presence of `<table>`, "vs.", "compared to",
             "versus", or a structured list with ≥3 parallel items. Flag if zero of (a),
             (b), (c) detected across all checked content pages.
             Page budget: 2–3 key content pages.
Evidence:    "None of the NNN checked content pages contain a definition of the primary
             product/service, a numerical fact, or a comparative structure. Pages lacking
             these signals are consistently ranked lower in AI answer absorption (P-01.10)."
Severity:    medium — correlational (P-01.10 measurement framework; not a causal
             intervention study). D-004 caps at high for correlational, but given the
             check is a proxy and the evidence is a single April 2026 measurement, medium
             is the honest assignment.
FP guard:    (1) Do NOT raise on pages that are not intended to be informational: contact
             pages, checkout flows, privacy policies, 404 pages, login pages. Per D-009,
             condition on archetype. (2) Do NOT raise on purely image/video-based pages
             where the content medium is intentionally non-textual. (3) The check looks
             for absence across multiple pages; do not fire on a single page that happens
             to be a short landing page if other pages on the site have evidence density.
Not-measurable: If extracted text is empty (JS-only or login-gated), emit `not_determinable`.
Fix:         For each key product or service page: add one explicit definition sentence
             ("X is a [category] that [function]"), at least one factual data point with
             a unit ("supports N concurrent users", "reduces processing time by X%"), and
             if applicable, a comparison section or table showing how the offering relates
             to alternatives or to the problem it solves.
Beyond-fix:  Add a FAQ section with question-and-answer pairs, each answer self-contained
             enough to be quoted without the question as context. This dramatically
             improves the passage-retrieval quotability (P-01.02, P-01.05) of the page.
Sources:     P-01.10 (Zhang Kai et al., arXiv 2604.25707, VERIFIED — high-influence pages
             richer in definitions, numbers, comparisons); P-01.01 (Aggarwal et al.,
             arXiv 2311.09735, KDD 2024, VERIFIED — GEO shows page text is a lever);
             P-01.02 (Gao et al., arXiv 2305.14627, EMNLP 2023, VERIFIED — ALCE:
             retrievable passages that entail the claim).

---

### R-011 — Pronoun-anchored key claims: primary facts not self-contained

Half:        discoverability
Mechanism:   C — the more explicitly and unambiguously a fact is stated, the more likely
             it is extracted correctly. The AIS stage-1 interpretability gate (P-01.05)
             requires a statement to be interpretable standalone — a sentence with "we",
             "it", or "our" as the subject, where no antecedent is nearby, fails the
             gate and cannot be attributed.
Signal:      The main content of key pages has a high fraction of sentences where the
             subject is a pronoun ("we", "our", "it", "they") or unresolved reference
             with no preceding explicit mention of the organisation's name in the same
             paragraph.
Check:       Fetch 2–3 content pages (static GET). Extract main content. Count sentences
             where the grammatical subject is "We", "Our", "It", "They" and the page's
             own organisation name does not appear in the same or preceding sentence. If
             > 60% of sentences in the opening 300 words of main content use such
             pronoun subjects with no nearby explicit antecedent: flag.
             Page budget: 2–3 pages, static fetch only.
Evidence:    "In the first 300 words of page [URL], NNN% of sentences use a pronoun as
             the subject without a preceding explicit mention of the organisation name.
             These sentences cannot be attributed without surrounding context."
Severity:    low — the AIS framework (P-01.05) establishes the mechanism but not a
             quantitative threshold; the pronoun-density heuristic is our extrapolation.
             D-004 caps theoretical/practitioner at medium; we assign low given the heuristic
             nature of the check.
FP guard:    (1) Conversational or narrative pages (blog posts, case studies) are expected
             to use pronouns; only flag on pages intended to state facts about the
             organisation (About, Home hero, Product descriptions). Per D-009.
             (2) Do NOT flag a page where "we" is preceded by the organisation's name in
             the same sentence or in the immediately preceding sentence.
Not-measurable: If main content extraction fails, emit `not_determinable`.
Fix:         Rewrite the opening paragraphs of About and Product pages so the first
             occurrence of each key claim explicitly names the subject (the organisation
             or product name) rather than using a pronoun. Subsequent sentences in the
             same paragraph may use pronouns if the antecedent is immediately prior.
Beyond-fix:  Apply the AIS "would a stranger understand this sentence alone?" test to
             every statement intended to be a key fact. If the answer is no, rewrite.
Sources:     P-01.05 (Rashkin et al., arXiv 2112.12870, VERIFIED — AIS interpretability
             gate); P-01.02 (Gao et al., arXiv 2305.14627, VERIFIED — entailment requires
             a retrievable passage); P-06.04 (Thorne et al., arXiv 1803.05355, NAACL 2018,
             VERIFIED — FEVER κ=0.68 for claim extractability).

---

### R-012 — Missing or stale date signal on time-sensitive content

Half:        discoverability
Mechanism:   D — LLMs have a parametric timestamp tied to training data (P-06.09); facts
             on a page that has not been re-crawled since a change will persist as
             outdated in LLM memory. The FreshQA study (P-06.08) shows all tested LLMs
             struggle with fast-changing knowledge. The site-side lever is explicit date
             signals on pages whose content expires.
Signal:      Pages with time-sensitive content (press releases, pricing, product version
             notes, news articles, personnel/leadership pages) lack an explicit date stamp
             in the body text or in `<meta>` / `article:published_time` Open Graph tags.
Check:       Fetch 2–3 content pages. Classify each as TIME-SENSITIVE (news, announcement,
             pricing, version-specific, leadership) or EVERGREEN (marketing copy, about
             pages, general descriptions). For TIME-SENSITIVE pages: check for (a) a date
             pattern (ISO 8601 or common prose format "Month YYYY") in main-body text,
             or (b) `<meta property="article:published_time">` in `<head>`. If neither
             present: flag.
             Page budget: 3–5 pages sampled by type, static fetch only.
Evidence:    "Page [URL] (classified as time-sensitive: [reason]) has no detectable
             publication or modification date. AI systems relying on this page for current
             information have no basis to assess its freshness."
Severity:    low — freshness is mechanistically linked to correct representation (P-06.08,
             P-06.09) but the causal strength per-page is weak; the site may update content
             without updating a date. D-004 caps theoretical/practitioner at medium; low
             given the classification heuristic.
FP guard:    (1) NEVER raise on evergreen content (marketing copy, static about pages,
             general descriptions). The freshness trap: old ≠ stale if the content is not
             time-dependent. (2) Do NOT raise if a `Last-Modified` HTTP header is present
             and recent — treat as a weak freshness signal (not conclusive per P-06.08
             discussion, but sufficient to suppress the finding). (3) Do NOT raise if the
             footer copyright year is the only date present — footer dates are often auto-
             generated and do not reflect content updates.
Not-measurable: If page type cannot be determined from extracted text, emit `not_determinable`
             for that page's freshness check.
Fix:         Add a visible "Published" or "Last updated" date in the body text of all
             time-sensitive pages, or add `<meta property="article:published_time">` to
             `<head>`. Update the date whenever the substantive content changes.
Beyond-fix:  Implement a content-expiry review schedule: any page containing software
             version numbers, prices, personnel names, or regulatory status should be
             reviewed quarterly.
Sources:     P-06.08 (Tu Vu et al., arXiv 2310.03214, EMNLP 2023, VERIFIED — FreshLLMs:
             LLMs struggle with fast-changing knowledge); P-06.09 (Dhingra et al.,
             arXiv 2106.15110, TACL 2022, VERIFIED — parametric memory has implicit
             training timestamp).

---

### R-013 — Near-duplicate or templated thin content across many pages

Half:        discoverability
Mechanism:   C — synthetic or near-duplicate content provides little additional signal to
             retrieval systems. P-01.09 found ~16% of cited sources show evidence of AI-
             generation; the risk of thin templated pages being treated as low-quality
             is real regardless of how they were produced.
Signal:      Multiple pages at different URLs contain near-identical main-content text
             (high inter-page text similarity) with only slot-filled differences (name,
             location, price replaced) — indicating a templated content pattern that
             provides no additional retrievable fact.
Check:       Fetch 4–6 inner content pages (static GET). Extract main content from each.
             Compute pairwise Jaccard similarity on word-level trigrams. If any pair
             exceeds 0.8 Jaccard similarity (80%+ shared trigrams after slot-variable
             differences are normalised), flag the group.
             Page budget: 4–6 pages.
Evidence:    "Pages [URL-A] and [URL-B] share approximately X% of trigrams in their main
             content, suggesting near-duplicate templated pages. Retrieval systems treating
             these as distinct sources gain little additional evidence."
Severity:    low — the mechanism link is real (P-01.09) but the check is a proxy; some
             legitimate templated structures (location pages, product variant pages) are
             expected. D-004: single non-replicated study + contested interpretation = low.
FP guard:    (1) Do NOT raise if the duplicate pages are clearly product variant pages
             (e.g., same product in two colours) — this is expected structure. (2) Do NOT
             raise if only 2 pages out of many are similar; the pattern must span ≥ 3
             pages. (3) Do NOT raise for privacy policy / ToS pages that are intentionally
             standard. (4) Severity stays at low regardless of how many duplicates are
             found; do not escalate on volume alone.
Not-measurable: If content extraction fails, emit `not_determinable`.
Fix:         For each templated page type, add unique, specifically-written content that
             answers a question specific to that page's subject (location-specific details,
             use-case-specific examples). Do not recommend generating bulk AI content —
             that is the failure mode this check detects.
Beyond-fix:  Audit for thin pages that are not serving any unique user need; consider
             consolidating or noindexing them.
Sources:     P-01.09 (Allaham & Diakopoulos, arXiv 2605.23684, VERIFIED — ~16% of cited
             sources show AI-generation evidence; thin-content risk); P-06.03 (Li Yang et al.,
             arXiv 2112.08663, WSDM 2022, VERIFIED — MAVE: implicit vs explicit attributes).

---

## Engagement signals

### R-014 — Machine-detectable WCAG failures (the WebAIM six)

Half:        engagement
Mechanism:   E (from Round-2 appendix) — content locked in a form a reader can't interpret
             is invisible; WCAG failures corrupt the accessibility tree, which is the same
             representation web agents and assistive technology use.
Signal:      Presence of any of the six machine-detectable WCAG 2 failure types that
             account for 96% of all detected failures on the web (P-07.06): low-contrast
             text, missing image `alt` text, unlabelled form inputs, empty links, empty
             buttons, missing `<html lang>` attribute.
Check:       Fetch page (static GET). Parse DOM. Run the following per-rule checks:
             (a) `<html>` element lacks `lang` attribute;
             (b) `<img>` elements with no `alt` attribute and no `role="presentation"`;
             (c) `<a>` elements with empty or whitespace-only text content and no
             `aria-label` or `title`;
             (d) `<button>` elements with empty or whitespace-only text and no
             `aria-label`;
             (e) `<input>`, `<select>`, `<textarea>` elements with no associated `<label>`,
             no `aria-label`, and no `aria-labelledby`;
             (f) text elements with colour contrast ratio below 4.5:1 (computed from
             computed colour values — note: CSS variables and dynamic backgrounds reduce
             accuracy; flag low-confidence cases separately).
             Page budget: 3–5 pages, static fetch only.
Evidence:    "Page [URL]: [N] accessibility violations detected: [list of types]. These
             failures corrupt the accessibility tree used by both assistive technology and
             web agent systems (P-07.06, P-04.11)."
Severity:    high for (a)–(e): these are statically deterministic and normatively required
             (WCAG 2.0/2.1 Success Criteria). D-004 allows up to high for correlational;
             these have a normative basis that is stronger. Medium for (f) contrast: false-
             positive risk is higher due to CSS-variable and dynamic-background limitations.
             D-008: frame as "defect that obstructs access", never as "will reduce bounce rate."
FP guard:    (a) Do NOT flag `alt=""` (empty alt) — this is the correct pattern for
             decorative images. Only flag truly missing `alt` attribute. (b) For contrast:
             do NOT flag text that is explicitly marked `aria-hidden="true"`. (c) For
             empty links: do NOT flag links used as icon buttons if they carry an
             `aria-label`. (d) Do NOT extrapolate: "accessibility guidelines are only
             half of the story" — report as a floor, not an exhaustive audit (P-07.07).
Not-measurable: If CSS is dynamically loaded (JS-only), contrast computation may be
             unreliable; emit `not_determinable` for the contrast check on SPA pages.
             Always emit findings for (a)–(e) on raw DOM, even on SPAs.
Fix:         (a) Add `lang="en"` (or correct language code) to `<html>`;
             (b) Add descriptive `alt` text to all non-decorative images;
             (c) Add visible or `aria-label` text to all links and buttons;
             (d) Associate all form inputs with `<label for="...">` or `aria-label`;
             (e) Adjust colour palette to meet 4.5:1 minimum contrast.
             Note: automated detection covers roughly half of real accessibility barriers
             (P-07.07); manual and assistive-technology testing is recommended in addition.
Beyond-fix:  Run a full WCAG 2.1 AA audit with both an automated tool (axe, WAVE) and
             manual review with a screen reader. Automated detection covers the most
             common cases but misses context-dependent barriers.
Sources:     P-07.06 (WebAIM Million 2026, webaim.org, VERIFIED — 95.9% of home pages
             have WCAG failures; six types account for 96%); P-07.07 (Power et al.,
             CHI 2012, SEARCH-ONLY — 50.4% of real blind-user barriers map to WCAG);
             P-04.11 (accessibility tree / machine readability overlap, SEARCH-ONLY —
             WCAG failures corrupt the AXTree used by web agents).

---

### R-015 — Viewport blocking: zoom disabled or no viewport meta

Half:        engagement
Mechanism:   E — content locked in a form a reader can't interpret is invisible; a page
             that cannot be zoomed by users with low vision, or that requires horizontal
             scrolling on mobile devices, is inaccessible to a substantial portion of users.
Signal:      (a) `<meta name="viewport">` is absent from `<head>`, OR
             (b) `<meta name="viewport">` contains `user-scalable=no` or
             `maximum-scale=1` (prevents pinch-zoom), OR
             (c) The page requires horizontal scrolling at 375px viewport width (content
             overflows the viewport).
Check:       Fetch page (static GET). Parse `<head>` for `<meta name="viewport">`.
             Check content attribute for `user-scalable=no` or `maximum-scale=[<2]`.
             Also emulate 375px viewport width (headless or CSS-computed) and check for
             horizontal overflow. Flag any of (a), (b), or (c).
             Page budget: 2–3 pages (home + 1–2 key inner pages), static fetch for (a)(b),
             render required for (c).
Evidence:    (a) "Missing viewport meta tag — mobile layout cannot adapt to device width."
             (b) "Viewport meta disables user zoom (user-scalable=no). This is a WCAG 1.4.4
             failure and prevents users with low vision from zooming."
             (c) "Page overflows horizontally at 375px viewport width — requires horizontal
             scrolling on standard phone screens."
Severity:    high for (b): zoom blocking is a WCAG 1.4.4 (AA) normative failure with a
             causal link to access obstruction. Hard-mechanical consequence for users who
             depend on zoom. D-004 allows high for hard-mechanical. Medium for (a) and (c):
             detectable structural causes with a normative basis. D-008: frame as access
             defect, not engagement prediction.
FP guard:    (a) Do NOT raise on pages explicitly intended for desktop-only delivery if
             the site consistently serves a separate mobile domain. (b) Do NOT flag
             `minimum-scale=1` — only `maximum-scale` that is too restrictive. (c) For
             horizontal overflow: exclude decorative elements, wide images within a
             scroll container, and maps that are intentionally horizontally scrollable.
Not-measurable: Horizontal overflow requires a CSS-computed layout; if headless rendering
             fails, emit `not_determinable` for (c) only.
Fix:         (a) Add `<meta name="viewport" content="width=device-width, initial-scale=1">`.
             (b) Remove `user-scalable=no` and any `maximum-scale` below 5.
             (c) Fix layout to use responsive CSS (flexbox, grid, or percent widths)
             so content reflows at 375px without overflow.
Beyond-fix:  Test on real devices across iOS (Safari) and Android (Chrome) at multiple
             viewport sizes. Use browser developer tools' responsive mode as a first pass.
Sources:     P-07.15 (Parhi et al., MobileHCI 2006, SEARCH-ONLY — tap-target study;
             WCAG 2.2 SC 2.5.8 24×24 CSS px used as normative threshold); D-008
             (project decision on engagement framing); P-07.01 (McQuade, web.dev, VERIFIED
             — CWV thresholds; mobile accessibility basis).

---

### R-016 — Standalone tap targets below minimum size

Half:        engagement
Mechanism:   E — interactive elements too small for thumb-driven tap create access
             barriers for mobile users. WCAG 2.2 SC 2.5.8 sets a normative minimum of
             24×24 CSS pixels for standalone interactive targets.
Signal:      Standalone interactive elements (`<a>`, `<button>`, `<input>`, `[role=button]`)
             have a rendered bounding box smaller than 24×24 CSS pixels with less than
             24px spacing to the nearest adjacent interactive element.
Check:       Render the page in a 375px mobile viewport (headless). For each interactive
             element that is not inline within body text (standalone: navigation items,
             form controls, icon buttons, call-to-action buttons): measure rendered
             bounding box width and height. Flag elements below 24×24 CSS px that also
             lack 24px spacing to the nearest neighbour (per WCAG 2.2 SC 2.5.8 offset
             exception).
             Page budget: 1–2 pages (home + key conversion page), headless render required.
Evidence:    "N standalone interactive element(s) on [URL] fall below WCAG 2.2 SC 2.5.8
             minimum target size (24×24 CSS px). Examples: [element descriptions]."
Severity:    medium — WCAG 2.2 SC 2.5.8 is a normative criterion, but it is Level AA
             (not A), and the lab evidence (P-07.15) establishes the mechanism for tap
             errors rather than site abandonment. D-004 caps: normative basis → medium.
             D-008: frame as access defect.
FP guard:    (1) Do NOT flag inline links within body text paragraphs — only standalone
             controls. (2) Do NOT flag elements hidden from view (display:none, visibility:
             hidden, off-screen) — measure only visible, interactive elements. (3) Elements
             with the WCAG 2.2 spacing exception (24px of clear space to nearest adjacent
             target) are not a violation.
Not-measurable: If headless rendering is not available within budget, emit `not_determinable`
             for this check.
Fix:         Increase the size of small interactive elements to at least 24×24 CSS pixels
             (44×44 px recommended for comfortable use by most users). For icon-only
             buttons, add padding rather than increasing the icon itself, so the
             clickable/tappable area is large enough.
Beyond-fix:  Adopt the 44×44 CSS px recommendation from Apple HIG and Google Material
             Design for all primary interactive elements, not just the normative minimum.
Sources:     P-07.15 (Parhi et al., MobileHCI 2006, SEARCH-ONLY — target-size study;
             WCAG 2.2 SC 2.5.8 used as the normative threshold); D-007 (tap-target figure
             of 9.2mm not assertable; WCAG normative threshold used instead).

---

### R-017 — Non-descriptive anchor text and navigation labels

Half:        engagement
Mechanism:   E — information scent (P-07.12) is carried by link text; "click here", bare
             URLs, and single-word generic navigation labels give users and machines no
             indication of what the destination contains. Also a WCAG 2.4.4 (Link Purpose,
             AA) criterion.
Signal:      Presence of `<a>` elements with anchor text that is "click here", "here",
             "read more", "learn more", a bare URL string, or a single generic word with
             no surrounding context that provides purpose.
Check:       Fetch 2–3 pages (static GET). Parse all `<a>` elements with visible text
             (text-content not empty). Flag those whose stripped text matches a
             non-descriptive pattern list (case-insensitive): "click here", "here",
             "read more", "learn more", "more", "link", "this", "continue", "download",
             bare URLs (text starts with http). Count as a fraction of all links on the
             page. If more than 10% of links on a page are non-descriptive: flag.
             Page budget: 3–5 pages, static fetch only.
Evidence:    "Page [URL]: N of M links (X%) have non-descriptive anchor text
             (e.g., 'click here', 'read more'). These provide no information scent to
             users or AI retrieval systems scanning the page."
Severity:    medium — WCAG 2.4.4 normative basis (AA) plus information-foraging theory
             (P-07.12, SEARCH-ONLY). D-004: normative basis allows medium; theoretical
             underpinning from SEARCH-ONLY source limits to medium, not high.
FP guard:    (1) A single "read more" link on a card or article excerpt is not a defect
             if the surrounding `<article>` provides the title as context. (2) Icon links
             with appropriate `aria-label` are not non-descriptive. (3) The 10% threshold
             means a page with mostly good link text is not flagged for one or two lazy
             instances.
Not-measurable: Not applicable — this is a static DOM check.
Fix:         Replace generic link text with descriptive text that identifies the destination:
             "Read our enterprise pricing guide" not "Read more." For navigation items,
             add enough specificity that a user can predict the destination content.
Beyond-fix:  Audit navigation labels: single-word items like "Solutions" or "Resources"
             benefit from a short descriptive sub-label or a mega-menu summary to increase
             information scent.
Sources:     P-07.12 (Pirolli & Card, Psychological Review 1999, SEARCH-ONLY —
             information foraging theory; scent carried by proximal cues); WCAG 2.4.4
             (Link Purpose — normative criterion); P-07.06 (WebAIM Million — empty links
             one of the six most common failures).

---

### R-018 — Content-blocking overlay at page load

Half:        engagement
Mechanism:   C/E — an overlay blocking all visible content at load is both an engagement
             defect (obstructs access) and a discoverability defect (a crawler that sees
             only the overlay may not extract the page's main content).
Signal:      A `position: fixed` or `position: absolute` element with a high `z-index`
             (>= 999) that covers >= 50% of the initial viewport area is present in the
             DOM at load, AND the page `<body>` has `overflow: hidden` (scroll-lock),
             AND the element is not a standard cookie-consent / age-gate pattern.
Check:       Fetch page (static GET). Parse DOM for: elements with `position: fixed` +
             `z-index` >= 999. Estimate coverage (CSS-computed width × height as fraction
             of viewport). Check if `body` or `html` has `overflow: hidden`. Classify
             element as: COOKIE-CONSENT (contains keywords: "cookie", "consent", "gdpr",
             "privacy", "accept"), AGE-GATE (contains: "age", "born", "18"), or OTHER.
             Flag only OTHER with >= 50% viewport coverage + scroll-lock.
             Page budget: 2–3 pages, static fetch only.
Evidence:    "An overlay covering approximately X% of the initial viewport with scroll-lock
             is present at load on [URL]. Main content is inaccessible without user
             interaction, which AI crawlers cannot simulate."
Severity:    high — meets all three D-008 severity criteria: deterministic to detect,
             blocks content access for some population (crawlers, users), and has normative
             basis (P-07.11 Google policy; P-07.09 Better Ads Standards). D-004: normative
             policy basis supports high.
FP guard:    (1) ALWAYS whitelist COOKIE-CONSENT and AGE-GATE patterns — these are legally
             required in many jurisdictions. (2) Do NOT flag overlays that are dismissible
             with a visible close control in the accessibility tree (check for `aria-label`
             = "close" / "dismiss" button inside the overlay). (3) Do NOT flag modals that
             are triggered by user interaction (scroll, timer, exit intent) — these are not
             in the initial DOM and our static-fetch check will not see them.
Not-measurable: Timer-triggered and exit-intent modals are explicitly not observable
             read-only. Emit as `severity: info, not_determinable`: "Scroll-triggered or
             exit-intent overlays may exist but cannot be assessed in a read-only audit.
             Review manually."
Fix:         For promotional overlays: move them to be triggered on user interaction
             (scroll to 50%, exit intent, time-on-site) so the initial DOM is clean.
             For content that must gate access (age verification): implement as a proper
             redirect to a dedicated verification page (not an overlay) or use a
             dismissible modal with a clearly visible close button. Never use scroll-lock
             on the body behind a non-dismissible promotional overlay.
Beyond-fix:  For email capture overlays: test whether delayed trigger (e.g., 60 seconds
             on page or scroll-triggered) achieves similar capture rates with lower
             abandonment impact. Refer to P-07.09 findings on tolerated vs. intolerable
             ad experiences.
Sources:     P-07.09 (Coalition for Better Ads, betterads.org, VERIFIED — measured user
             intolerance for intrusive experiences; 30%/50% ad-density thresholds);
             P-07.11 (Google Search Central, VERIFIED — interstitial policy; exemptions
             for legally mandated overlays stated explicitly).

---

### R-019 — Blank first paint: client-side-only content with no loading signal

Half:        engagement
Mechanism:   C/E — a page that delivers a blank white screen until JS hydrates is
             invisible to non-rendering crawlers AND provides the worst-tolerated loading
             experience (P-07.10: blank waits are least tolerated; P-04.10: crawlers
             without JS see nothing).
Signal:      The no-JS HTTP response body contains < 50 words of visible text AND no
             `<noscript>` block with substantive content AND no loading skeleton/spinner
             indicator, while the headless-rendered version contains significant content.
Check:       This check shares the headless render from R-003 (JS-rendering gap). If
             R-003 flags a large gap AND the raw-fetch main-text word count is < 50:
             additionally flag as "blank first paint" with a separate finding. The
             additional signal to check: presence of `<noscript>` with > 50 words.
             Page budget: shared with R-003 headless render.
Evidence:    "Homepage: raw HTTP fetch yielded NNN words; no loading indicator or
             noscript fallback present. Users on slow connections, crawlers, and JS-
             disabled contexts see a blank page until hydration completes."
Severity:    high — two independent mechanisms: access defect (crawlers see nothing) and
             perceived-latency defect (blank first paint is least tolerated loading state
             per P-07.10; causal in lab, 2004 basis). Together these support high under
             D-008 severity rules (deterministic + blocks content + documented basis).
FP guard:    (1) Do NOT raise if a meaningful `<noscript>` block is present with > 50
             words of main content. (2) Do NOT raise if the raw HTML contains a server-
             rendered skeleton with visible `<h1>` and introductory text even if the rest
             loads via JS. (3) Do NOT raise for deliberately minimal one-page apps where
             the JS loads quickly and a spinner is visible.
Not-measurable: If headless rendering fails or times out, emit `not_determinable` for both
             R-003 and this check.
Fix:         Implement server-side rendering (SSR) or static-site generation (SSG) so
             that the primary content is in the initial HTTP response. Add a meaningful
             loading state (skeleton UI or spinner) for any content that must remain
             client-side rendered.
Beyond-fix:  Consider progressive enhancement: ensure the page is usable with JS disabled
             for the core use case (reading key information), even if interactive features
             require JS.
Sources:     P-07.10 (Nah 2004, SEARCH-ONLY — tolerable wait is ~2 s; blank = least
             tolerated); P-04.10 (JS rendering gap, SEARCH-ONLY — AI crawlers don't
             execute JS); P-07.02 (Vodafone A/B test, VERIFIED — server-rendered critical
             HTML improved LCP and engagement outcomes).

---

### R-020 — Auto-playing media with sound

Half:        engagement
Mechanism:   E — auto-playing video or audio with sound is consistently among the least-
             tolerated intrusive experiences, measured across >66,000 consumers in the
             Better Ads research (P-07.09).
Signal:      A `<video>` or `<audio>` element is present with an `autoplay` attribute
             and without the `muted` attribute (or with `muted` removed by JS).
Check:       Fetch page (static GET). Parse DOM for `<video autoplay>` and
             `<audio autoplay>`. Check for absence of `muted` attribute. Flag any match.
             Page budget: 2–3 pages, static fetch only.
Evidence:    "Page [URL]: [N] video/audio element(s) with autoplay and no muted attribute
             detected. Auto-playing media with sound is among the most intolerated
             intrusive experiences per P-07.09."
Severity:    high — the Better Ads Standards are based on a large measured study (>66,000
             consumers), making this one of the few engagement findings with a strong
             measured basis. D-004: while not peer-reviewed (industry consortium),
             methodology is documented and the sample is large; treat as correlational
             (high ceiling).
FP guard:    (1) `<video autoplay muted>` is the correct pattern for background videos and
             is NOT a defect. (2) `autoplay` on a `<video>` inside a `<details>` that is
             not `open` at load time is not a defect. (3) User-triggered media players
             (inside a click-handler or hidden by default) are not autoplay in the
             engaged-user sense, but are in the DOM sense; flag conservatively and note
             the uncertainty.
Not-measurable: JS-triggered autoplay (added dynamically after load) is not detectable
             in static DOM. Emit: "Audio/video autoplay via JavaScript cannot be assessed
             read-only; manual review recommended."
Fix:         Add the `muted` attribute to all `<video autoplay>` elements. Do not
             autoplay audio at all. For promotional videos, use a poster image with a
             visible play button as the default state.
Beyond-fix:  Provide `<track kind="captions">` for all video with meaningful audio content
             (accessibility benefit and WCAG 1.2.2).
Sources:     P-07.09 (Coalition for Better Ads, betterads.org, VERIFIED — >66,000 consumers
             across countries; auto-play with sound among most intolerated experiences).

---

### R-021 — Structural CLS causes: images and iframes without intrinsic dimensions

Half:        engagement
Mechanism:   E — images without explicit width/height or aspect-ratio allow layout shifts
             as they load, degrading perceived stability. The page-side structural causes
             of CLS are observable read-only.
Signal:      `<img>` elements without both a `width` and `height` attribute (or an
             `aspect-ratio` CSS property), or `<iframe>` elements without explicit
             dimensions, present on content pages. Especially significant when multiple
             such elements appear above the fold.
Check:       Fetch page (static GET). Parse DOM. Count `<img>` elements without both
             `width` + `height` attributes and without `aspect-ratio` in inline style.
             Count `<iframe>` without `width` + `height`. If N >= 3 such elements: flag.
             Page budget: 2–3 pages, static fetch only.
Evidence:    "Page [URL]: N image(s)/iframe(s) lack explicit dimensions (width/height or
             aspect-ratio). These are known structural causes of Cumulative Layout Shift
             (CLS), a Core Web Vitals metric."
Severity:    medium — the structural cause→CLS link is mechanically established (P-07.01
             cites this explicitly). CLS has no perception research behind it (P-07.01
             states this), so the engagement link is theoretical. D-004: theoretical/
             practitioner observation → medium.
FP guard:    (1) Do NOT raise for a single small icon or bullet image. The threshold of
             N >= 3 ensures the finding applies when the pattern is systematic. (2)
             Decorative images with `role="presentation"` or `alt=""` that don't affect
             layout are lower priority; include them in the count but note they may be
             decorative. (3) Do NOT raise if only `<picture>` or `srcset` patterns are
             used (these have responsive dimensions by design).
Not-measurable: CSS-computed dimensions (aspect-ratio defined in an external stylesheet)
             are not accessible in a static-fetch parse; flag only cases where no
             attribute is set in the DOM.
Fix:         Add `width` and `height` attributes to all `<img>` elements matching their
             natural dimensions. Alternatively, set `aspect-ratio: [w/h]` in CSS. For
             `<iframe>`, set width and height or use `aspect-ratio` via CSS.
Beyond-fix:  Use `loading="lazy"` on below-fold images to reduce initial page weight.
             Use modern image formats (WebP, AVIF) with `<picture>` and `srcset`.
Sources:     P-07.01 (McQuade, web.dev, VERIFIED — CWV thresholds; images without
             dimensions explicitly named as CLS structural cause); P-07.02 (Vodafone,
             VERIFIED — image optimisation bundle improved LCP and engagement).

---

### R-022 — Missing primary landmark structure and heading integrity

Half:        engagement
Mechanism:   E — conventional prototypicality (P-07.05) is observable through structural
             conventions. Missing landmark regions (`<main>`, `<nav>`, `<header>`) and
             heading integrity (no `<h1>`, multiple `<h1>`, or heading-level skips) are
             also WCAG failures and reduce both machine readability and user orientation.
Signal:      The page (a) has no `<main>` landmark, or (b) has no `<h1>`, or (c) has
             more than one `<h1>`, or (d) has a heading-level skip (e.g., `<h1>` directly
             followed by `<h4>` with no `<h2>` or `<h3>` in between).
Check:       Fetch page (static GET). Parse DOM. Check: `<main>` presence;
             `<h1>` count (exactly 1); heading-level sequence for skips (e.g., after
             `<h2>`, next heading-type appearing is `<h4>` = skip). Flag any violation.
             Page budget: 3–5 pages, static fetch only.
Evidence:    "Page [URL]: [specific violation: no <main>, no <h1>, multiple <h1>s, or
             heading-level skip (h1→h4)]. This violates structural conventions used by
             assistive technology and web agents for page orientation."
Severity:    medium — heading integrity has a WCAG basis (WCAG 1.3.1, 2.4.6) and a
             prototypicality basis (P-07.05). Missing `<main>` is a structural convention
             issue. D-004: normative + practitioner observation → medium for convention
             failures; high only for normative violations that block access (multiple
             `<h1>` is high-confusion but not access-blocking).
FP guard:    (1) Do NOT raise on single-page or landing-page archetypes where a `<main>`
             is absent by design and structure is carried by other landmarks. (2) Do NOT
             raise for heading-level skips on WYSIWYG-content pages where user-generated
             content drives heading use. (3) Icon-only or app-style pages may legitimately
             lack a `<h1>`.
Not-measurable: Not applicable — static DOM check.
Fix:         Wrap the main page content in a `<main>` element. Ensure exactly one `<h1>`
             per page (the primary topic/title). Fix heading-level skips by using
             `<h2>` before `<h3>` even if visually styled differently via CSS.
Beyond-fix:  Add `<header>` and `<footer>` landmarks, and `<nav>` for navigation regions.
             This improves both accessibility (screen readers) and machine readability
             (web agents using accessibility tree).
Sources:     P-07.05 (Tuch et al., IJHCS 2012, VERIFIED — prototypicality and appeal;
             landmark structure as observable prototypicality signal); P-07.06 (WebAIM
             Million, VERIFIED — heading errors prevalent); P-04.11 (accessibility tree,
             SEARCH-ONLY — heading structure used by web agents).

---

### R-023 — High ad/promo density in the first viewport (mobile)

Half:        engagement
Mechanism:   E — ad density above the published threshold is among the most measured
             intrusive experiences (P-07.09). The 30% mobile / 50% desktop density
             thresholds are published, measurable norms.
Signal:      The first viewport of a mobile-emulated page (375px width) is more than 30%
             occupied by advertisement elements or promotional interstitial banners
             (identified by: third-party ad-network `<iframe>` sources, common ad-slot
             class names, or fixed/sticky promotional banners).
Check:       Render page in 375px mobile viewport (headless). Identify ad/promo elements
             by: `<iframe>` pointing to known ad-network domains, elements with class
             names matching common ad-slot patterns (`ad`, `ad-slot`, `advertisement`,
             `promo-banner`), or fixed/sticky elements with z-index >= 100 that are not
             navigation. Estimate their combined area as a fraction of the 375×667 px
             first viewport. If > 30%: flag.
             Page budget: 1–2 pages, headless render required.
Evidence:    "First viewport (mobile, 375px): approximately X% of the visible area is
             occupied by advertisements/promotional elements. The Better Ads Standards
             threshold is 30% for mobile (measured on >66,000 consumers)."
Severity:    medium — the Better Ads research is large-scale (>66,000 consumers, P-07.09)
             but uses preference and annoyance ratings, not directly measured abandonment.
             D-004: correlational → high ceiling; but the ad-classification step is a
             heuristic with real false-positive risk. Medium is the honest assignment.
FP guard:    (1) Do NOT flag standard in-content ads that are below the threshold
             individually and in total. (2) Cookie-consent banners are not ads.
             (3) Navigation bars are not ads even if they promote features.
             (4) If the site clearly does not serve ads (no third-party iframes, no
             ad-network references), suppress this check as N/A.
Not-measurable: If headless rendering fails, emit `not_determinable`.
Fix:         Reduce the ad area in the first viewport below 30% (mobile) / 50% (desktop).
             Move advertising content below the fold or to sidebar placements.
Beyond-fix:  Review ad formats against the Better Ads Standards prohibited-experience list:
             remove pop-ups, prestitials, and auto-play video with sound regardless of
             density.
Sources:     P-07.09 (Coalition for Better Ads, betterads.org, VERIFIED — >66,000
             consumers; 30%/50% thresholds; specific prohibited experiences).

---

### R-024 — Missing trust signals for commercial and content sites

Half:        engagement
Mechanism:   E — credibility is influenced by identifiable publisher, contact route,
             HTTPS, and dated/attributed content (P-07.13 lower-ranked credibility
             categories). These are also machine-readable signals.
Signal:      A commercial or content-publishing site lacks one or more of: (a) a reachable
             contact page or contact information in the footer (phone, email, or a form
             link), (b) an identifiable organisation name in the footer or About page,
             (c) a valid HTTPS certificate (HTTP or cert error), (d) dated and attributed
             content on pages that are explicitly news or editorial.
Check:       Fetch home page and footer (static GET). Check: (a) presence of email pattern,
             telephone pattern, or `<a href="/contact*">` in footer or nav; (b) organisation
             name in `<footer>` or About-page link; (c) `https://` scheme and no TLS error
             on fetch; (d) for news/editorial pages: presence of `<time>` or date pattern
             in byline area. Gated on archetype: only raise on commercial, service, or
             news/editorial sites. Do NOT raise on personal blogs or portfolio sites.
             Page budget: 2–3 pages, static fetch only.
Evidence:    "Commercial site [domain]: no detectable contact information in footer or nav;
             no identifiable organisation name in footer. These are credibility signals
             expected by users and AI extraction systems for commercial entities."
Severity:    low — the Stanford credibility study (P-07.13) is correlational/descriptive
             (comment frequency, not behavioural outcome). D-004 caps at medium for
             correlational; we assign low given the SEARCH-ONLY status of P-07.13 and
             the interpretive distance from comment mentions to engagement outcomes.
FP guard:    (1) Do NOT raise for personal portfolios, hobby sites, or explicitly
             single-person creative sites — contact info is optional there. (2) Do NOT
             raise for HTTPS if the site is internal-only or under construction. (3) The
             archetype gate is essential; a missing "contact us" link on a documentation
             site for an open-source library is expected, not a defect.
Not-measurable: TLS validity requires an actual HTTPS connection attempt; if the fetch
             times out, emit `not_determinable` for the HTTPS check.
Fix:         (a) Add a contact page or include email/phone in the footer; (b) add the
             organisation name to the footer; (c) migrate to HTTPS and renew the
             certificate before expiry; (d) add author bylines and publication dates to
             news/editorial articles.
Beyond-fix:  Add a privacy policy and terms-of-service link to the footer (also a legal
             requirement in many jurisdictions).
Sources:     P-07.13 (Fogg et al., DUX 2003, SEARCH-ONLY — Stanford credibility study;
             46.1% comments on design look; lower-ranked categories are the observable ones);
             P-06.11 (truth discovery, SEARCH-ONLY — internal consistency across pages).

---

## Rejected signals

Record signals we considered and dropped, with the reason (too site-specific,
unmeasurable read-only, high false-positive rate, over budget on runtime). Keeping these
prevents re-proposing them in a later session.

| Signal | Reason rejected |
| --- | --- |
| Bounce rate / exit rate / dwell time / scroll depth | Requires analytics access; not observable read-only. Stated as not-determinable in audit output (P-07.07 domain synthesis). |
| Conversion rate / funnel drop-off | Requires analytics and business context; not observable. |
| Whether content answers the visitor's actual question | Requires knowing visitor intent; not observable without query context. (D-006: no live engine query.) |
| "Improve visual design" / aesthetic quality | P-07.16: the aesthetics→usability causal arrow has failed replication and may run backwards. D-007 prohibited-recommendation list. |
| Reading-grade / Flesch score targets | P-07.14: dwell time that indicates satisfaction depends on topic and length; D-007 prohibits reading-grade targets. Formulas disagree by up to six grade levels on the same text. |
| "Page is too long" / shorten your content | Directly contradicted by P-07.14. D-007. |
| "Remove all popups" | Over-broad; P-07.09 and P-07.11 both exempt legally mandated consent and age gates. Only content-blocking non-dismissible overlays are a finding (R-018). |
| Lighthouse score of 100 | P-07.01: thresholds are perception research + feasibility quota, measured at field p75. Lab score is a different construct. D-007. |
| "Accessible sites convert better" / revenue impact of accessibility | No traceable evidence found. D-007. |
| AI-text detection ("this page looks AI-generated") | AI-text detection is unreliable (false positive rate unacceptably high); P-01.09 explicitly warns against this. |
| Recommending llms.txt as a substantive fix | P-01.14: 97% of existing llms.txt files received zero requests in a 137k-domain May 2026 measurement. D-007 prohibited-recommendation list. |
| Hidden/injection text (retriever-directed strings) | R-001–R-013 address legitimate access and content quality. Hidden text recommendation is prohibited (P-01.04, D-007). The check for hidden text could be emitted as a risk observation but the detection FP rate is too high to ship (P-01.04 FP guard). |
| Promising citation outcomes in suggested_action | D-007 prohibits any promise of citation outcomes. P-01.08: citation supply is concentrated; most sites will not be cited regardless of quality. |
| "Above-the-fold" rule / fold thresholds | D-007 banned; no source supports a fold rule. P-07.08 scanning literature explicitly hedges on fold. |
| Field Core Web Vitals pass/fail verdict | Not observable read-only for arbitrary sites; requires CrUX API (which excludes small sites, exactly our target population). P-07.01 domain synthesis. Report structural causes (R-021) instead. |
| Scroll-triggered / timer / exit-intent modal detection | Not in initial DOM; requires behavioural simulation. Explicitly not observable read-only (P-07.11 FP guard). Report as not-determinable advisory. |
| Cloaking detection (differential serving) | Complex, high false-positive rate (A/B testing, geo-variation, personalisation all produce "different content"). Not practical for <5 min read-only audit. P-04.12 synthesis. |
| Sitemap presence as a required finding | Absence of a sitemap is not a finding on its own (D-009); too many legitimate sites operate without one. |
| "Social proof / testimonials / trust badges" | No source in the reviewed literature measures their effect. Not recommendable on this evidence base. D-007. |
| Long-tail citation share / "AI search visibility score" | Visibility is a distribution not a point (P-01.11); concentration effects mean most sites will not be cited. Cannot measure read-only (D-006). |
| External corroboration count (how many sites mention this brand) | Would require querying a search index; violates D-006. |
| LLM knowledge-boundary testing (what a model knows about the brand) | Requires querying a live generative engine; violates D-006. |
| Off-site authority / brand mention frequency (vendor-research claims) | No peer-reviewed primary source found; cannot be traced to a citable primary study (P-01 domain synthesis "thin or contested" section). |
| Wikidata presence check | Mechanism is sound (P-06.05, P-06.06), but requires querying Wikidata API during audit — this is an external API call, not a site-side read. May be added in a future version if external lookup budget is allocated. Currently out of scope. |
