"""page_type and archetype labelling. Reference: procedure.md §3 tables.

A label is a hypothesis; downstream suppression rules tolerate a wrong one. Ambiguity
resolves to the more specific label, ties resolve to 'other'.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# Ordered most-specific-first so the first match wins ties per "more specific label" rule.
_PATH_TITLE_RULES: list[tuple[str, re.Pattern]] = [
    ("login", re.compile(r"login|signin|sign-in|account|register", re.I)),
    ("legal", re.compile(r"privacy|terms|cookie|legal|imprint", re.I)),
    ("faq", re.compile(r"\bfaq\b", re.I)),
    # "plans" alone is an ordinary English word (rights-of-way improvement plans, floor
    # plans, lesson plans) and false-positived a UK government guidance page as `pricing`
    # -- found in Stage C (2026-09-04). "pricing" is unambiguous enough to stay unanchored;
    # "plans" is anchored to a path segment, the same fix already applied to `documentation`.
    ("pricing", re.compile(r"pricing|/plans(/|$)", re.I)),
    # Path-segment anchored, like the `product` rule below. The unanchored version
    # matched any URL containing "guide", "api", "reference" or "manual" anywhere --
    # which on a real engineering blog matched roughly half of all article slugs and
    # classified the whole site as documentation. Found in Stage B' (2026-09-04).
    ("documentation", re.compile('/(docs?|documentation|api|reference|manual|handbook|guides?)(/|$)', re.I)),
    ("contact", re.compile(r"contact|support|get-in-touch", re.I)),
    ("about", re.compile(r"about|company|who-we-are|team|mission", re.I)),
    ("product", re.compile(r"/(product|item|p|shop)(/|$)", re.I)),
]

_DATE_IN_PATH_RE = re.compile(r"/(19|20)\d{2}[/-]")

# A sitemap.xml commonly lists media/asset URLs alongside real pages (CMS-generated image
# sitemaps, a media API under the same host). These are not pages and must not reach the
# page-type/archetype rules at all: found in Stage C (2026-09-04) when a blog's own media
# API (`/_emdash/api/media/file/*.png`) matched the `documentation` path rule on "/api/"
# and mislabelled 95 of 200 inventory entries, which alone flipped the site's whole
# archetype from `news_editorial` to `documentation`. Checked ahead of every other rule.
_NON_PAGE_EXT_RE = re.compile(
    r"\.(png|jpe?g|gif|webp|svg|ico|bmp|avif|heic|"
    r"css|js|mjs|json|xml|"
    r"pdf|docx?|xlsx?|pptx?|csv|"
    r"woff2?|ttf|eot|otf|"
    r"mp3|mp4|webm|mov|avi|wav|ogg|"
    r"zip|gz|tar|rar)$", re.I
)


def classify_page_type(url: str, title: str | None, json_ld_types: list[str]) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    title = title or ""

    if path == "/" or path == "":
        return "home"

    if _NON_PAGE_EXT_RE.search(path):
        return "asset"

    types_lower = {t.lower() for t in json_ld_types if t}
    if any(t in types_lower for t in ("product", "offer")):
        return "product"
    if any(t in types_lower for t in ("article", "blogposting", "newsarticle")):
        return "article"
    if "faqpage" in types_lower:
        return "faq"

    for label, pattern in _PATH_TITLE_RULES:
        if pattern.search(path) or pattern.search(title):
            return label

    if _DATE_IN_PATH_RE.search(path):
        return "article"

    return "other"


# D-3 (2026-09-12): URL and host patterns that identify a vertical when the page_type
# distribution alone is thin. Personal blogs whose posts have no date in the URL and no
# JSON-LD Article type (danluu.com, jvns.ca, overreacted.io) landed in `other` for every
# post; a docs subdomain (docs.djangoproject.com, developer.mozilla.org) is a docs site
# even with only 3 doc-classified pages in the sample; a blog subdomain
# (blog.cloudflare.com) is editorial even when the sample is stratified across types.
_DOCS_HOST_RE = re.compile(r"^(docs?|documentation|developer|dev|api|wiki)\.", re.I)
_NEWS_HOST_RE = re.compile(r"^(blog|news|posts?)\.", re.I)
_SHOP_HOST_RE = re.compile(r"^(shop|store)\.", re.I)
_BLOG_PATH_RE = re.compile(r"/(blog|posts?|writing|articles?|essays?|notes|journal)/", re.I)
_NEWS_PATH_RE = re.compile(r"/(news|editorial|opinion|column)/|/(19|20)\d{2}/", re.I)
_DOC_PATH_RE = re.compile(
    r"/(docs?|documentation|manual|handbook|reference|guides?|tutorials?)(/|$)", re.I,
)
_SHOP_PATH_RE = re.compile(
    r"/(shop|store|cart|checkout|catalog|catalogue|collections?)(/|$)", re.I,
)


def _urlparts(pages: list[dict]) -> tuple[list[str], list[str]]:
    """Return (hosts, paths) for pages that carry a url. A page without a url (offline
    replay artefact) contributes to neither list."""
    hosts, paths = [], []
    for p in pages:
        u = p.get("url") or ""
        if not u:
            continue
        pu = urlparse(u)
        if pu.netloc:
            hosts.append(pu.netloc.lower())
        if pu.path:
            paths.append(pu.path)
    return hosts, paths


def classify_archetype(pages: list[dict], inventory: list[dict] | None = None) -> tuple[str, float]:
    """pages: list of {'page_type', 'json_ld_types', 'has_price', 'has_postal_address',
    'primary_date', 'url'} for the pages actually fetched. inventory: the full discovered
    URL list (page_type only), used for every rule that is a *proportion* or a site-size
    test.

    Why the split (2026-09-04, Stage B' of the evaluation):

    Every proportion rule below ("40% of the site is documentation", "the site has at most
    5 pages") is a statement about the **site**. They were being evaluated against the
    fetched sample, which `sampling.select_static_sample` deliberately stratifies across
    page types and caps at 4 per type. A stratified sample cannot preserve the proportion
    the rule is asking about -- the sampler exists precisely to flatten it -- so a
    documentation site whose inventory is 95% docs presented as ~25% docs and fell through
    to `unknown`. Measured over 36 real sites, the classifier abstained on 24 of them and
    scored 22% accuracy; the rules were never wrong, they were reading the wrong population.

    Content signals (`has_price`, `json_ld_types`, `has_postal_address`) still come from
    `pages`, because they require a page body that only the fetched sample has.

    Widened 2026-09-12 (D-3): the offline-replay bundle carries an empty `inventory`, so
    the classifier ran on the tiny fetched-page sample and returned `unknown` for 30 of 39
    real sites. `unknown` then disabled every per-archetype exemption downstream (D-006
    told a personal blog to add Organization JSON-LD; D-013's recommendation used
    e-commerce wording on a documentation site). This pass adds URL and host patterns as
    a second population the classifier can read (a docs subdomain is a very strong signal
    even with three fetched pages) plus a `personal` archetype path that was previously
    never emitted, and lowers the doc/news proportion thresholds from 0.40 to 0.30 so the
    classifier does not abstain on a docs site whose sample is 37% docs.
    """
    # No page body was fetched -- the site blocked us, or every sampled URL failed.
    # Every rule below rests on evidence we do not have, and the small-inventory
    # fallback (`total <= 5` -> brochure) would otherwise turn a *blocked* site into a
    # confidently-labelled one. `unknown` is the only honest answer here, and it
    # correctly suppresses every archetype-conditioned check downstream.
    if not pages:
        return "unknown", 0.0

    basis = [p for p in (inventory if inventory else pages) if p.get("page_type") != "asset"]
    total = len(basis)
    if total == 0:
        return "unknown", 0.0

    product_count = sum(1 for p in basis if p.get("page_type") == "product")
    doc_count = sum(1 for p in basis if p.get("page_type") == "documentation")
    article_count = sum(1 for p in basis if p.get("page_type") == "article")
    has_pricing = any(p.get("page_type") == "pricing" for p in basis)
    has_about = any(p.get("page_type") == "about" for p in basis)

    has_offer_price = any(p.get("has_price") for p in pages)
    article_dates = {
        p.get("primary_date") for p in pages
        if p.get("page_type") == "article" and p.get("primary_date")
    }
    is_local_business = any(p.get("json_ld_types") and
                             "localbusiness" in [t.lower() for t in p["json_ld_types"]]
                             for p in pages)
    has_postal_address = any(p.get("has_postal_address") for p in pages)

    # Read URL patterns off the same population the proportion tests use -- the fetched
    # pages are stratified and small (~10 URLs), the inventory is the site (~150 URLs).
    hosts, paths = _urlparts(basis)
    docs_host_hits = sum(1 for h in hosts if _DOCS_HOST_RE.search(h))
    news_host_hits = sum(1 for h in hosts if _NEWS_HOST_RE.search(h))
    shop_host_hits = sum(1 for h in hosts if _SHOP_HOST_RE.search(h))
    blog_path_hits = sum(1 for p in paths if _BLOG_PATH_RE.search(p))
    news_path_hits = sum(1 for p in paths if _NEWS_PATH_RE.search(p))
    doc_path_hits = sum(1 for p in paths if _DOC_PATH_RE.search(p))
    shop_path_hits = sum(1 for p in paths if _SHOP_PATH_RE.search(p))

    # Ordered most-specific-first. `product_count >= 5` alone used to be sufficient at 0.9
    # confidence, on the theory that a single stray price elsewhere was the weak signal to
    # guard against ("an editorial site selling one book is not an ecommerce site"). Stage C
    # (2026-09-04) found the URL-path side has the same problem: `/(product|item|p|shop)/`
    # matches non-commerce catalogues too -- heise.de's free-software download directory
    # uses `/download/product/<name>`, confidently mislabelling a news/editorial site as
    # ecommerce. Real commerce catalogues carry `price` in their Product/Offer JSON-LD
    # near-universally (Google's own rich-results guidelines require it); a catalogue with
    # no price signal anywhere in the fetched sample is exactly the free-item-catalogue case.
    if product_count >= 5 and has_offer_price:
        return "ecommerce", 0.9
    # Docs subdomain is a very strong signal even with a small doc_count in the sample.
    if docs_host_hits >= 1:
        return "documentation", 0.85
    if doc_count / total >= 0.30 or doc_path_hits / total >= 0.35:
        return "documentation", 0.8
    # News/editorial: dated articles, dated-URL patterns, a news/blog subdomain, OR a
    # substantial `/blog/`|`/articles/` URL presence. The last catches plausible.io
    # (161-URL sample, 105 under `/blog/`) and www.docker.com's engineering blog --
    # sites that read as editorial-heavy marketing, not personal blogs.
    if (article_count / total >= 0.30 and len(article_dates) >= 2) or news_host_hits >= 1:
        return "news_editorial", 0.8
    if news_path_hits / total >= 0.35 or blog_path_hits >= max(3, total * 0.05):
        return "news_editorial", 0.7
    if has_pricing and product_count < 5:
        return "saas_marketing", 0.8
    if is_local_business or (has_postal_address and total <= 15):
        return "local_business", 0.75
    # Shop subdomain or a heavy `/shop|/store` URL pattern implies commerce even absent
    # explicit Offer JSON-LD (the price may be render-side).
    if has_offer_price or shop_host_hits >= 1 or shop_path_hits / total >= 0.25:
        return "ecommerce", 0.6
    # Personal / portfolio: has a home + about, no commercial or documentation signals,
    # not a blog-heavy editorial site (that would have matched news_editorial above), and
    # -- the deciding tell -- the URL structure is dominated by top-level single-segment
    # slugs (`/perf-opt/`, `/a-social-filesystem/`, `/what-are-the-react-team-principles`).
    # That top-level slug pattern is the shape of a personal essay blog and is not the
    # shape of a government site (`/government/publications/...`, four segments deep) or
    # a large product site (`/students/2026/`, `/api/reference/...`). The depth guard was
    # added 2026-09-12 after the first pass classified gov.uk and chatgpt.com as personal.
    if has_about and product_count == 0 and doc_count == 0 and not has_pricing \
            and not has_postal_address and not has_offer_price:
        single_segment = sum(1 for p in paths
                             if len([s for s in p.split("/") if s]) <= 1)
        if paths and single_segment / len(paths) >= 0.70:
            return "personal", 0.65
    if total <= 5:
        return "brochure", 0.7

    return "unknown", 0.0
