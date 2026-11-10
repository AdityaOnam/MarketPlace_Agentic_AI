# 05 — Check-by-check Q&A

All 32 checks, one entry each. Format: **what it detects → when it fires → strength/severity
→ the guard that keeps it quiet → the action it suggests.**

Source of truth for the set: `CHECK_TITLES` in
`skills/audit-orchestrator/scripts/compose_report.py` (32 entries). Per-check rules:
`docs/research/EVIDENCE-LEDGER.md` and each analyser's `references/checks.md`.

**Numbering note.** IDs are a single global sequence — `CHK-D-001`…`D-013`, then
`CHK-E-014`…`E-024`, then `CHK-D-025`…`D-027`, then `CHK-D-029`…`D-034`. The `D`/`E` letter
denotes which half of the brief the check serves, **not** a per-half counter. IDs are stable
and never reused, because renumbering would invalidate every gold label keyed to them.
`CHK-E-023` was cut and `CHK-D-028` was never issued.

---

## `crawl-access-audit` (2)

### CHK-D-001 — Retrieval-time AI crawler blocked at root
**Detects:** a robots.txt rule that stops answer-time assistants from fetching the site.
**Fires when:** any `retrieval` or `hybrid` agent has `allowed_root: false`.
**Strength/severity:** `HARD-MECHANICAL` → **critical**. The consequence is definitional, not
statistical — a disallowed path is not fetched — so no effect size is required.
**Guard:** silent when only `training` agents are blocked, or when the block is on a path
other than root (a site restricting `/admin` is behaving correctly).
**Action:** name the specific agent and line, and recommend **narrowing** the rule to the
paths that actually need protection — not deleting the file.
**Measured:** precision 1.00, recall 1.00, clean-site FP 0.00 (after the RFC 9309 fix, D-031).

### CHK-D-002 — Training-corpus crawler blocked, retrieval intact
**Detects:** a block on corpus crawlers while answer-time access is fine.
**Fires when:** a `training` agent has `allowed_root: false` **and** D-001 did not fire.
**Strength/severity:** `CORRELATIONAL` (low impact) → **low**, informational.
**Guard:** suppressed entirely if D-001 fired.
**Action:** state plainly that this is **frequently intentional and not necessarily a
defect**; note only that it forgoes future parametric-memory coverage, and leave the decision
with the owner.

---

## `content-engagement-audit` (17)

### CHK-D-003 — Primary content and h1 missing from raw HTML (JS-render gap)
**Detects:** content that exists only after JavaScript runs, so a non-rendering fetch
receives nothing.
**Fires when:** *two-sided* — raw HTML has no `<h1>` and <50 words of main text while the
rendered DOM has ≥200. *One-sided (D-015, no browser)* — raw HTML has no `<h1>` and <50
words, **capped one severity tier lower** because it proves the static fetch is empty, not
that a render gap caused it.
**Strength/severity:** `HARD-MECHANICAL` → ceiling **critical**. Definitional, not
threshold-fitted.
**Guard:** suppress if the gap is <20% or `<noscript>` carries >50 words.
**Action:** implement SSR or SSG.

