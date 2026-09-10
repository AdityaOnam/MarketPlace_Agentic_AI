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


def classify_archetype(pages: list[dict], inventory: list[dict] | None = None) -> tuple[str, float]:
    """pages: list of {'page_type', 'json_ld_types', 'has_price', 'has_postal_address',
    'primary_date'} for the pages actually fetched. inventory: the full discovered URL list
    (page_type only), used for every rule that is a *proportion* or a site-size test.

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

    has_offer_price = any(p.get("has_price") for p in pages)
    article_dates = {
        p.get("primary_date") for p in pages
        if p.get("page_type") == "article" and p.get("primary_date")
    }
    is_local_business = any(p.get("json_ld_types") and
                             "localbusiness" in [t.lower() for t in p["json_ld_types"]]
                             for p in pages)
    has_postal_address = any(p.get("has_postal_address") for p in pages)

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
    if doc_count / total >= 0.4:
        return "documentation", 0.9
    if article_count / total >= 0.4 and len(article_dates) >= 2:
        return "news_editorial", 0.85
    if has_pricing and product_count < 5:
        return "saas_marketing", 0.8
    if is_local_business or (has_postal_address and total <= 15):
        return "local_business", 0.75
    if has_offer_price:
        return "ecommerce", 0.6
    if total <= 5:
        return "brochure", 0.7

    return "unknown", 0.0
