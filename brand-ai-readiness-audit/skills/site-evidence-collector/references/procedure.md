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

1. Sitemaps declared in `robots.txt`, then `/sitemap.xml`. Follow sitemap indexes one level,
   choosing child sitemaps by **name diversity** (group child file names with digits and
   locale prefixes stripped, then round-robin across groups) rather than by position: a
   757-file index that is mostly per-locale blog files never reaches `sitemap_products`
   under a positional sample, and the classifier then sees only the blog. Sample large
   sitemaps evenly (every Nth entry), not the first N. Keep every child sitemap *name* even
   when it is not fetched — file names such as `sitemap_products_1.xml` are evidence.
   **A `Sitemap:` line is untrusted input** — discard any value that is not an absolute
   `http(s)` URL before requesting it. One real site serves `{{ site.url }}/sitemap.xml`,
   an unrendered template left in the published file; treating that as a URL raises rather
   than degrading.
   **A `<sitemapindex>` lists other sitemaps, not pages.** Each `<loc>` inside it (commonly
   `…/sitemap.xml.gz`) is fetched, decompressed if needed, and its own `<urlset>` `<loc>`
   entries are what enter the inventory. The child sitemap URL itself never does — it is
   XML, and no page-level check can be run against it. `sampling.is_page_url()` enforces
   this as a last line of defence.
2. If no sitemap: breadth-first same-origin crawl from the homepage, depth ≤ 2, collecting
   URLs only — no fetching beyond what discovery requires.

Cap the inventory at 200 URLs. Discovery is not the audit; it exists to make sampling
representative. **Discard `asset` URLs (see the `page_type` table below) before they count
against the cap** — a sitemap that mixes in media/image URLs would otherwise let them crowd
out real pages ahead of the 200-URL limit.

### `page_type` labelling

Assigned from URL path, `<title>`, and structured-data `@type`, in that order of confidence.

| Label | Signals |
| --- | --- |
| `asset` | Path ends in a non-HTML extension (image, stylesheet, script, font, document, archive, media). Checked before every other rule, since a sitemap commonly lists media URLs alongside real pages and a path like `/api/media/file/x.png` would otherwise match the `documentation` rule on `/api/`. Never sampled for fetch; excluded from every `archetype` proportion below |
| `home` | Path is `/` |
| `about` | Path or title contains about, company, who-we-are, team, mission |
| `contact` | Path or title contains contact, support, get-in-touch |
| `product` | `@type` Product/Offer/AggregateOffer/ProductGroup, or path segment `products?`, `items?`, `shop`, `dp`, `itm`, `ip`, `listing`, `sku`, `pd`, or `/p/<id-with-digits>` |
| `category` | `@type` CollectionPage/ItemList, or path segment `collections?`, `categor(y\|ies)`, `store`, `browse`, `catalog(ue)?`, `departments?`, `brands?`, `shop-by`, `all-products`, `new-arrivals`, or `/cp/<slug>/<digits>` |
| `article` | `@type` Article/BlogPosting/NewsArticle (and the NewsArticle subtypes, Report, ScholarlyArticle), a `/YYYY/MM/` date in the path, or path segment `blog`, `news`, `articles?`, `posts?`, `stories`, `press`, `newsroom`, `magazine`, `opinion`, `insights?`, or a section word (politics, business, sports, world, tech, health, lifestyle, science, culture, travel, entertainment) |
| `documentation` | `@type` TechArticle/APIReference/HowTo; path segment `docs?`, `documentation`, `api(s)?`, `reference`, `manual`, `handbook`, `guides?`, `tutorials?`, `how-?to`, `kb`, `knowledge-?base`, `help-?center`, `developers?`, `dev`, `sdk`, `cli`, `getting-started`, `quickstart`, `specs?`, `functions?`, `commands?`, `methods?`, `configuration`, `installation`, `troubleshooting`, `changelog`, `release-notes`, `en/latest`, `en/stable`; or a `docs.`, `documentation.`, `developer(s).`, `kb.`, `wiki.`, `manual.` host (`api.` and `help.` are **not** docs hosts — they serve whole storefronts and support portals); or a `/wiki/` path (reference content, kept under this label for suppression purposes) |
| `pricing` | Path segment `pricing`, `plans`, `fees`, `compare-plans` (or a `-pricing`/`-fees` suffix); title only when it *is* a pricing page ("Pricing", "Plans & Pricing"). Never an unanchored substring — `/news/gpu-pricing-…` is an article |
| `faq` | `@type` FAQPage, or path/title contains FAQ / frequently-asked |
| `legal` | Path or title contains privacy, terms, cookie, legal, imprint, impressum, tos, accessibility-statement |
| `login` | Path contains login, signin, signup, account, register, auth, password — **never fetched** |
| `other` | No signal matched |