### CHK-D-004 — Thin main content
**Detects:** pages whose extracted main text is too sparse to answer anything.
**Fires when:** main text <200 words after boilerplate removal.
**Strength/severity:** `CORRELATIONAL` → **medium**.
**Guard:** skip contact/login/**home** page types (a homepage is framing, not content —
D-022); self-suppress when D-003 fired on that page. D-030 added a **URL fallback** after a
contact page misfiled as `product` defeated the exclusion.
**Action:** add substantive, explicitly stated content.
**Measured:** precision 0.75, FP 0.33 — three of its remaining disagreements are index/listing
pages sent to adjudication, not a code change.

### CHK-D-005 — Missing or generic subheadings
**Detects:** long pages a machine cannot chunk, because there is nothing to chunk on.
**Fires when:** no descriptive `h2`/`h3` on a page of ≥500 words.
**Strength/severity:** `THEORETICAL` → **low**.
**Guard:** exclude legal / FAQ / minimal-content archetypes.
**Action:** add descriptive subheadings.

### CHK-D-009 — Broken internal links
**Detects:** 4xx/5xx internal links, which strand both crawlers and readers.
**Fires when:** any of ≤20 HEAD-checked internal links returns 4xx/5xx.
**Strength/severity:** `THEORETICAL` / `CORRELATIONAL` → **low**.
**Guard:** exclude robots-disallowed paths and fragment links; `not_determinable` on a bot 403.
**Action:** repair or remove the links; add 301s.

### CHK-D-010 — Low extractable-evidence density *(recommendation-only)*
**Detects:** content with no definitions, numbers with units, or comparisons — nothing an
assistant can quote as a fact.
**Fires when:** none of the checked content pages contains any of the three.
**Strength/severity:** `CORRELATIONAL` → **recommendation-only** (demoted D-022 for firing
too broadly).
**Guard:** exclude non-informational pages; suppressed if D-004 fired; **returns
`not_determinable` for a declared non-English `lang`** (D-031 — its detectors are
English-only, and it had been asserting "no numeric fact" about pages carrying
`Ab 9 €/Monat`).
**Action:** add explicit definitions, numerical facts, or comparisons.

### CHK-D-011 — Pronoun-saturated key claims *(recommendation-only)*
**Detects:** claims whose subject is never named, only referred to.
**Fires when:** >60% of sentences start with a pronoun without a preceding explicit mention,
on home/about pages.
**Strength/severity:** `THEORETICAL` / `HEURISTIC` → **recommendation-only** (D-027 — all
three cited sources were opened by hand and none discusses pronouns or unclear referents; a
genuine evidence gap).
**Guard:** exclude narrative/blog pages.
**Action:** ensure the first occurrence of a key claim explicitly names the subject.

### CHK-D-013 — Near-duplicate templated content *(recommendation-only)*
**Detects:** variant pages that are the same page with a word changed.
**Fires when:** Jaccard similarity >0.8 over word trigrams across ≥3 pages.
**Strength/severity:** `CORRELATIONAL` → **recommendation-only** (D-027 — neither cited
source discusses duplicate/templated content).
**Guard:** exclude legitimate variant pages and legal/ToS templates.
**Action:** add unique content answering the specific question that variant exists for.
**Note:** runs on `pages[].main_text`, not `trigram_hash` — a hash proves identity or
difference, not a similarity *percentage*.

### CHK-E-014 — Machine-detectable accessibility violations
**Detects:** six independently graded WCAG failures — missing `lang`, missing `alt`, empty
links/buttons, unlabelled inputs, plus contrast.
**Strength/severity:** `HARD-MECHANICAL` / `NORMATIVE` → **high** for sub-checks a–e,
**medium** for contrast.
**Guard:** `alt=""` is *correct* for decorative images — test `alt === null`. A hidden
`rel="me"` verification anchor is not an unnamed control (D-029 — it was reading Mastodon
verification links, the very construct `CHK-D-025` asks sites to add).
**Degraded:** the contrast sub-check needs rendered computed styles and reports
`not_determinable` without a browser. The other five survive from static HTML.
**Measured:** precision 1.00, recall 1.00, FP 0.00 after D-029.

### CHK-E-015 — Mobile viewport meta missing or restricting user zoom
**Detects:** `user-scalable=no`, `maximum-scale<2`, a missing viewport meta, or horizontal
overflow at 375 px.
**Strength/severity:** `HARD-MECHANICAL` / `NORMATIVE` (WCAG 1.4.4) → **high** for a zoom
block, **medium** for missing meta or overflow.
**Guard:** exclude desktop-only sites; `minimum-scale=1` is fine.
**Degraded:** the 375 px overflow sub-check needs rendered geometry; only the meta-tag half
survives without a browser.
**Action:** add the standard viewport meta; remove zoom blocks; fix responsive CSS.

### CHK-E-016 — Tap targets below WCAG 2.2 minimum size
**Detects:** standalone interactive elements under **24×24 CSS px** (SC 2.5.8).
**Strength/severity:** `NORMATIVE` → **medium**.
**Guard:** exclude inline text links and adequately spaced targets.
**Degraded:** fully render-dependent — `not_determinable` in the grading sandbox, named in
`degraded_stages[]`. **Kept rather than cut** because it is dead due to an absent tool, not a
weak check.
**Note:** the project deliberately uses WCAG's 24×24 px rather than the cited paper's
9.2 mm figure — and the 9.2 mm figure is on the **prohibited-statistics** list.

### CHK-E-017 — Non-descriptive link text
**Detects:** "click here", "read more", "learn more" as the entire accessible name.
**Fires when:** >10% of links on a page.
**Strength/severity:** `NORMATIVE` (WCAG 2.4.4) / `THEORETICAL` → **medium**.
**Guard:** exclude `aria-label`led links.
**Action:** use descriptive link text.

### CHK-E-018 — Content-blocking overlay present at load
**Detects:** an overlay that covers the content before the visitor has done anything.
**Fires when:** a fixed/absolute element with `z-index ≥ 999` covers ≥50% of the viewport
**and** the body is scroll-locked.
**Strength/severity:** `HARD-MECHANICAL` / `NORMATIVE` → **high**.
**Guard:** **suppress cookie-consent and age-gate overlays** — legal compliance, not a defect.
**Degraded:** render-dependent; `not_determinable` without a browser.
**Action:** trigger overlays on user interaction; remove the scroll lock.

### CHK-E-019 — Blank first paint with no fallback
**Detects:** a plain HTTP fetch that yields nothing, with no loading state and no
`<noscript>`.
**Fires when:** *two-sided* — render gap ≥0.5 with no `<noscript>` fallback and no skeleton.
*One-sided (D-015)* — raw words <50 **and** `<noscript>` words <50.
**Strength/severity:** `HARD-MECHANICAL` / `CAUSAL` → **high**.
**Guard:** suppress if `<noscript>` >50 words or a skeleton UI is present; **suppressed by
D-003 via rule O-1** when both are present.
**Action:** implement SSR/SSG, or a meaningful loading state.
**Supporting evidence:** a loading indicator alone nearly triples patience before abandonment
(13 s → 38 s average wait).

### CHK-E-020 — Autoplaying media with sound
**Detects:** `<video autoplay>` or `<audio autoplay>` without `muted` and with no pause/stop
control.
**Strength/severity:** `NORMATIVE` (WCAG 2.2 SC 1.4.2, Audio Control) → **medium**.
**Guard:** `video autoplay muted` is fine.
**Action:** add `muted` to video; remove autoplay from audio.
**History:** originally `high` on a single study; R-3 re-grounded it on the WCAG SC and
demoted it to `medium`.

### CHK-E-021 — Images/iframes missing dimensions *(recommendation-only)*
**Detects:** `<img>` / `<iframe>` without width+height or `aspect-ratio`, so content reflows
during load.
**Strength/severity:** `THEORETICAL` → capped at **medium**, and shipped
recommendation-only. *The reflow is mechanical; the engagement harm is unevidenced* — Google's
own CLS documentation states the metric has no perception research behind it.
**Guard:** require N≥3; exclude responsive `<picture>` tags.
**Action:** add width/height attributes or CSS `aspect-ratio` to reserve layout space.

### CHK-E-022 — Missing landmark or heading structure
**Detects:** missing `<main>`, zero or multiple `<h1>`, heading-level skips.
**Strength/severity:** `NORMATIVE` / `PRACTITIONER` → **high** for no `h1` on
ecommerce/news/docs, **medium** otherwise, **low** on personal sites; **medium** for other
violations.
**Guard:** exclude heading skips on user-generated-content pages.
**Action:** add `<main>`, ensure exactly one `<h1>`, fix heading skips.

### CHK-E-024 — Missing trust signals *(recommendation-only)*
**Detects:** absent contact info, organisation name, HTTPS, or byline dates on commercial and
news sites.
**Strength/severity:** `CORRELATIONAL`, **single-study** → recommendation-only under D-004.
It may **never** appear in `findings[]` at any severity.
**Guard:** commercial/service/news archetypes only; exclude personal/hobby.
**Action:** add contact info, org name in the footer, HTTPS, bylines.

### ~~CHK-E-023~~ — Mobile ad density *(CUT, D-018)*
Read only `rendered[].viewports.mobile_375.ad_area_pct_total`, which is empty in every graded
run — so it emitted nothing at all, not even a `not_determinable` envelope. It was also
already the ledger's most false-positive-prone row, carrying a two-detector agreement rule no
other check needed. **The row was struck rather than deleted** — a deleted row reads as an
oversight, a struck one reads as a decision.

---

## `entity-identity-audit` (13)

### CHK-D-006 — No explicit organisation-definition sentence
**Detects:** the absence of a sentence in the first 300 words naming the organisation, its
category, and its function.
**Strength/severity:** `CORRELATIONAL` → **medium**.
**Guard:** suppress if the title carries a clear category, or if D-007 is present.
**Action:** add a clear declarative sentence naming category and function.
**History:** the definition regex originally accepted exactly *one* sentence shape and
rejected genuine self-definitions like *"Hugo is one of the most popular open-source static
site generators."* Fixed in D-029: precision 0.57 → 1.00, FP 0.67 → 0.00, **recall 0.73 →
0.55** — the widened pattern buys precision with recall, and both numbers are reported.

### CHK-D-007 — Missing or incomplete Organization JSON-LD
**Detects:** absent `@type: Organization` markup, or present-but-incomplete required fields.
**Strength/severity:** `THEORETICAL` / `PRACTITIONER` → **medium**, capped at `low` by D-022
on base-rate grounds.
**Guard:** exclude personal/hobby archetypes.
**Action:** add or complete the JSON-LD Organization block.
**Measured:** clean-site FP 0.50, **deliberately untouched** — Web Data Commons put
structured data at 44.1% of domains, so "no JSON-LD" is the open web's majority condition.
That is a base rate, not a bug.

### CHK-D-008 — Missing or cross-domain canonical tag
**Detects:** no `rel=canonical`, or one pointing at another domain — duplicate-content
attribution risk, where an assistant cites a syndicated copy over the original.
**Strength/severity:** `NORMATIVE`; `CAUSAL` with sampled duplicate URL variants → **medium**.
**Guard:** pass if self-referential, or a valid pagination canonical.
**Action:** add a consistent self-referential `rel=canonical`.
**Measured:** precision 1.00, recall 0.86, FP 0.00.

### CHK-D-012 — Missing date on time-sensitive content
**Detects:** a time-sensitive page with no detectable publication date.
**Strength/severity:** `THEORETICAL` → **low**.
**Guard:** **NEVER raise on an evergreen page**; suppress if a valid `Last-Modified` header
is present; bias toward evergreen when classification is ambiguous.
**Action:** add a visible date or `article:published_time` meta.

### CHK-D-025 — No declared identity anchors
**Detects:** no `sameAs` declarations and no outbound identity-profile links — so cross-web
corroboration has nothing to attach to.
**Strength/severity:** `CORRELATIONAL` → **medium**.
**Guard:** suppress on personal/hobby/portfolio archetypes; **any one resolvable anchor
passes**.
**Action:** add `sameAs` to the Organization JSON-LD pointing at authoritative external
profiles (public knowledge base, official social accounts, industry or company registry).

### CHK-D-026 — Declared identity anchors do not resolve
**Detects:** declared anchors that are dead, breaking the disambiguation chain.
**Fires when:** a declared anchor URL fails a bounded HEAD (≤8 URLs, 3 s timeout, ≤3
redirects, one per host) **and** a confirming GET also fails.
**Strength/severity:** `HARD-MECHANICAL` → **high** if all anchors fail, **medium** if some do.
**Guard:** **401/403/429 = bot-blocked, never broken** → `not_determinable`, never a finding.
404/405/410/501 from HEAD alone is not enough either. Requires ≥1 anchor to exist, else D-025
fires instead.
**Action:** repair or remove dead anchor URLs.

### CHK-D-027 — Inconsistent organisation identity attributes
**Detects:** the organisation's name, legal name, phone or postal address differing across
JSON-LD, footer and contact page — which actively defeats corroboration.
**Strength/severity:** `THEORETICAL` → **medium** for a name/legal-name conflict, **low** for
formatting variance only.
**Guard:** suppress pure formatting differences — whitespace, punctuation, international
phone prefixes, and legal-entity suffixes (Ltd/Limited/LLC/Inc/Corp/GmbH), **implemented in
code**. Requires ≥2 observed instances.
**Action:** state one canonical form of each attribute and use it identically everywhere.

### CHK-D-029 — Product and offer data for ecommerce pages
Applies only to `ecommerce`. Passes on complete Product/Offer JSON-LD on sampled product
pages. Recommendation-only.

### CHK-D-030 — Software and pricing data for SaaS pages
Applies only to `saas_marketing`. Passes on SoftwareApplication or priced Offer data on the
homepage or pricing page. Recommendation-only.

### CHK-D-031 — Listing data for marketplace pages
Applies only to `marketplace`. Passes on complete Event, ItemList, or JobPosting data on a
listing page. Recommendation-only.

### CHK-D-032 — Article provenance and feed discovery for news sites
Applies only to `news_editorial`. Passes on NewsArticle `headline` + `datePublished` +
`author.name` on sampled articles **plus** an RSS/Atom `<link rel="alternate">` in the head.
Recommendation-only.

### CHK-D-033 — Author identity and feed discovery for personal sites
Applies to the `personal` family. Passes on named Person data, an RSS/Atom head link, and
consistent authorship across sampled articles. Recommendation-only.

### CHK-D-034 — Repository or dataset data for code and data archives
Applies to `reference` / `institutional`, and only when code/data-archive evidence is
present. Passes on SoftwareSourceCode or DataCatalog data. Recommendation-only.

> The RSS/Atom detector reads already-collected `raw_html` — it never makes an additional
> request.

---

## Cross-cutting

### Q. Which checks are render-dependent, and what happens to them?
**A.** Six were originally: `CHK-D-003`, `CHK-E-014` (contrast), `CHK-E-015` (overflow),
`CHK-E-016`, `CHK-E-018`, `CHK-E-019`. Two of them — D-003 and E-019 — **re-derive a
one-sided static signal capped one tier lower**. The other four have no defensible static
proxy and stay `not_determinable`, surfaced through `degraded_stages[]`.

### Q. Why is there a shared render pass rather than one render per check?
**A.** Four checks each implying their own render would alone exceed the 5-minute budget.
They are declared **consumers of a single shared artifact set** (rendered DOM, computed
styles, element geometry, 375 px and desktop captures), at most 3 pages, one render each.

### Q. Which signals were considered and *rejected*?
**A.** AI-text detection, Lighthouse SEO score, field Core Web Vitals verdicts, Wikidata
presence (external API), cloaking detection, scroll depth / bounce rate / dwell time,
reading-grade and Flesch scores, aesthetic quality checks, external brand-mention frequency,
and recommending `llms.txt`. Meta-description tags and sitemap presence on their own are also
deliberately absent. **Each rejection has a documented reason** in the evidence ledger —
which is itself an answer to "what did you choose not to do, and why".
