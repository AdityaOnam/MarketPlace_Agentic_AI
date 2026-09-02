# Collection procedure — full detail

Expands the numbered procedure in `SKILL.md`. Every rule here exists to make the bundle
deterministic, politely obtained, and honest about what it could not observe.

## 1. Target resolution

Accept a bare domain or full URL. Try `https://` first; fall back to `http://` only if HTTPS
fails to connect, and record `scheme` accordingly (CHK-E-024 reads it). Follow at most 3
redirects, recording each hop. A redirect loop, or a chain longer than 3, sets
`site.status = "partial"` with reason `redirect_chain_exceeded` and collection continues
from the last successful hop.

The final host after redirects is `canonical_host`. All same-origin decisions use it, so a
site that redirects apex → `www` is not treated as linking off-site to itself.

## 2. robots.txt

Fetch `{origin}/robots.txt` first, always, before any other request.

- `200` → parse. `404` or `410` → `parse_ok: true`, no rules, everything permitted (this is
  the correct reading of an absent file, not an error).
- `5xx`, timeout, or a challenge page → `robots.status = "unavailable"`. **Collection stops
  here.** Without knowing the rules we cannot fetch politely, and guessing permission is not
  acceptable. The bundle is emitted with only `site` and `robots` populated.
- Group `User-agent` lines that share a rule block, per the standard. Record `matched_line`
  for the specific rule that decides root access for each agent.
- Classify each agent via [`ai-crawler-agents.md`](ai-crawler-agents.md).
- Honour `Crawl-delay` when present; it overrides the default 250 ms gap when longer.

## 3. Page discovery

Preference order:

1. Sitemaps declared in `robots.txt`, then `/sitemap.xml`. Follow sitemap indexes one level.
2. If no sitemap: breadth-first same-origin crawl from the homepage, depth ≤ 2, collecting
   URLs only — no fetching beyond what discovery requires.

Cap the inventory at 200 URLs. Discovery is not the audit; it exists to make sampling
representative.

### `page_type` labelling

Assigned from URL path, `<title>`, and structured-data `@type`, in that order of confidence.

| Label | Signals |
| --- | --- |
| `home` | Path is `/` |
| `about` | Path or title contains about, company, who-we-are, team, mission |
| `contact` | Path or title contains contact, support, get-in-touch |
| `product` | `@type` Product/Offer, or path segment product/item/p/shop |
| `category` | Listing page linking ≥ 8 sibling `product` URLs |
| `article` | `@type` Article/BlogPosting/NewsArticle, or a date in the path |
| `documentation` | Path contains docs, api, reference, guide, manual |
| `pricing` | Path or title contains pricing, plans |
| `faq` | `@type` FAQPage, or title contains FAQ |
| `legal` | Path or title contains privacy, terms, cookie, legal, imprint |
| `login` | Path contains login, signin, account, register — **never fetched** |
| `other` | No signal matched |

Ambiguity resolves to the **more specific** label; ties resolve to `other`. A label is a
hypothesis, and downstream suppression rules are written to tolerate a wrong one — no
finding depends on a single page's label being correct.

### `archetype` labelling

Site-level, from the inventory's `page_type` distribution:

| Archetype | Rule |
| --- | --- |
| `ecommerce` | ≥ 5 `product` pages, or any `@type` Offer with a price |
| `documentation` | ≥ 40% of inventory is `documentation` |
| `news_editorial` | ≥ 40% is `article` with distinct dates |
| `saas_marketing` | Has `pricing` and < 5 `product` pages |
| `local_business` | `@type` LocalBusiness, or a postal address plus ≤ 15 total pages |
| `brochure` | ≤ 5 pages total |
| `unknown` | No rule matched — **suppresses every archetype-conditioned check** |

`unknown` is a real answer, not a fallback to be avoided. Guessing an archetype activates
suppression rules that were written for a different kind of site.

## 4. Static sampling and fetch

**Deterministic selection.** Sort the inventory by URL, hash the sorted list to produce
`sampling_seed`, and use that seed for any tie-breaking. Never use wall-clock or unseeded
randomness — `pass^k` stability at k=5 depends on identical page selection across runs.

