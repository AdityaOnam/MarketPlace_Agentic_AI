# Check reference — render-extractability-audit

Full per-check detail for the seven checks this skill owns. Sourced directly from
`docs/research/EVIDENCE-LEDGER.md`; if the two ever disagree, the ledger wins and this file
is stale.

---

## CHK-D-003 — Raw-fetch content gap vs. rendered DOM

- **Mechanism**: C — a JS-rendering gap hides content from a non-rendering AI fetch.
- **Strength**: `HARD-MECHANICAL`. Ceiling: `critical`.
- **Reads**: `pages[].main_text_words`, `pages[].headings` (for the raw h1 count) vs.
  `rendered[].main_text_words`, `rendered[].h1_count`, homepage only.
- **Severity rule** (definitional, not threshold-fitted — see R-2):
  - `critical` — raw HTML has no h1 **and** &lt;50 words of main text, while the rendered
    DOM has ≥200 words. The content is categorically absent from what a non-rendering
    fetch receives.
  - `medium` — h1 present in raw, but ≥60% of main text is render-only.
  - `low` — 20–60% of main text is render-only.
  - Below 20%: not a finding.
- **Evidence**: `Homepage: raw HTTP fetch contains {raw} words of main text and {h1_raw}
  h1; rendered DOM contains {rend} words and {h1_rend} h1.`
- **FP guard**: suppress if the gap is &lt;20%, or if `noscript.words > 50` (a working
  fallback already exists).
- **Not-determinable**: `rendered.status != "ok"` → `Rendered page evidence unavailable.`
- **Action**: implement server-side rendering or static generation for the homepage; at
  minimum ensure primary content and the h1 are present in the initial HTTP response.
- **Runtime**: high (reads the shared render pass; adds no cost of its own).
- **Downstream**: consumed by `audit-orchestrator` for `CHK-E-019` root-cause dedup — see
  `SKILL.md`'s "When to use".

## CHK-D-004 — Thin main content

- **Mechanism**: C — thin main content gives an assistant nothing to extract or quote.
- **Strength**: `CORRELATIONAL`. Ceiling: `medium`.
- **Reads**: `pages[].main_text_words`, `page_type`, per sampled page (3–5).
- **Severity rule**: `medium` if `main_text_words < 200` after boilerplate removal.
- **Evidence**: `Page {URL}: main-content extraction yielded {count} words after
  boilerplate removal.`
- **FP guard**: exclude `page_type` in `{contact, login}`. **Suppress if `CHK-D-003`
  fired** on a JS-SPA — the thinness is already explained by the render gap.
- **Not-determinable**: `extraction_ok == false` → `Content could not be extracted.`
- **Action**: add substantive, explicitly-stated content — not padding, not a redesign;
  a paragraph of real prose naming the specific facts the page exists to convey.
- **Runtime**: low.

## CHK-D-005 — Absent or generic headings

- **Mechanism**: B/C — missing structural headings hurt chunking, both for a crawler
  splitting a page into passages and for a human scanning it.
- **Strength**: `THEORETICAL`. Ceiling: `low`.
- **Reads**: `pages[].headings`, `main_text_words`, on pages &gt;500 words (3–5 pages).
- **Severity rule**: `low` if no h2/h3 present, or headings are generic
  (e.g. "More", "Details") rather than descriptive.
- **Evidence**: `Page {URL}: {words} words of body text with {h_count} descriptive
  subheadings.`
- **FP guard**: exclude legal, FAQ, and other minimal-content archetypes where flat
  structure is the genre norm.
- **Not-determinable**: extraction failure → `not_determinable`.
- **Action**: add descriptive subheadings that state the fact or topic of each section,
  not a table of contents label.
- **Runtime**: low.

## CHK-D-009 — Broken internal links

- **Mechanism**: B — a broken internal link is a dead end for both a crawler following
  links to build its index and a user following a citation back to the source.
