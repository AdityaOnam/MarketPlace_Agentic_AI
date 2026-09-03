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
    ("pricing", re.compile(r"pricing|plans", re.I)),
    ("documentation", re.compile(r"\bdocs\b|documentation|\bapi\b|reference|guide|manual", re.I)),
    ("contact", re.compile(r"contact|support|get-in-touch", re.I)),
    ("about", re.compile(r"about|company|who-we-are|team|mission", re.I)),
    ("product", re.compile(r"/(product|item|p|shop)(/|$)", re.I)),
]

_DATE_IN_PATH_RE = re.compile(r"/(19|20)\d{2}[/-]")


def classify_page_type(url: str, title: str | None, json_ld_types: list[str]) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    title = title or ""

    if path == "/" or path == "":
        return "home"

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


def classify_archetype(pages: list[dict]) -> tuple[str, float]:
    """pages: list of {'page_type': str, 'json_ld_types': list[str], 'has_price': bool,
    'has_postal_address': bool}. Returns (archetype, confidence)."""
    total = len(pages)
    if total == 0:
        return "unknown", 0.0

    product_count = sum(1 for p in pages if p.get("page_type") == "product")
    has_offer_price = any(p.get("has_price") for p in pages)
    doc_count = sum(1 for p in pages if p.get("page_type") == "documentation")
    article_dates = {
        p.get("primary_date") for p in pages
        if p.get("page_type") == "article" and p.get("primary_date")
    }
    article_count = sum(1 for p in pages if p.get("page_type") == "article")
    has_pricing = any(p.get("page_type") == "pricing" for p in pages)
    is_local_business = any(p.get("json_ld_types") and
                             "localbusiness" in [t.lower() for t in p["json_ld_types"]]
                             for p in pages)
    has_postal_address = any(p.get("has_postal_address") for p in pages)

    if product_count >= 5 or has_offer_price:
        return "ecommerce", 0.9 if product_count >= 5 else 0.6
    if doc_count / total >= 0.4:
        return "documentation", 0.9
    if article_count / total >= 0.4 and len(article_dates) >= 2:
        return "news_editorial", 0.85
    if has_pricing and product_count < 5:
        return "saas_marketing", 0.8
    if is_local_business or (has_postal_address and total <= 15):
        return "local_business", 0.75
    if total <= 5:
        return "brochure", 0.7

    return "unknown", 0.0
