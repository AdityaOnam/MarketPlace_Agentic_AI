"""Deterministic page sampling. Reference: procedure.md §4.

Never uses wall-clock or unseeded randomness — `pass^k` stability at k=5 (D-010) depends
on identical page selection across repeated runs against the same site state.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlparse

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

_EXCLUDED_PATH_FAMILIES = (
    # Authentication and session plumbing.
    "/auth/", "/authentications/", "/oauth/", "/login", "/signin", "/signup",
    "/logout", "/session", "/sso/", "/callback",
    # Legal/policy pages do not represent the site's substantive content.
    "/legal", "/legal-notice", "/privacy", "/terms", "/cookies", "/imprint",
    "/impressum", "/gdpr", "/dmca", "/eula", "/mentions-legales", "/conduct",
    "/code-of-conduct", "/coc",
    # Download and brand-asset utilities.
    "/assets", "/brand", "/media-kit", "/press", "/download", "/downloads", "/dl",
)
_AUTH_QUERY_KEYS = {"return_to", "redirect_uri", "next"}

# ISO 639-1 alpha-2 language codes. Keeping the allow-list avoids treating ordinary
# two-letter route names such as /us/ as locale prefixes.
_ISO_639_1 = frozenset(
    "aa ab ae af ak am an ar as av ay az ba be bg bh bi bm bn bo br bs ca ce ch co cr "
    "cs cu cv cy da de dv dz ee el en eo es et eu fa ff fi fj fo fr fy ga gd gl gn gu "
    "gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik in io is it iu ja jv ka kg ki kj "
    "kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lu lv mg mh mi mk ml mn mr "
    "ms mt my na nb nd ne ng nl nn no nr nv ny oc oj om or os pa pi pl ps pt qu rm rn "
    "ro ru rw sa sc sd se sg si sk sl sm sn so sq sr ss st su sv sw ta te tg th ti tk "
    "tl tn to tr ts tt tw ty ug uk ur uz ve vi vo wa wo xh yi yo za zh zu".split()
)
_LOCALE_SEGMENT_RE = re.compile(r"^([a-z]{2})(?:[-_]([a-z]{2}))?$", re.I)


def _path_in_family(path: str, family: str) -> bool:
    """Match a named path segment/family without catching words such as /pressure."""
    segment = family.strip("/").lower()
    return bool(re.search(rf"(?:^|/){re.escape(segment)}(?:/|$)", path.lower()))


def _url_locale(url: str) -> str | None:
    first_segment = next((part for part in urlparse(url).path.split("/") if part), "")
    match = _LOCALE_SEGMENT_RE.fullmatch(first_segment)
    if not match or match.group(1).lower() not in _ISO_639_1:
        return None
    return match.group(1).lower()


def _lang_locale(lang: str | None) -> str | None:
    if not lang:
        return None
    match = _LOCALE_SEGMENT_RE.fullmatch(lang.strip())
    if not match or match.group(1).lower() not in _ISO_639_1:
        return None
    return match.group(1).lower()


def is_page_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if _NEVER_A_PAGE_RE.search(path):
        return False
    if any(_path_in_family(path, family) for family in _EXCLUDED_PATH_FAMILIES):
        return False
    query_keys = {key.lower() for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    return not query_keys.intersection(_AUTH_QUERY_KEYS)


def sampling_seed(inventory_urls: list[str]) -> str:
    sorted_urls = sorted(inventory_urls)
    digest = hashlib.sha256("\n".join(sorted_urls).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def select_static_sample(inventory: list[dict], max_pages: int = MAX_STATIC_PAGES,
                         seed_url: str | None = None, seed_lang: str | None = None) -> list[dict]:
    """inventory: list of {'url': str, 'page_type': str, 'source': str}.
    Returns the selected subset, deterministically, per the quota in procedure.md §4:
    homepage always; about/contact if present; up to `max_pages` - fixed, distributed
    across remaining types proportional to inventory, capped at MAX_PER_TYPE each,
    remaining slots to the largest type. `login` and `asset` are never selected.
    """
    eligible = [p for p in inventory
                if p.get("page_type") not in ("login", "asset") and is_page_url(p["url"])]

    # Prefer the seed page's language while retaining unprefixed URLs, which commonly
    # inherit that same default locale. If the preferred pool is empty, keep all locales
    # so a locale-only site still produces a sample. Callers may pass the seed page's
    # extracted <html lang>; enriched inventory records with `lang`/`html_lang` work too.
    seed_entry = next((p for p in inventory if seed_url and p.get("url") == seed_url), None)
    if seed_entry is None:
        seed_entry = next((p for p in inventory if p.get("page_type") == "home"), None)
    locale = _lang_locale(seed_lang)
    if locale is None and seed_entry:
        locale = _lang_locale(seed_entry.get("lang") or seed_entry.get("html_lang"))
    if locale is None:
        locale = _url_locale(seed_url or (seed_entry or {}).get("url", ""))
    if locale:
        preferred = [p for p in eligible if _url_locale(p["url"]) in (None, locale)]
        if preferred:
            eligible = preferred
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
