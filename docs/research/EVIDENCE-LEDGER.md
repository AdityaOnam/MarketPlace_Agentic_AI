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

---

## Discoverability checks

| CHK-ID | Owning skill | Mechanism | Sources | Evidence strength | Observation | Evidence emitted | Severity rule | FP guard | Not-determinable | Suggested action | Runtime | Verified by hand |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CHK-D-001 | marketplace_auditor | A — blocks retrieval-time AI crawlers from indexing | P-01.03, P-01.12 | HARD-MECHANICAL | robots.txt Disallow on root/homepage for GPTBot, PerplexityBot, etc. (1 URL) | `robots.txt line {N}: Disallow: / applies to {agent} (retrieval-time AI crawler).` | critical | IF only training crawlers blocked, emit CHK-D-002 instead. | `robots.txt is unavailable (HTTP {status})` | Remove or narrow the Disallow rule for {agent}. | very-low | AGY (2026-09) |
| CHK-D-002 | marketplace_auditor | A — blocks training-only crawlers | P-01.03, P-01.12 | CORRELATIONAL (low impact) | robots.txt Disallow on training crawlers (CCBot) when no retrieval block | `robots.txt blocks {agent} (a training-corpus crawler) but permits retrieval-time AI crawlers.` | low (informational) | IF CHK-D-001 fires, suppress. | Same as CHK-D-001 | If future parametric memory coverage matters, consider removing the block. | very-low | AGY (2026-09) |
| CHK-D-003 | marketplace_auditor | C — JS-rendering gap hides content from AI | P-04.10, P-04.08, P-04.02 | HARD-MECHANICAL | Token count ratio plain-fetch vs headless render (1 page) | `Homepage: plain HTTP fetch yielded {raw} tokens; headless render yielded {rend} ({pct}% more).` | high if title/h1 missing in raw and >50% gap; medium if >50% gap but title present; low if 20-50% gap | Suppress if <20% gap or if noscript >50 words. | `Headless rendering did not complete.` | Implement SSR or SSG. | high (headless) | AGY (2026-09) |
| CHK-D-004 | marketplace_auditor | C — thin main content | P-04.08, P-04.09, P-01.10 | CORRELATIONAL | Word count of extracted main text < 200 (3-5 pages) | `Page {URL}: main-content extraction yielded {count} words after boilerplate removal.` | medium | Suppress on JS-SPAs if CHK-D-003 fired. Condition on archetype (exclude contact/login). | `Content could not be extracted.` | Add substantive, explicitly-stated content. | low | AGY (2026-09) |
| CHK-D-005 | marketplace_auditor | B/C — absent/generic headings hurt chunking | P-01.13, P-01.10, P-07.08 | THEORETICAL | h2/h3 absent on >500w pages, or generic headings (3-5 pages) | `Page {URL}: {words} words of body text with {h_count} descriptive subheadings.` | low | Exclude legal/FAQ/minimal archetypes. | `not_determinable` if extraction fails. | Add descriptive subheadings. | low | AGY (2026-09) |
| CHK-D-006 | marketplace_auditor | D — missing explicit entity definition | P-01.05, P-06.05, P-06.06, P-01.15 | CORRELATIONAL | Missing sentence with org name + category + function in first 300w (home/about) | `No sentence in the first 300 words explicitly names the organisation, its category, and its function.` | medium | Exclude if title has clear category or CHK-D-007 present. Gated on commercial/org. | `not_determinable` if JS-only. | Add clear declarative sentence naming category and function. | low | AGY (2026-09) |
| CHK-D-007 | marketplace_auditor | D — missing/incomplete Organization JSON-LD | P-06.01, P-06.02, P-01.15 | THEORETICAL / PRACTITIONER | Absence or missing required fields in @type: Organization (home) | `No Organization JSON-LD block found.` OR `Found but missing: {fields}.` | medium | Exclude personal/hobby sites. | `not_determinable` if injected via JS. | Add/complete JSON-LD Organization block. | low | AGY (2026-09) |
| CHK-D-008 | marketplace_auditor | B — duplicate content attribution risk | P-01.06, P-01.07 | CAUSAL | Missing or cross-domain rel=canonical (3-5 pages) | `Page {URL}: no rel=canonical found.` OR `canonical points to {other_domain}.` | medium | Pass if self-referential or valid pagination. | `Redirect chain too deep.` | Add consistent self-referential rel=canonical. | low | AGY (2026-09) |
| CHK-D-009 | marketplace_auditor | B — broken internal links | P-01.06, P-01.07 | THEORETICAL / CORRELATIONAL | 4xx/5xx status of internal links (up to 20 HEAD requests) | `Found {N} broken internal link(s).` | low | Exclude robots.txt blocked paths and fragment links. | `not_determinable` on bot 403. | Repair/remove links; add 301s. | medium | AGY (2026-09) |
| CHK-D-010 | marketplace_auditor | B/C — low extractable-evidence density | P-01.10, P-01.01, P-01.02 | CORRELATIONAL | No definitions, numbers with units, or comparisons across content pages (2-3 pages) | `None of the checked pages contain a definition, numerical fact, or comparison.` | medium | Exclude non-informational pages. Suppress if CHK-D-004 (thin content) fires. | `not_determinable` if extraction fails. | Add explicit definitions, numerical facts, or comparisons. | low | AGY (2026-09) |
| CHK-D-011 | marketplace_auditor | C — pronoun-saturated key claims | P-01.05, P-01.02, P-06.04 | THEORETICAL / HEURISTIC | >60% sentences start with pronoun w/o explicit antecedent (home/about) | `{pct}% of sentences use a pronoun as subject without a preceding explicit mention.` | low | Exclude narrative/blog pages. | `not_determinable` if extraction fails. | Ensure first occurrence of key claims explicitly names the subject. | low | AGY (2026-09) |
| CHK-D-012 | marketplace_auditor | D — missing date signal on time-sensitive content | P-06.08, P-06.09 | THEORETICAL | Missing date in body/meta on TIME-SENSITIVE pages (3-5 pages) | `Page {URL} (time-sensitive) has no detectable publication date.` | low | NEVER raise on EVERGREEN. Suppress if valid Last-Modified header present. | `not_determinable` if page type ambiguous. | Add visible date or article:published_time meta. | low | AGY (2026-09) |
| CHK-D-013 | marketplace_auditor | C — near-duplicate templated thin content | P-01.09, P-06.03 | CORRELATIONAL | Jaccard similarity >0.8 across >=3 pages (4-6 inner pages) | `Pages share {pct}% of word trigrams in their main content.` | low | Exclude legitimate variant pages or legal/ToS pages. | `not_determinable` if extraction fails. | Add unique content answering specific questions for that variant. | medium | AGY (2026-09) |

