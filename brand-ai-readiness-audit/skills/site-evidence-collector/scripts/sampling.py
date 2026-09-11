"""Deterministic page sampling. Reference: procedure.md §4.

Never uses wall-clock or unseeded randomness — `pass^k` stability at k=5 (D-010) depends
on identical page selection across repeated runs against the same site state.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

MAX_STATIC_PAGES = 20
MAX_PER_TYPE = 4

# Belt-and-braces over the inventory builder's own `asset` labelling: a sitemap index's
# child sitemaps (`/sitemaps/en-us/sitemap.xml.gz`) are URL *sources*, never pages, and
# nothing downstream can grade gzipped XML for an <h1>. Found on developer.mozilla.org
# (2026-09-12) when an inventory reached this function with three child sitemaps labelled
# as pages and every page-level check fired on them.
_NEVER_A_PAGE_RE = re.compile(
    r"(\.(xml|xml\.gz|gz|txt|json|pdf|css|js|mjs|zip|tar|rar|"
    r"png|jpe?g|gif|webp|svg|ico|avif|woff2?|ttf|mp3|mp4|webm|mov)$)|(/sitemap[^/]*$)",
    re.I,
)


def is_page_url(url: str) -> bool:
    path = urlparse(url).path or "/"
    return not _NEVER_A_PAGE_RE.search(path)


def sampling_seed(inventory_urls: list[str]) -> str:
    sorted_urls = sorted(inventory_urls)
    digest = hashlib.sha256("\n".join(sorted_urls).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def select_static_sample(inventory: list[dict], max_pages: int = MAX_STATIC_PAGES) -> list[dict]:
    """inventory: list of {'url': str, 'page_type': str, 'source': str}.
    Returns the selected subset, deterministically, per the quota in procedure.md §4:
    homepage always; about/contact if present; up to `max_pages` - fixed, distributed
    across remaining types proportional to inventory, capped at MAX_PER_TYPE each,
    remaining slots to the largest type. `login` and `asset` are never selected.
    """
    eligible = [p for p in inventory
                if p.get("page_type") not in ("login", "asset") and is_page_url(p["url"])]
    # Deterministic tie-break: sort by (page_type, url) so selection never depends on
    # discovery order.
    eligible.sort(key=lambda p: (p["page_type"], p["url"]))

    selected: list[dict] = []
    seen_urls: set[str] = set()

    def take(pred, limit=None):
        count = 0
        for p in eligible:
            if p["url"] in seen_urls:
                continue
            if pred(p):
                selected.append(p)
                seen_urls.add(p["url"])
                count += 1
                if limit is not None and count >= limit:
                    break

    take(lambda p: p["page_type"] == "home", limit=1)
    take(lambda p: p["page_type"] == "about", limit=1)
    take(lambda p: p["page_type"] == "contact", limit=1)

    remaining_budget = max_pages - len(selected)
    if remaining_budget <= 0:
        return selected[:max_pages]

    by_type: dict[str, list[dict]] = {}
    for p in eligible:
        if p["url"] in seen_urls:
            continue
        by_type.setdefault(p["page_type"], []).append(p)

    if not by_type:
        return selected

    total_remaining = sum(len(v) for v in by_type.values())
    # Proportional allocation, capped at MAX_PER_TYPE, deterministic order by type name.
    allocations: dict[str, int] = {}
    for ptype in sorted(by_type.keys()):
        pages_of_type = by_type[ptype]
        proportional = round(remaining_budget * len(pages_of_type) / total_remaining)
        allocations[ptype] = min(proportional, MAX_PER_TYPE, len(pages_of_type))

    used = sum(allocations.values())
    leftover = remaining_budget - used
    if leftover > 0:
        # "Remaining slots to the largest type" — but the MAX_PER_TYPE cap from the
        # proportional pass still applies; it does not get waived for the top-up. If the
        # largest type is already at its cap, the leftover goes unused rather than
        # silently exceeding the per-type limit.
        for largest_type in sorted(by_type.keys(), key=lambda t: (-len(by_type[t]), t)):
            room = min(MAX_PER_TYPE, len(by_type[largest_type])) - allocations.get(largest_type, 0)
            if room <= 0:
                continue
            take_amount = min(leftover, room)
            allocations[largest_type] = allocations.get(largest_type, 0) + take_amount
            leftover -= take_amount
            if leftover <= 0:
                break

    for ptype in sorted(allocations.keys()):
        take(lambda p, pt=ptype: p["page_type"] == pt, limit=allocations[ptype])

    return selected[:max_pages]