Ambiguity resolves to the **more specific** label; ties resolve to `other`. A label is a
hypothesis, and downstream suppression rules are written to tolerate a wrong one — no
finding depends on a single page's label being correct.

### `archetype` labelling

Site-level. Decided by **additive evidence scoring**, not by a first-match rule table
(D-035, 2026-09-12): every archetype accumulates weighted evidence from five independent
families, explicit counter-evidence subtracts, and the top score wins only with a margin.
`page_classifier.classify_archetype_detailed` returns the label, a confidence and the
evidence that decided it.

| Family | Weight | What counts |
| --- | --- | --- |
| identity | 4–6 | who runs the site: organisation `@type`s on home/about (NewsMediaOrganization, Store/OnlineStore, SoftwareApplication, LocalBusiness family, EducationalOrganization/GovernmentOrganization/NGO), `.edu`/`.gov` TLD, commerce or docs platform `generator`, `docs.`/wiki hosts, `Person`/`ProfilePage` with **no** Organization entity anywhere |
| affordances | 2–4 | what the site invites: cart/basket link, pricing page + trial/demo/signup CTAs, order/menu/locations, post-a-job / become-a-seller, donate/volunteer |
| structure | ≤ 4 | what the inventory is made of — proportions over the **inventory** (discovered URLs plus same-origin links on fetched pages), never over the fetched sample; article share is capped at 3 so a blog section is evidence, not a verdict; sitemap file names (`sitemap_products`, `post-sitemap`) |
| sampled content | ≤ 2 | what fetched pages are (priced Offers, article-typed pages with dates, MedicalWebPage, JobPosting/Event/SearchResultsPage, single-Person authorship) — **discounted when the inventory does not back it**, because the static sample is stratified by page type and over-represents small sections such as `/docs/` |
| vocabulary | ≤ 3 | weighted keyword sets scored over titles, meta/og descriptions, visible text, raw HTML (hydration data survives a JS shell), robots.txt Disallow paths and sitemap names; a label only scores when a *core activity term* is present (a recipe site full of "pizza" and "menu" never says "order online"); English-centric |

Counter-evidence is explicit: commerce identity subtracts from news/saas/personal; pricing
or software identity from news/personal/docs; institutional identity from news/saas;
"author is a Person with no Organization" from news; third-party listings from saas; any
Organization entity from personal.

Decision: top score ≥ 3.0 and top − second ≥ 1.0. Confidence = 0.5 + 0.25·min(top, 12)/12 +
0.15·min(margin, 6)/6, clamped to 0.55–0.90 — derived from evidence strength and
separation, never assigned per rule. `unknown` is returned for insufficient evidence
**and** for a near-tie, with the reason naming both sides (`ambiguous: news_editorial 6.5
vs reference 6.0 […]`), so a report reader sees what the site is torn between.