---

## Engagement checks

| CHK-ID | Owning skill | Mechanism | Sources | Evidence strength | Observation | Evidence emitted | Severity rule | FP guard | Not-determinable | Suggested action | Runtime | Verified by hand |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CHK-E-014 | marketplace_auditor | E — machine-detectable WCAG failures | P-07.06, P-07.07, P-04.11 | HARD-MECHANICAL / NORMATIVE | Missing lang, missing alt, empty links/buttons, unlabelled inputs, low contrast (3-5 pages) | `Page {URL}: {N} accessibility violation(s) of type {type}.` | high (a-e), medium (f contrast) | `alt=""` is correct for decorative. | `not_determinable` for contrast on JS-SPA. | Standard WCAG fixes per violation type. | low | AGY (2026-09) |
| CHK-E-015 | marketplace_auditor | E — viewport blocking | P-07.15, P-07.01, WCAG 1.4.4 | HARD-MECHANICAL / NORMATIVE | Missing viewport meta, user-scalable=no, max-scale<2, horizontal overflow (2-3 pages) | `Missing viewport meta` / `disables user zoom` / `horizontal scroll` | high for zoom block; medium for missing meta / overflow | Exclude desktop-only sites. Exclude minimum-scale=1. | `not_determinable` for overflow if headless fails. | Add standard viewport meta; remove zoom blocks; fix responsive CSS. | low/high | AGY (2026-09) |
| CHK-E-016 | marketplace_auditor | E — small tap targets | P-07.15, WCAG 2.2 | NORMATIVE | Standalone targets < 24x24 CSS px (1-2 pages) | `{N} standalone interactive elements are below WCAG 2.2 SC 2.5.8 minimum.` | medium | Exclude inline text links and spaced targets. | `not_determinable` if headless fails. | Increase target size or padding to >= 24x24 px. | high (headless) | AGY (2026-09) |
| CHK-E-017 | marketplace_auditor | E — non-descriptive anchor text | P-07.12, WCAG 2.4.4, P-07.06 | NORMATIVE / THEORETICAL | >10% of links use "click here", "read more", etc. (2-3 pages) | `{N} links ({pct}%) have non-descriptive anchor text.` | medium | Exclude aria-labeled links. | n/a | Use descriptive link text. | low | AGY (2026-09) |
| CHK-E-018 | marketplace_auditor | C/E — content-blocking overlay at load | P-07.09, P-07.11 | HARD-MECHANICAL / NORMATIVE | Fixed/absolute element with z-index >= 999 covering >= 50% viewport + body scroll lock (2-3 pages) | `An overlay covering ~{pct}% of viewport with scroll-lock is present at load.` | high | Suppress COOKIE-CONSENT / AGE-GATE. | `not_determinable` for scroll-triggered modals. | Trigger overlays via user interaction; remove scroll-lock. | low | AGY (2026-09) |
| CHK-E-019 | marketplace_auditor | C/E — blank first paint | P-07.10, P-04.10, P-07.02 | HARD-MECHANICAL / CAUSAL | JS-rendering gap (CHK-D-003) >= 0.5 + no noscript fallback + no skeleton | `Homepage: plain HTTP fetch yielded {words} words; no loading indicator or noscript present.` | high | Suppress if noscript >50w or skeleton UI present. | `not_determinable` if headless fails. | Implement SSR/SSG or meaningful loading state. | low (shared) | AGY (2026-09) |
| CHK-E-020 | marketplace_auditor | E — autoplaying media with sound | P-07.09 | CORRELATIONAL / NORMATIVE | `<video autoplay>` or `<audio autoplay>` w/o muted attribute (2-3 pages) | `{N} video/audio element(s) with autoplay and no muted attribute.` | high | `video autoplay muted` is fine. | `not_determinable` if added via JS dynamically. | Add `muted` to video; remove autoplay from audio. | low | AGY (2026-09) |
| CHK-E-021 | marketplace_auditor | E — structural CLS causes (missing dimensions) | P-07.01, P-07.02 | THEORETICAL / HARD-MECHANICAL | `<img>`/`<iframe>` without width+height/aspect-ratio (2-3 pages) | `{N} image(s)/iframe(s) lack explicit width/height or aspect-ratio.` | medium | Require N>=3. Exclude responsive `<picture>` tags. | `not_determinable` for CSS-computed dimensions. | Add width/height attributes or CSS aspect-ratio. | low | AGY (2026-09) |
| CHK-E-022 | marketplace_auditor | E — missing landmark/heading integrity | P-07.05, P-07.06, P-04.11 | NORMATIVE / PRACTITIONER | Missing `<main>`, multiple/zero `<h1>`, heading skips (3-5 pages) | `Violation: {description}. Violates structural conventions.` | high (no h1), medium (skips/missing main) | Exclude skips on user-generated content pages. | n/a | Add `<main>`, ensure exactly one `<h1>`, fix heading skips. | low | AGY (2026-09) |
| CHK-E-023 | marketplace_auditor | E — ad/promo density >30% on mobile | P-07.09 | CORRELATIONAL / NORMATIVE | Ad element area >30% in 375px viewport (1-2 pages) | `First viewport: ~{pct}% of visible area occupied by advertisements.` | medium | Suppress if no ads detected site-wide. | `not_determinable` if headless fails. | Reduce ad density; move ads below fold. | high (headless) | AGY (2026-09) |
| CHK-E-024 | marketplace_auditor | E — missing trust signals | P-07.13, P-06.11 | CORRELATIONAL | Missing contact info, org name, HTTPS, or byline dates on commercial/news sites (2-3 pages) | `Commercial site: no detectable {signal}.` | low | ONLY apply to commercial/service/news. Exclude personal/hobby. | `not_determinable` for HTTPS timeout. | Add contact info, org name in footer, HTTPS, bylines. | low | AGY (2026-09) |

---

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