Quota, up to 20 pages: homepage always; then `about` and `contact` if present; then up to 12
distributed across the remaining types present, proportional to inventory but capped at 4
per type; remaining slots to the largest type. `login` pages are never fetched.

### Per-page extraction

- **Main text**: boilerplate-removed extraction. Set `extraction_ok: false` (not empty
  string) when extraction yields under 20 words from a document over 5 KB — that is a
  signal, and CHK-D-004's guard depends on distinguishing it from a genuinely short page.
- **Structured data**: parse `application/ld+json`, recording `@type` and which fields are
  present. Invalid JSON records the type as `null` with a parse error, never a silent skip.
- **Headings**: level, text, document order — order is needed for CHK-E-022's skip detection.
- **Dates**: `article:published_time`, `article:modified_time`, `<time datetime>`, visible
  date strings, and the `Last-Modified` header, kept as separate fields. Do not collapse
  them; CHK-D-012's guard distinguishes a header timestamp from an authored date.
- **`outbound_profile_links`**: off-origin links appearing in `<header>`, `<footer>`, or
  with `rel="me"`. This is a link inventory only; no off-site request is made at this stage.
- **`trigram_hash`**: word-trigram set hashed for CHK-D-013's Jaccard comparison.
- **`interactive_empty`**: anchors and buttons with no accessible name from text, `alt`, or
  `aria-label`.

## 5. Shared render pass

At most 3 pages: homepage, plus the two highest-quota page types. **One navigation per
page.**

1. Navigate. Wait for network idle or 8 s, whichever comes first.
2. Measure at 375 × 812. Capture overlays, tap targets, ad regions, contrast pairs,
   `document.scrollWidth`, and body scroll-lock.
3. **Homepage only**: resize to 1280 × 800 and re-measure. Resize, never re-navigate — a
   second navigation would roughly double the most expensive stage for evidence no check
   requires.
4. Record `render_ms` per page. Hard timeout 25 s per page; on timeout mark that entry
   `unavailable` and continue to the next.

### Detector definitions

- **Overlay**: `position: fixed|absolute`, `z-index ≥ 999`, covering ≥ 50% of the viewport,
  present at load with no interaction. `dismissible_hint` records `cookie`, `age`, or `none`
  from text content — CHK-E-018's guard suppresses consent and age gates.
- **Tap target**: an interactive element with a rendered box. `standalone: false` when it is
  inline within a text run (WCAG 2.2 SC 2.5.8's exemption). `spacing_px` is the distance to
  the nearest other target.
- **Ad region**, recording which detector fired: `iframe_thirdparty` (cross-origin iframe
  from a distinct registrable domain), `slot_attr` (`data-ad*`, `id`/`class` matching
  `^(ad|ads|advert)[-_]`), `filterlist` (bundled list match). **Report `ad_area_pct_total`
  only from regions where ≥ 2 detectors agree.** Single-detector regions are recorded
  individually so the analyser can see them, but do not contribute to the total — this check
  is the most likely of the 27 to produce false positives.
- **Contrast pair**: foreground/background computed colour, ratio, font size, weight. Only
  for text nodes with a non-empty rendered box.

## 6. Internal links

HEAD, at most 20, sampled deterministically across the fetched pages. Skip fragments,
`mailto:`, `tel:`, `javascript:`, and any path `robots.txt` disallows — each recorded in
`skipped[]` with its reason so CHK-D-009's guard can exclude them. One retry on a network
error, none on an HTTP status.

## 7. Off-site identity anchors

The only off-origin requests in the audit. At most 8, **one per registrable domain**, HEAD
only, 3 s timeout, ≤ 3 redirects. Sourced from `sameAs` in Organization/Person JSON-LD and
from `outbound_profile_links`.

**401, 403, 429 → `resolved: null` with note `bot_blocked_not_broken`.** Never `false`.
These hosts commonly block automated HEAD requests, and reporting that as a dead link would
be a false positive on a perfectly healthy profile. This distinction is encoded in the data
rather than left to the analyser to remember.

## 8. Emission

Populate `budget.stages` with actual timings and abandonment flags. Set each section's
status. Emit. The collector never returns an error to the orchestrator — an unusable site
produces a bundle that says so.
