# Crawl & access checks — full logic

Each entry: **trigger** (deterministic condition), **evidence template**,
**why it matters** (mechanism), **fix**.

---

## CR-01 — Site-wide crawl block

**Trigger:** `robots.txt` contains a `User-agent: *` group with `Disallow: /`
and no narrower `Allow` re-opening content paths.
**Severity:** `critical` · confidence `high`
**Evidence:** `robots.txt (HTTP 200) contains "User-agent: *" + "Disallow: /". Every content path is disallowed for general crawlers.`
**Why:** step 1 of the three-step chain (reach → read → extract) fails. The
site cannot appear in any retrieval index, so it can never be cited.
**Fix:** replace the blanket disallow with targeted rules — disallow only
`/admin`, `/cart`, `/api`, and internal search; allow content routes.
Effort `low`, priority `critical`.
**Verify:** `robots.txt` no longer disallows `/`; a fetch of a content URL is
permitted.

---

## CR-02 — AI crawlers specifically blocked

**Trigger:** a `Disallow: /` group naming any of `GPTBot`, `OAI-SearchBot`,
`ChatGPT-User`, `ClaudeBot`, `Claude-Web`, `anthropic-ai`, `PerplexityBot`,
`Google-Extended`, `CCBot`, `Applebot-Extended`, `Bytespider`, `Amazonbot`.
**Severity:** `high` · confidence `high`
**Evidence:** `robots.txt blocks 4 AI crawlers with Disallow: / — GPTBot, ClaudeBot, PerplexityBot, Google-Extended.`
**Why:** these are the fetchers that build answers in assistants. Blocking
them removes the brand from AI answers while leaving classic search intact —
which is why the loss is usually invisible in analytics.
**Fix:** decide the policy deliberately. To be citable, remove the disallow
for retrieval agents (`OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`,
`ClaudeBot`); to stay out of *training* while staying citable, block only
`GPTBot`, `CCBot`, `Google-Extended`, `Applebot-Extended`.
**Note:** flag as `info`, not `high`, if the site shows deliberate opt-out
signals elsewhere (a stated AI policy page). State the trade-off; do not
assume the block was a mistake.

---

## CR-03 — Pages unreachable

**Trigger:** homepage status ≠ 200 → `critical`. Otherwise ≥ 25% of sampled
pages returning 4xx/5xx → `high`.
**Evidence:** `3/8 sampled URLs returned non-200: /pricing 404, /docs 500, /blog 403.`
**Why:** an unreachable page is absent from the index; a 5xx during a crawl
window can drop already-indexed pages.
**Fix:** restore or 301 the broken routes; audit internal links pointing at
them. Effort `low`–`medium`.

---

## CR-04 — Content only exists after JavaScript

**Trigger:** all three, on ≥ 3 sampled pages:
1. raw-HTML word count < 150,
2. ≥ 5 `<script>` tags **or** a known SPA root (`<div id="root">`,
   `id="__next"`, `id="app"` with near-empty body),
3. `<body>` text-to-markup ratio < 5%.

**Severity:** `high` · confidence `high` if ≥ 3 pages, else `medium`
**Evidence:** `5/8 sampled pages return <150 words of text in the raw HTML response while loading 12+ scripts; /pricing returns 38 words and an empty <div id="__next">.`
**Why:** many retrieval fetchers do not execute JavaScript. Whatever is in the
raw response *is* the page as far as they are concerned — so content that is
plainly visible in a browser is invisible to them.
**Fix:** server-render or statically pre-render every indexable route so the
primary copy, headings and key facts are present in the initial HTML. For an
SPA, enable SSR/SSG for content routes; at minimum, inline the core facts and
metadata server-side.
**Verify:** `curl -s <url> | wc -w` returns the real content; the main heading
and key facts appear in view-source.

---

## CR-05 — No sitemap

**Trigger:** `/sitemap.xml` returns non-200 **and** no `Sitemap:` line in
`robots.txt`.
**Severity:** `medium`
**Evidence:** `/sitemap.xml returned 404 and robots.txt declares no Sitemap: directive.`
**Why:** discovery then depends entirely on link-following. Pages not linked
from the homepage within a couple of hops may never be found.
**Fix:** generate `sitemap.xml` with accurate `<lastmod>`, declare it in
`robots.txt`, keep it current in the build.

---

## CR-06 — Canonical missing or wrong

**Trigger:** no `<link rel="canonical">` on ≥ 50% of sampled pages, **or** a
canonical pointing at a different host.
**Severity:** `medium` (cross-host → `high`)
**Evidence:** `6/8 pages have no rel=canonical; /blog/post-1 canonicalises to https://old-domain.com/post-1.`
**Why:** duplicate URLs split signals across variants, and a wrong canonical
hands attribution to another domain entirely.
**Fix:** emit a self-referential absolute canonical on every page; point
variants at one chosen URL.

---

## CR-07 — Missing title / meta description

**Trigger:** empty or absent `<title>`, or absent
`<meta name="description">`, on ≥ 30% of sampled pages. Also fire on titles
duplicated across ≥ 3 pages.
**Severity:** `medium`
**Evidence:** `4/8 pages share the identical title "Home"; 5/8 have no meta description.`
**Why:** these are the highest-confidence one-line summaries a machine has for
what a page is about, and they are what gets shown when it is surfaced.
**Fix:** unique, specific, entity-bearing titles (`<Page> | <Brand>`) and a
1–2 sentence description that states the page's actual claim.

---

## CR-08 — Redirect hygiene

**Trigger:** ≥ 2 hops to reach final URL, or `http://` does not 301 to
`https://`, or www/non-www both serve 200.
**Severity:** `low`
**Evidence:** `http://example.com -> http://www.example.com -> https://www.example.com/ (2 hops); https://example.com/ also returns 200 (no canonical host).`
**Why:** chains lose signal and waste crawl budget; a split host duplicates
every page.
**Fix:** one 301 to a single canonical host+scheme.

---

## CR-09 — noindex on content

**Trigger:** `<meta name="robots" content="...noindex...">` or an
`X-Robots-Tag: noindex` header on a content page.
**Severity:** `critical`
**Evidence:** `/pricing returns header X-Robots-Tag: noindex, so the page is excluded from indexes despite returning 200.`
**Why:** the page is fetched, renders fine, and is still excluded — the
failure mode hardest to notice from the outside.
**Fix:** remove the directive from content routes; keep it on staging, thank-you
and internal-search pages only.

---

## CR-10 — Missing `<html lang>`

**Trigger:** no `lang` attribute on `<html>`.
**Severity:** `low`
**Evidence:** `<html> has no lang attribute on 8/8 sampled pages.`
**Why:** language is used to route content to the right audience and affects
both accessibility tooling and locale-scoped retrieval.
**Fix:** set an accurate BCP-47 value; add `hreflang` if there are locales.