| Archetype | Meaning |
| --- | --- |
| `ecommerce` | sells its own catalogue: product/category paths, cart, priced Offers, commerce platform |
| `saas_marketing` | markets software or a service: pricing page, trial/demo/signup CTAs, SoftwareApplication, no cart |
| `news_editorial` | a publisher: NewsMediaOrganization, dated article inventory |
| `documentation` | docs/tutorials/reference: docs host or generator, documentation-path share, self-declared tutorials |
| `local_business` | a place you visit: LocalBusiness-family `@type` on home/about, menu/locations/order affordances |
| `brochure` | ≤ 8 pages, homepage links to them, no structural evidence of anything else |
| `reference` | encyclopaedic lookup: `/wiki/` paths, wiki host, MedicalWebPage/DefinedTerm content, reference-shaped paths |
| `institutional` | university, government, foundation, NGO, open-source project: institutional `@type`s, `.edu`/`.gov`, donate/mission/admissions paths |
| `marketplace` | third-party inventory: JobPosting/Event/SearchResultsPage/Flight listings, LocalBusiness entities only on listing pages of a large site, user-profile paths, many distinct Person entities, seller/employer/host CTAs |
| `personal` | one individual's site: Person/ProfilePage identity with no Organization entity, single author across articles, first-person self-description on home/about, `rel=me`/profile links |
| `unknown` | insufficient evidence, a near-tie, a bot wall, a JS shell with no links, or nothing fetched — **suppresses every archetype-conditioned check** |

Before any evidence is read, a fetched page whose text is an access-denied / captcha /
"enable JavaScript to run this app" wall is dropped: a 200 response can still be a bot
wall, and a bot wall carries no evidence about the site.

Downstream only two groupings change behaviour: the commercial set (`ecommerce`,
`saas_marketing`, `news_editorial`, `local_business`) enables CHK-E-024 and the personal
set suppresses CHK-D-006/007/025. `reference`, `institutional` and `marketplace` are in
neither and behave like `documentation`.

`unknown` is a real answer, not a fallback to be avoided. Guessing an archetype activates
suppression rules that were written for a different kind of site. Where the audit could
not see the site, the reason says so (`bot_blocked_page`, `homepage_no_links`,
`discovery_starved`, `no_pages_fetched`).

## 4. Static sampling and fetch

**Deterministic selection.** Sort the inventory by URL, hash the sorted list to produce
`sampling_seed`, and use that seed for any tie-breaking. Never use wall-clock or unseeded
randomness — `pass^k` stability at k=5 depends on identical page selection across runs.

Quota, up to 20 pages: homepage always; then `about` and `contact` if present; then up to 12
distributed across the remaining types present, proportional to inventory but capped at 4
per type; remaining slots to the largest type. `login` pages are never fetched.

### What counts as a page

A sampled URL becomes an auditable `pages[]` entry **only** when the response is `2xx`,
the `Content-Type` is HTML (`text/html` or `application/xhtml+xml`), and the body is
non-empty. Anything else — a `404` left in a stale sitemap, a `3xx` whose body is a
redirect stub, an XML or PDF resource, an empty response — is recorded with
`status: "unavailable"`, the `http_status`, a `reason`, and `extraction_ok: false`, and
**no check is evaluated against it**. `extract_page()` applies this itself; do not bypass
it by handing it a body from a failed request. Found on weebly.com (a 404 and an empty
302 in the sitemap each produced four findings) and developer.mozilla.org (three child
sitemaps graded for `<h1>` and viewport meta).

Always follow redirects (max 3, per §1) and record the post-redirect URL as `final_url`.
Findings are located at `final_url`, so `/about` → `/in/about` is reported where the
content actually is.

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

**If `headless_browser` is not among this run's available tools, skip this step entirely —
do not attempt a workaround, and do not infer rendered values from static HTML.** This is
structurally different from a per-page timeout: it is known before collection starts, not
discovered mid-run. Emit `rendered: []` and record it in `budget.stages` as its own entry:
`{"name": "render_pass", "budget_s": 75, "actual_s": 0, "abandoned": true,
"completed_items": 0, "planned_items": <= 3, "reason": "No headless browser tool available
in this environment."}`. **This stage entry must be recorded even though no time was
spent** — its purpose is to make the gap visible in `degraded_stages[]` downstream, not to
account for elapsed time. Without it, the seven checks that read `rendered[]` disappear
from the report silently (they resolve to `not_determinable`, which is dropped before the
report is assembled) rather than being declared as an unmeasured gap.

Otherwise, at most 3 pages: homepage, plus the two highest-quota page types. **One
navigation per page.**

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