- **Strength**: `THEORETICAL/CORRELATIONAL`. Ceiling: `low`.
- **Reads**: `links.results[].http_status`, `links.skipped[]` (up to 20 HEAD checks,
  already executed by the collector).
- **Severity rule**: `low` if `count(results[].http_status in {4xx, 5xx}) > 0`.
- **Evidence**: `Found {N} broken internal link(s).`
- **FP guard**: entries already in `links.skipped[]` (robots-disallowed, fragment,
  `mailto:`, budget-cut) are excluded — they were never checked, not found broken.
- **Not-determinable**: a link's own status is `403` from a bot-challenge origin →
  `not_determinable` for that link specifically, not counted as broken.
- **Action**: repair the link's target or replace it; if the target is genuinely gone,
  add a 301 redirect rather than leaving a dead end.
- **Runtime**: medium (reads collector output only; no cost here).

## CHK-D-010 — Low extractable-evidence density

- **Mechanism**: B/C — an assistant favors pages it can quote a clear fact from. A page
  with no definitions, numbers, or comparisons has nothing quotable.
- **Strength**: `CORRELATIONAL`. Ceiling: `medium`.
- **Reads**: `pages[].main_text`, scanned for a definitional sentence pattern, a number
  with a unit, or an explicit comparison (2–3 content pages).
- **Severity rule**: `medium` if none of the three evidence shapes appear anywhere on the
  page.
- **Evidence**: `None of the checked pages contain a definition, numerical fact, or
  comparison.`
- **FP guard**: exclude non-informational page types (contact, login). **Suppress if
  `CHK-D-004` fired** — a page already flagged as too thin doesn't need a second, more
  specific content complaint layered on top.
- **Not-determinable**: extraction failure → `not_determinable`.
- **Action**: add explicit definitions, numerical facts, or comparisons — the shapes an
  assistant can lift verbatim into an answer.
- **Runtime**: low.

## CHK-D-011 — Pronoun-saturated key claims

- **Mechanism**: C — a claim whose subject is a pronoun with no preceding explicit
  mention is ambiguous outside its original context, exactly the form a machine reader
  extracting isolated passages loses.
- **Strength**: `THEORETICAL/HEURISTIC`. Ceiling: `low`.
- **Reads**: `pages[].main_text`, home/about pages only.
- **Severity rule**: `low` if &gt;60% of sentences open with a pronoun lacking a preceding
  explicit antecedent in the same passage.
- **Evidence**: `{pct}% of sentences use a pronoun as subject without a preceding
  explicit mention.`
- **FP guard**: exclude narrative/blog page types, where referential prose is the
  expected register.
- **Not-determinable**: extraction failure → `not_determinable`.
- **Action**: ensure the first occurrence of each key claim explicitly names its subject
  before any pronoun stands in for it.
- **Runtime**: low.

## CHK-D-013 — Near-duplicate templated thin content

- **Mechanism**: C — pages that are near-identical templated shells carrying little
  unique text give an assistant nothing to distinguish between them, and read as thin
  content repeated rather than substantive content once.
- **Strength**: `CORRELATIONAL`. Ceiling: `medium`, scored `low` in practice per the
  ledger's severity column below the element-count floor.
- **Reads**: `pages[].trigram_hash`, Jaccard similarity across ≥3 sampled inner pages
  (4–6 pages read to compute it).
- **Severity rule**: `low` if Jaccard similarity &gt;0.8 across three or more pages.
- **Evidence**: `Pages share {pct}% of word trigrams in their main content.`
- **FP guard**: exclude legitimate variant pages (e.g. size/color product variants) and
  legal/ToS pages, where near-identical text is expected and correct.
- **Not-determinable**: extraction failure on any compared page → `not_determinable`.
- **Action**: add unique content to each variant page that answers the specific
  question a reader would have about that variant, rather than relying on a shared
  template alone.
- **Runtime**: medium (hash comparison only; no extra fetch).
