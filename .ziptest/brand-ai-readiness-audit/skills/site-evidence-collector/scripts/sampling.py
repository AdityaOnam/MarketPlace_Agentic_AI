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
    # Authentication plumbing. Phase 10 P10-10: `/session` alone was excluding
    # legitimate conference-session detail pages like Databricks's
    # `/dataaisummit/session/{id}` because `_path_in_family` matches any URL with
    # a `/session/` segment. The authentication family is already covered by
    # `/login`, `/signin`, `/signup`, `/logout`, `/auth/`, `/oauth/`, `/sso/`,
    # `/callback`; specific session-auth verbs (`/session/new`, `/session/end`)
    # are handled by `_AUTH_SESSION_VERB_RE` below.
    "/auth/", "/authentications/", "/oauth/", "/login", "/signin", "/signup",
    "/logout", "/sso/", "/callback",
    # Legal/policy pages do not represent the site's substantive content.
    "/legal", "/legal-notice", "/privacy", "/terms", "/cookies", "/imprint",
    "/impressum", "/gdpr", "/dmca", "/eula", "/mentions-legales", "/conduct",
    "/code-of-conduct", "/coc",
    # Download and brand-asset utilities.
    "/assets", "/brand", "/media-kit", "/press", "/download", "/downloads", "/dl",
)
# Redirect/navigation utility parameters are eligible only when their value is an
# ordinary scalar (for example, `?next=5`).  A URL-shaped value routes collection
# through a redirect or navigation helper rather than to substantive page content.
_AUTH_QUERY_KEYS = {"return_to", "redirect_uri", "next", "go"}

# Phase 10 P10-10: narrow session-auth exclusion to explicit verb tails, so
# conference or session-detail content is not swept up. The old blanket
# `/session` family excluded `/dataaisummit/session/{id}` alongside the real
# `/session/new`.
_AUTH_SESSION_VERB_RE = re.compile(
    r"/session(?:s)?/(?:new|create|edit|update|destroy|end|logout|renew|refresh)(?:/|$|\?)",
    re.I,
)

# Phase 10 P10-10: MediaWiki administrative namespaces. The URL segment after
# `/wiki/` names a namespace when it contains a colon. Only exclude namespaces
# that are administrative — content article titles can also contain colons
# (e.g. "En:dash"), so a blanket colon exclusion would drop real content.
_MEDIAWIKI_ADMIN_RE = re.compile(
    r"/wiki/("
    r"Template|Category|Help|Wikipedia|File|MediaWiki|"
    r"Portal|Book|Draft|TimedText|Module|Special|User|User_talk|Talk|"
    r"Wikipedia_talk|Template_talk|Category_talk|File_talk|MediaWiki_talk|"
    r"Portal_talk|Book_talk|Draft_talk|Module_talk"
    r")(?::|%3A)",
    re.I,
)

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
    # Phase 10 P10-10: reject session-auth verb tails specifically, so conference
    # session detail URLs (`.../session/{id}`) continue to be eligible.
    if _AUTH_SESSION_VERB_RE.search(path):
        return False
    # Phase 10 P10-10: MediaWiki administrative namespaces.
    if _MEDIAWIKI_ADMIN_RE.search(path):
        return False
    # Phase 10 P10-10: only reject a `return_to` / `redirect_uri` / `next` / `go` query
    # value when the value is URL-shaped — a plain `?next=2` on a paginator is
    # not an auth redirect, whereas `?redirect_uri=https%3A%2F%2F...` is. This
    # keeps legitimate paginated content in the sampler while still filtering
    # true auth-flow URLs.
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in _AUTH_QUERY_KEYS and _looks_url_shaped(value):
            return False
    return True


def _looks_url_shaped(value: str) -> bool:
    """Whether a query-string value looks like an encoded or absolute URL. Used
    to distinguish `?next=5` from `?next=%2Faccount%2Fdashboard` — the former is
    pagination, the latter is an auth-flow redirect."""
    if not value:
        return False
    lowered = value.lower()
    if lowered.startswith(("http://", "https://", "//")):
        return True
    if lowered.startswith("%2f") or lowered.startswith("/"):
        # A leading path separator implies a target URL, not a numeric value.
        return True
    return False


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

    # Phase 10 P10-10: family-diversity pass. Before proportional allocation
    # by page_type, take one representative candidate from each unique
    # top-level path family that is not already represented in `selected`.
    # This is what stopped itch.io's sample being 5/6 `/blog/` and Mozilla's
    # from being all `/en-US/about/...`: the classifier saw one family and had
    # nothing else to weigh against it. Deterministic — families are visited
    # in sorted order, and inside each family we take the first URL by the
    # existing (page_type, url) sort — so the seed determines which URL wins.
    def _top_family(url: str) -> str:
        segments = [s for s in urlparse(url).path.split("/") if s]
        return segments[0] if segments else ""

    represented_families = {_top_family(p["url"]) for p in selected}
    # Reserve slots for the proportional pass so a very-narrow inventory (e.g. a
    # docs-only site) still gets multiple pages of its dominant family. When we
    # do have unrepresented families, take one candidate from each.
    candidates_by_family: dict[str, list[dict]] = {}
    for p in eligible:
        if p["url"] in seen_urls:
            continue
        fam = _top_family(p["url"])
        if fam in represented_families:
            continue
        candidates_by_family.setdefault(fam, []).append(p)
    unrep_family_count = len(candidates_by_family)
    # Take at most (remaining_budget - 1) diversity picks, so at least one slot
    # remains for the proportional / top-up pass; but do not take more than the
    # number of unrepresented families available.
    diversity_slots = max(0, min(remaining_budget - 1, unrep_family_count))
    if diversity_slots > 0:
        for fam in sorted(candidates_by_family.keys()):
            if diversity_slots <= 0:
                break
            candidate = candidates_by_family[fam][0]
            if candidate["url"] in seen_urls:
                continue
            selected.append(candidate)
            seen_urls.add(candidate["url"])
            represented_families.add(fam)
            diversity_slots -= 1

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
