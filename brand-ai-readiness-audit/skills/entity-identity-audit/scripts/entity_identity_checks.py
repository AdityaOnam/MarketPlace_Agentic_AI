"""The seven checks owned by entity-identity-audit: CHK-D-006, D-007, D-008, D-012,
D-025, D-026, D-027. Pure functions over an evidence bundle; no network access.

Reference: entity-identity-audit/SKILL.md and references/checks.md.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

PERSONAL_ARCHETYPES = {"personal", "hobby", "portfolio"}
LEGAL_SUFFIXES = ["ltd", "limited", "llc", "l.l.c", "inc", "incorporated", "corp",
                   "corporation", "gmbh", "s.a", "b.v"]

_TEMPORAL_WORD_RE = re.compile(
    r"\b(announced|released|launched|updated|published|last week|yesterday|"
    r"this (?:week|month|quarter)|in Q[1-4]|recently)\b", re.I
)
_YEAR_IN_URL_RE = re.compile(r"/(19|20)\d{2}([/-]|\b)")

# CHK-D-006 accepts identity spread across the homepage's explicit identity surfaces. The
# earlier sentence-shape regex mistook "did not use X is a Y that..." for "did not identify
# itself" on five judge-reviewed sites. A signal is sufficient when any two of a name, a
# category word, and a function word occur together.
_IDENTITY_CATEGORY_RE = re.compile(
    r"\b(?:agency|application|app|author|blog|business|community|company|consultant|"
    r"corporation|developer|designer|engineer|engine|foundation|framework|institute|"
    r"institution|journalist|library|magazine|manufacturer|marketplace|network|newspaper|"
    r"nonprofit|non-profit|organisation|organization|platform|project|provider|publication|"
    r"publisher|researcher|restaurant|retailer|school|service|shop|site|software|store|"
    r"studio|tool|university|website)\b", re.I
)
_IDENTITY_FUNCTION_RE = re.compile(
    r"\b(?:allow(?:s|ed|ing)?|build(?:s|ing)?|connect(?:s|ed|ing)?|creat(?:e|es|ed|ing)|"
    r"deliver(?:s|ed|ing)?|develop(?:s|ed|ing)?|enable(?:s|d|ing)?|focus(?:es|ed|ing)?|"
    r"help(?:s|ed|ing)?|host(?:s|ed|ing)?|inform(?:s|ed|ing)?|maintain(?:s|ed|ing)?|"
    r"make(?:s|made|making)?|offer(?:s|ed|ing)?|operat(?:e|es|ed|ing)|organis(?:e|es|ed|ing)|"
    r"organiz(?:e|es|ed|ing)|power(?:s|ed|ing)?|provid(?:e|es|ed|ing)|publish(?:es|ed|ing)?|"
    r"report(?:s|ed|ing)?|search(?:es|ed|ing)?|sell(?:s|ing)?|serv(?:e|es|ed|ing)|"
    r"speciali[sz](?:e|es|ed|ing)|support(?:s|ed|ing)?|teach(?:es|ing)?|lets?)\b", re.I
)
_TITLE_NAME_SPLIT_RE = re.compile(r"\s*(?:\||—|–|:|\s+-\s+)\s*")


class _HeroParagraphParser(HTMLParser):
    """Extract the first paragraph occurring after the first h1 from collected HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.seen_h1 = False
        self.in_paragraph = False
        self.paragraph_parts: list[str] = []
        self.paragraph: str | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "h1":
            self.seen_h1 = True
        elif tag == "p" and self.seen_h1 and self.paragraph is None:
            self.in_paragraph = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "p" and self.in_paragraph:
            self.paragraph = " ".join(" ".join(self.paragraph_parts).split())
            self.in_paragraph = False

    def handle_data(self, data: str) -> None:
        if self.in_paragraph:
            self.paragraph_parts.append(data)


class _FeedLinkParser(HTMLParser):
    """Collect RSS/Atom discovery links from the document head only."""

    FEED_TYPES = {"application/rss+xml", "application/atom+xml"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "head":
            self.in_head = True
            return
        if tag != "link" or not self.in_head:
            return
        attributes = {str(k).lower(): v for k, v in attrs}
        rel = {part.lower() for part in (attributes.get("rel") or "").split()}
        media_type = (attributes.get("type") or "").lower().split(";", 1)[0].strip()
        href = attributes.get("href")
        if href and "alternate" in rel and media_type in self.FEED_TYPES:
            self.hrefs.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "head":
            self.in_head = False


def _envelope(check_id, state, evidence, severity, evidence_strength, suggested_action,
              locus=None, suppressed_by=None, recommendation_only=False):
    env = {
        "check_id": check_id, "state": state, "locus": locus or {"url": None, "selector": None},
        "evidence": evidence, "severity": severity, "evidence_strength": evidence_strength,
        "suggested_action": suggested_action, "suppressed_by": suppressed_by or [],
    }
    if recommendation_only:
        env["recommendation_only"] = True
    return env


ORG_TYPES = ("organization", "localbusiness", "corporation", "ngo",
             "educationalorganization", "governmentorganization", "nonprofit")


def _org_type_names(entity: dict) -> list[str]:
    """schema.org `@type` is legitimately either a string or an array.

    Assuming a string crashed the whole entity-identity analyser on a real site during the
    Stage B screen -- `("@type": ["Organization", "LocalBusiness"])` is valid markup and
    common on business sites, which are exactly the sites this check most needs to read.
    An AttributeError here took down four checks, not one.
    """
    raw = entity.get("type")
    if isinstance(raw, str):
        return [raw.lower()]
    if isinstance(raw, (list, tuple)):
        return [t.lower() for t in raw if isinstance(t, str)]
    return []


def _organization_blocks(page: dict) -> list[dict]:
    return [
        e for e in page.get("structured_data", {}).get("json_ld", [])
        if any(t in ORG_TYPES for t in _org_type_names(e))
    ]


def _person_blocks(page: dict) -> list[dict]:
    return [
        e for e in page.get("structured_data", {}).get("json_ld", [])
        if "person" in _org_type_names(e)
    ]


def _identity_names(bundle: dict, home: dict) -> set[str]:
    names: set[str] = set()
    for page in bundle.get("pages", []):
        footer_name = page.get("contact_signals", {}).get("org_name_footer")
        if isinstance(footer_name, str) and footer_name.strip():
            names.add(footer_name.strip())
        for entity in _organization_blocks(page):
            raw = entity.get("raw")
            name = raw.get("name") if isinstance(raw, dict) else None
            if isinstance(name, str) and name.strip():
                names.add(name.strip())

    if bundle.get("site", {}).get("archetype") in PERSONAL_ARCHETYPES:
        for entity in _person_blocks(home):
            raw = entity.get("raw")
            name = raw.get("name") if isinstance(raw, dict) else None
            if isinstance(name, str) and name.strip():
                names.add(name.strip())

    host = (bundle.get("site", {}).get("canonical_host") or "").lower()
    ignored_host_parts = {"www", "com", "org", "net", "co", "io", "dev", "app",
                          "blog", "docs", "shop"}
    names.update(part for part in host.split(".")
                 if len(part) >= 3 and part not in ignored_host_parts)

    title = (home.get("title") or "").strip()
    title_prefix = _TITLE_NAME_SPLIT_RE.split(title, maxsplit=1)[0].strip()
    if title_prefix and len(title_prefix.split()) <= 5 and len(title_prefix) <= 60:
        names.add(title_prefix)
    return names


def _contains_identity_name(text: str, names: set[str]) -> bool:
    normalized_text = " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())
    for name in names:
        normalized_name = " ".join(re.sub(r"[^a-z0-9]+", " ", name.lower()).split())
        if len(normalized_name) >= 3 and re.search(
                rf"(?:^|\s){re.escape(normalized_name)}(?:\s|$)", normalized_text):
            return True
    return False


def _identity_signal_score(text: str, names: set[str]) -> int:
    if not text:
        return 0
    return sum((
        _contains_identity_name(text, names),
        bool(_IDENTITY_CATEGORY_RE.search(text)),
        bool(_IDENTITY_FUNCTION_RE.search(text)),
    ))


def _first_paragraph_after_h1(raw_html: str | None) -> str:
    if not raw_html:
        return ""
    parser = _HeroParagraphParser()
    try:
        parser.feed(raw_html)
        parser.close()
    except (ValueError, AssertionError):
        return ""
    return parser.paragraph or ""


def _identity_sources(bundle: dict, home: dict) -> list[tuple[str, str]]:
    h1 = next((h.get("text", "") for h in home.get("headings", [])
               if h.get("level") == 1 and h.get("text")), "")
    hero = _first_paragraph_after_h1(home.get("raw_html"))
    title = home.get("title") or ""
    sources = [
        ("homepage h1", h1),
        ("first paragraph after the homepage h1", hero),
        ("homepage meta description", home.get("meta", {}).get("description") or ""),
        ("homepage title and hero paragraph", " ".join(part for part in (title, hero) if part)),
    ]

    for entity in _organization_blocks(home):
        raw = entity.get("raw")
        if isinstance(raw, dict):
            sources.append(("Organization JSON-LD name and description", " ".join(
                str(raw.get(field) or "") for field in ("name", "description"))))

    if bundle.get("site", {}).get("archetype") in PERSONAL_ARCHETYPES:
        for entity in _person_blocks(home):
            raw = entity.get("raw")
            if isinstance(raw, dict):
                sources.append(("Person JSON-LD name, description, and job title", " ".join(
                    str(raw.get(field) or "")
                    for field in ("name", "description", "jobTitle"))))
    return sources


# ---------------------------------------------------------------------------
# Time-sensitivity classification (SKILL.md §2) — needed by CHK-D-012
# ---------------------------------------------------------------------------

def classify_time_sensitivity(page: dict) -> str:
    """'time-sensitive' if >=2 of the three signals hold, else 'evergreen'. Bias toward
    evergreen when ambiguous — a false 'evergreen' just skips CHK-D-012, a false
    'time-sensitive' risks a false-positive finding on a page that was never meant to
    carry a date."""
    signals = 0

    if page.get("page_type") in ("article", "documentation", "faq") and \
            _YEAR_IN_URL_RE.search(page.get("url", "") or ""):
        signals += 1

    dates = page.get("dates", {})
    if dates.get("meta_published") or dates.get("visible_dates"):
        signals += 1

    text_prefix = (page.get("main_text", "") or "")[:1200]  # ~200 words
    if len(_TEMPORAL_WORD_RE.findall(text_prefix)) >= 3:
        signals += 1

    return "time-sensitive" if signals >= 2 else "evergreen"


# ---------------------------------------------------------------------------
# CHK-D-006 — missing explicit entity definition
# ---------------------------------------------------------------------------

def check_d006(bundle: dict) -> dict:
    archetype = bundle.get("site", {}).get("archetype")
    if archetype in {"unknown", "brochure"}:
        return _envelope(
            "CHK-D-006", "not_applicable",
            f"Archetype {archetype!r} carries insufficient signal for this check.",
            None, "NORMATIVE", None, recommendation_only=True,
        )

    home = next((p for p in bundle.get("pages", []) if p.get("page_type") == "home"), None)
    if home is None:
        return _envelope("CHK-D-006", "not_determinable", "No homepage in the sample.",
                          None, "CORRELATIONAL", None)
    if not home.get("extraction_ok", True):
        return _envelope("CHK-D-006", "not_determinable", "Content could not be extracted.",
                          None, "CORRELATIONAL", None, locus={"url": home.get("url")})

    names = _identity_names(bundle, home)
    for source_name, source_text in _identity_sources(bundle, home):
        if _identity_signal_score(source_text, names) >= 2:
            return _envelope(
                "CHK-D-006", "absent",
                f"Identity text found in the {source_name}.", None, "CORRELATIONAL", None,
                locus={"url": home.get("url")},
            )

    # Personal sites are not required to introduce themselves as organisations. Person
    # JSON-LD can positively satisfy the check above, but its absence is not a defect.
    if archetype in PERSONAL_ARCHETYPES:
        return _envelope("CHK-D-006", "not_applicable", "Personal/hobby archetype: exempt.",
                          None, "CORRELATIONAL", None)

    return _envelope(
        "CHK-D-006", "present",
        "None of the homepage h1, first paragraph after it, meta description, title/hero "
        "combination, or relevant JSON-LD contains at least two identity signals (name, "
        "category, function).", "medium", "CORRELATIONAL",
        {"summary": "Consider whether readers would benefit from clarifying the name, "
                     "category, and function together in a prominent homepage identity "
                     "surface.",
         "priority": "medium"},
        locus={"url": home.get("url")}, recommendation_only=True,
    )


# ---------------------------------------------------------------------------
# CHK-D-007 — missing or incomplete Organization JSON-LD
# ---------------------------------------------------------------------------

def check_d007(bundle: dict) -> dict:
    """Severity capped at `low` (was `medium`) since Stage C (2026-09-04): fired on 26 of 34
    real dev/negative-control sites. Web Data Commons Oct 2024 measured only 44.1% of 37.4M
    domains carrying *any* structured data at all (PLAN.md §5), so absence is the majority
    condition on the open web, not a differentiated signal -- D-009's "findings conditioned
    on base rates" rule, applied in code rather than left as a design statement. The Phase 8
    judge study additionally found that presenting this common absence as a scored defect
    made the action read like a prescribed implementation. A present result therefore routes
    to `recommendations[]`; a complete block still contributes to `checks_passed[]`.
    """
    archetype = bundle.get("site", {}).get("archetype")
    if archetype in {"unknown", "brochure"}:
        return _envelope(
            "CHK-D-007", "not_applicable",
            f"Archetype {archetype!r} carries insufficient signal for this check.",
            None, "NORMATIVE", None, recommendation_only=True,
        )
    if archetype in PERSONAL_ARCHETYPES:
        return _envelope("CHK-D-007", "not_applicable", "Personal/hobby archetype: exempt.",
                          None, "THEORETICAL/PRACTITIONER", None)

    home = next((p for p in bundle.get("pages", []) if p.get("page_type") == "home"), None)
    if home is None:
        return _envelope("CHK-D-007", "not_determinable", "No homepage in the sample.",
                          None, "THEORETICAL/PRACTITIONER", None)
    if not home.get("extraction_ok", True):
        return _envelope("CHK-D-007", "not_determinable", "Content could not be extracted.",
                          None, "THEORETICAL/PRACTITIONER", None, locus={"url": home.get("url")})

    blocks = _organization_blocks(home)
    locus = {"url": home.get("url")}
    if not blocks:
        return _envelope(
            "CHK-D-007", "present", "No Organization JSON-LD block found.", "low",
            "THEORETICAL/PRACTITIONER",
            {"summary": "Consider whether machine readers would benefit from an "
                         "Organization JSON-LD block that declares at least the name and "
                         "authoritative URL.", "priority": "low"}, locus=locus,
            recommendation_only=True)

    required = {"name", "url"}
    missing = required - set(blocks[0].get("fields_present", []))
    if missing:
        return _envelope(
            "CHK-D-007", "present", f"Found but missing: {sorted(missing)}.", "low",
            "THEORETICAL/PRACTITIONER",
            {"summary": "Consider whether completing the existing Organization JSON-LD "
                         "with the missing name or authoritative URL would help machine "
                         "readers identify the organisation.", "priority": "low"},
            locus=locus, recommendation_only=True)

    return _envelope("CHK-D-007", "absent", "Organization JSON-LD present with required "
                      "fields.", None, "THEORETICAL/PRACTITIONER", None, locus=locus)


# ---------------------------------------------------------------------------
# CHK-D-008 — missing or cross-domain canonical
# ---------------------------------------------------------------------------

def check_d008(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        if not page.get("extraction_ok", True):
            # A page whose fetch failed outright has canonical={} by construction, which
            # read as "no rel=canonical found" -- a confirmed defect on a page we never
            # actually got. Found live on www.gnu.org in the adversarial set (2026-09-04).
            findings.append(_envelope("CHK-D-008", "not_determinable",
                                       "Page could not be fetched.", None, "CAUSAL", None,
                                       locus=locus))
            continue
        canonical = page.get("canonical", {})
        if canonical.get("self_referential"):
            findings.append(_envelope("CHK-D-008", "absent", f"Page {page.get('url')}: "
                                       "self-referential canonical present.", None, "CAUSAL",
                                       None, locus=locus))
        elif not canonical.get("href"):
            findings.append(_envelope(
                "CHK-D-008", "present", f"Page {page.get('url')}: no rel=canonical found.",
                "medium", "CAUSAL",
                {"summary": "Consider whether a consistent self-referential canonical URL "
                             "would make the preferred version of this indexable page "
                             "unambiguous.", "priority": "medium"}, locus=locus,
                recommendation_only=True))
        elif canonical.get("cross_domain"):
            findings.append(_envelope(
                "CHK-D-008", "present",
                f"Page {page.get('url')}: canonical points to a different domain.",
                "medium", "CAUSAL",
                {"summary": "Consider whether the cross-domain canonical URL intentionally "
                             "identifies the brand's authoritative domain; otherwise, a "
                             "self-referential canonical may better express ownership.",
                 "priority": "medium"}, locus=locus, recommendation_only=True))
        else:
            findings.append(_envelope("CHK-D-008", "absent", f"Page {page.get('url')}: "
                                       "canonical present, same domain.", None, "CAUSAL",
                                       None, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-D-012 — missing date signal on time-sensitive content
# ---------------------------------------------------------------------------

def check_d012(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        if not page.get("extraction_ok", True):
            findings.append(_envelope("CHK-D-012", "not_determinable",
                                       "Page could not be fetched.", None, "THEORETICAL", None,
                                       locus=locus))
            continue
        classification = classify_time_sensitivity(page)
        if classification == "evergreen":
            continue
        dates = page.get("dates", {})
        # Any one of: Last-Modified header, meta published/modified, JSON-LD
        # datePublished/dateModified, a <time> or visible date string, or a /YYYY/MM/DD/
        # path segment. A page with a date in its own URL is not undated.
        if (dates.get("header_last_modified") or dates.get("meta_published")
                or dates.get("jsonld_published") or dates.get("jsonld_modified")
                or dates.get("visible_dates") or dates.get("url_date")):
            findings.append(_envelope("CHK-D-012", "absent", f"Page {page.get('url')}: date "
                                       "signal present.", None, "THEORETICAL", None, locus=locus))
        else:
            findings.append(_envelope(
                "CHK-D-012", "present",
                f"Page {page.get('url')} (time-sensitive) has no detectable publication date.",
                "low", "THEORETICAL",
                {"summary": "Add a visible publication date or article:published_time meta "
                             "tag.", "priority": "low"}, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-D-025 / CHK-D-026 — declared identity anchors and their reachability
# ---------------------------------------------------------------------------

def check_d025_d026(bundle: dict) -> tuple[dict, dict]:
    archetype = bundle.get("site", {}).get("archetype")
    if archetype in PERSONAL_ARCHETYPES:
        d025 = _envelope("CHK-D-025", "not_applicable", "Personal/hobby/portfolio "
                          "archetype: exempt.", None, "CORRELATIONAL", None)
        d026 = _envelope("CHK-D-026", "not_applicable", "No CHK-D-025 finding to act on.",
                          None, "HARD-MECHANICAL", None)
        return d025, d026

    # Pages whose fetch failed outright (extraction_ok=False) carry empty
    # structured_data/outbound_profile_links by construction -- including them would read
    # as "no anchors declared" on a page we never actually got. Found live on www.gnu.org
    # in the adversarial set (2026-09-04): a fetch failure produced a false CHK-D-025.
    home_about_raw = [p for p in bundle.get("pages", []) if p.get("page_type") in ("home", "about")]
    home_about = [p for p in home_about_raw if p.get("extraction_ok", True)]
    if home_about_raw and not home_about:
        d025 = _envelope("CHK-D-025", "not_determinable",
                          "Home/about page(s) could not be fetched.", None, "CORRELATIONAL", None)
        d026 = _envelope("CHK-D-026", "not_determinable", "No CHK-D-025 verdict to act on.",
                          None, "HARD-MECHANICAL", None)
        return d025, d026
    same_as_present = any(
        "sameAs" in e.get("fields_present", [])
        for p in home_about for e in p.get("structured_data", {}).get("json_ld", [])
    )
    outbound_links = [l for p in home_about for l in p.get("outbound_profile_links", [])]

    anchors = bundle.get("anchors", {})
    any_resolved = any(r.get("resolved") is True for r in anchors.get("results", []))

    if not same_as_present and not outbound_links and not any_resolved:
        d025 = _envelope(
            "CHK-D-025", "present",
            "No sameAs declarations or outbound identity-profile links found on the "
            "homepage or about page.", "medium", "CORRELATIONAL",
            {"summary": "Declare identity anchors: add sameAs to the Organization JSON-LD "
                         "pointing at the organisation's authoritative external profiles.",
             "priority": "medium"})
        d026 = _envelope("CHK-D-026", "not_applicable", "No declared anchor to check "
                          "(CHK-D-025 fired).", None, "HARD-MECHANICAL", None,
                          suppressed_by=["CHK-D-025"])
        return d025, d026

    d025 = _envelope("CHK-D-025", "absent", "At least one identity anchor declared.", None,
                      "CORRELATIONAL", None)

    if anchors.get("status") != "ok":
        d026 = _envelope("CHK-D-026", "not_determinable", anchors.get("reason") or
                          "Off-site anchor check unavailable.", None, "HARD-MECHANICAL", None)
        return d025, d026

    results = anchors.get("results", [])
    if not results:
        d026 = _envelope("CHK-D-026", "not_determinable", "No anchors were checked.", None,
                          "HARD-MECHANICAL", None)
        return d025, d026

    failed = [r for r in results if r.get("resolved") is False]
    determinable = [r for r in results if r.get("resolved") is not None]

    if not determinable:
        d026 = _envelope("CHK-D-026", "not_determinable",
                          "All declared anchors returned bot-blocked statuses.", None,
                          "HARD-MECHANICAL", None)
    elif len(failed) == len(determinable):
        d026 = _envelope(
            "CHK-D-026", "present",
            f"{len(failed)} of {len(results)} declared identity anchors did not resolve.",
            "high", "HARD-MECHANICAL",
            {"summary": "Repair or remove dead anchor URLs so every declared profile "
                         "resolves.", "priority": "high"})
    elif failed:
        d026 = _envelope(
            "CHK-D-026", "present",
            f"{len(failed)} of {len(results)} declared identity anchors did not resolve.",
            "medium", "HARD-MECHANICAL",
            {"summary": "Repair or remove dead anchor URLs so every declared profile "
                         "resolves.", "priority": "medium"})
    else:
        d026 = _envelope("CHK-D-026", "absent", "All declared anchors resolve.", None,
                          "HARD-MECHANICAL", None)

    return d025, d026


# ---------------------------------------------------------------------------
# CHK-D-027 — self-inconsistent identity attributes
# ---------------------------------------------------------------------------

def _normalize_name(name: str) -> str:
    n = name.strip().lower()
    n = re.sub(r"[.,]", "", n)
    for suffix in LEGAL_SUFFIXES:
        n = re.sub(rf"\b{re.escape(suffix)}\b", "", n)
    return re.sub(r"\s+", " ", n).strip()


def check_d027(bundle: dict) -> dict:
    """Names must come from Organization entities, not from every entity with a `name`.

    Repaired 2026-09-04 after the Stage B negative-control screen. This read `name` off
    *every* JSON-LD entity on every sampled page. A real site's graph carries WebPage,
    BreadcrumbList, ListItem and ImageObject entities, all of which have a `name` that is
    a page title or a breadcrumb label -- so on any site with per-page JSON-LD the check
    collected twenty page titles, found them "inconsistent", and reported the site's own
    headlines as competing organisation names. It fired on 6 of 8 clean sites that way.

    `_organization_blocks` -- the same filter CHK-D-007 already used -- was sitting in
    this file unused by this check.
    """
    names = []
    for page in bundle.get("pages", []):
        for e in _organization_blocks(page):
            raw = e.get("raw", {})
            if isinstance(raw, dict) and raw.get("name"):
                names.append(raw["name"])
        footer_name = page.get("contact_signals", {}).get("org_name_footer")
        if footer_name:
            names.append(footer_name)

    if len(names) < 2:
        return _envelope("CHK-D-027", "not_determinable",
                          "Fewer than 2 name instances found to compare.", None, "THEORETICAL",
                          None, recommendation_only=True)

    normalized = sorted({_normalize_name(n).lower() for n in names if _normalize_name(n)})
    # Brand-family variants are not inconsistency: "USA TODAY" / "USA TODAY Network" /
    # "USA TODAY Witness" share one stem. If every name contains the shortest one, the
    # site is naming its parent brand and its divisions, not contradicting itself.
    if len(normalized) <= 1 or all(normalized[0] in n for n in normalized):
        return _envelope("CHK-D-027", "absent", "Organisation name is consistent across "
                          "all observed locations.", None, "THEORETICAL", None,
                          recommendation_only=True)

    # Recommendation-only (2026-09-12). Fired three times on outside test sites and was
    # wrong three times -- twice on footer extraction, once on brand-family names -- and
    # Stage E could not grade it (below the 10-site floor). A name-variation *notice* the
    # owner can confirm or dismiss cannot be a false positive; a `medium` finding can.
    return _envelope(
        "CHK-D-027", "present",
        f"The organisation is named {len(normalized)} different ways across "
        f"{len(names)} places on the site: {sorted(set(names))}.",
        None, "THEORETICAL",
        {"summary": "If these are meant to be the same organisation, pick one form of the "
                     "name and use it in the footer, the About page and the Organization "
                     "JSON-LD. If they are distinct brands or divisions, no change is needed. "
                     "(Proactive — not a confirmed defect.)", "priority": "low"},
        recommendation_only=True,
    )


# ---------------------------------------------------------------------------
# CHK-D-029..034 — archetype-specific structured-data and feed signals
# ---------------------------------------------------------------------------

_ARTICLE_TYPES = {"article", "blogposting", "newsarticle", "report", "analysisnewsarticle"}
_LISTING_PATH_RE = re.compile(
    r"/(?:jobs?|events?|listings?|hackathons?|competitions?|challenges?|marketplace|browse)(?:/|$)", re.I
)
_ARCHIVE_SIGNAL_RE = re.compile(
    r"\b(?:code repository|source code|software archive|dataset|data catalogue|data catalog|"
    r"open data|code archive)\b|/(?:datasets?|data-catalog|repositories|source)(?:/|$)", re.I
)


def _json_entities(page: dict, accepted_types: set[str]) -> list[dict]:
    return [entity for entity in page.get("structured_data", {}).get("json_ld", [])
            if accepted_types.intersection(_org_type_names(entity))]


def _raw_dict(entity: dict) -> dict:
    return entity.get("raw") if isinstance(entity.get("raw"), dict) else {}


def _feed_hrefs(page: dict) -> list[str]:
    raw_html = page.get("raw_html")
    if not raw_html:
        return []
    parser = _FeedLinkParser()
    try:
        parser.feed(raw_html)
        parser.close()
    except (ValueError, AssertionError):
        return []
    return parser.hrefs


def _first_available_page(bundle: dict) -> dict | None:
    return next((p for p in bundle.get("pages", []) if p.get("extraction_ok", True)), None)


def _offer_is_complete(offer: object) -> bool:
    offers = offer if isinstance(offer, list) else [offer]
    return any(
        isinstance(item, dict)
        and (item.get("price") not in (None, "")
             or item.get("lowPrice") not in (None, ""))
        and item.get("priceCurrency")
        for item in offers
    )


def _vertical_na(check_id: str, archetype: str | None) -> dict:
    return _envelope(check_id, "not_applicable",
                     f"Archetype {archetype!r} is outside this schema check's scope.",
                     None, "NORMATIVE/PRACTITIONER", None, recommendation_only=True)


def _vertical_pass(check_id: str, evidence: str, locus: dict | None = None) -> dict:
    return _envelope(check_id, "absent", evidence, None, "NORMATIVE/PRACTITIONER", None,
                     locus=locus, recommendation_only=True)


def _vertical_recommendation(check_id: str, evidence: str, action: str,
                             locus: dict | None = None) -> dict:
    return _envelope(
        check_id, "present", evidence, "low", "NORMATIVE/PRACTITIONER",
        {"summary": action, "priority": "low"}, locus=locus, recommendation_only=True,
    )


def check_d029_ecommerce_schema(bundle: dict) -> dict:
    check_id = "CHK-D-029"
    archetype = bundle.get("site", {}).get("archetype")
    if archetype != "ecommerce":
        return _vertical_na(check_id, archetype)
    pages = [p for p in bundle.get("pages", [])
             if p.get("extraction_ok", True) and p.get("page_type") == "product"]
    valid_pages = []
    malformed_pages = []
    for page in pages:
        products = _json_entities(page, {"product"})
        standalone_offers = _json_entities(page, {"offer", "aggregateoffer"})
        valid = any(_raw_dict(e).get("name")
                    and _offer_is_complete(_raw_dict(e).get("offers"))
                    for e in products)
        valid = valid or any(_offer_is_complete(_raw_dict(e)) for e in standalone_offers)
        if valid:
            valid_pages.append(page)
        elif products or standalone_offers:
            malformed_pages.append(page)
    if pages and len(valid_pages) == len(pages):
        return _vertical_pass(
            check_id, f"Valid Product/Offer JSON-LD found on all {len(pages)} sampled "
            "product pages.", locus={"url": pages[0].get("url")})
    affected = malformed_pages or [p for p in pages if p not in valid_pages]
    locus_page = affected[0] if affected else _first_available_page(bundle)
    locus = ({"url": locus_page.get("url")} if locus_page
             else {"url": None, "scope": "site"})
    detail = (f"{len(affected)} of {len(pages)} sampled product pages lack complete "
              "Product/Offer JSON-LD." if pages else
              "No sampled product page supplied Product/Offer JSON-LD evidence.")
    return _vertical_recommendation(
        check_id, detail,
        "Consider whether complete Product and Offer data on product pages would make "
        "names, prices, currency, and availability easier for machine readers to verify.", locus)


def check_d030_saas_schema(bundle: dict) -> dict:
    check_id = "CHK-D-030"
    archetype = bundle.get("site", {}).get("archetype")
    if archetype != "saas_marketing":
        return _vertical_na(check_id, archetype)
    pages = [p for p in bundle.get("pages", []) if p.get("extraction_ok", True)
             and p.get("page_type") in {"home", "pricing"}]
    for page in pages:
        applications = _json_entities(page, {"softwareapplication", "webapplication"})
        offers = _json_entities(page, {"offer", "aggregateoffer", "pricing"})
        valid_app = any(_raw_dict(e).get("name") and any(
            _raw_dict(e).get(field) for field in ("applicationCategory", "operatingSystem", "offers")
        ) for e in applications)
        valid_offer = any(_offer_is_complete(_raw_dict(e)) for e in offers)
        if valid_app or valid_offer:
            return _vertical_pass(
                check_id, "SoftwareApplication or priced Offer JSON-LD is present on a "
                "homepage/pricing page.", locus={"url": page.get("url")})
    return _vertical_recommendation(
        check_id, "No complete SoftwareApplication or priced Offer JSON-LD was found on "
        "the sampled homepage/pricing pages.",
        "Consider whether structured software identity and pricing data would help machine "
        "readers distinguish the product and interpret its commercial terms.",
        {"url": pages[0].get("url")} if pages else
        ({"url": _first_available_page(bundle).get("url")} if _first_available_page(bundle)
         else {"url": None, "scope": "site"}))


def check_d031_marketplace_schema(bundle: dict) -> dict:
    check_id = "CHK-D-031"
    archetype = bundle.get("site", {}).get("archetype")
    if archetype != "marketplace":
        return _vertical_na(check_id, archetype)
    pages = [p for p in bundle.get("pages", []) if p.get("extraction_ok", True)
             and (p.get("page_type") == "category" or _LISTING_PATH_RE.search(p.get("url", "")))]
    required = {
        "event": ("name", "startDate", "location"),
        "itemlist": ("itemListElement",),
        "jobposting": ("title", "datePosted", "hiringOrganization"),
    }
    for page in pages:
        for entity in page.get("structured_data", {}).get("json_ld", []):
            raw = _raw_dict(entity)
            for entity_type in _org_type_names(entity):
                fields = required.get(entity_type)
                if fields and all(raw.get(field) for field in fields):
                    return _vertical_pass(
                        check_id, f"Complete {entity_type} JSON-LD is present on a sampled "
                        "listing page.", locus={"url": page.get("url")})
    return _vertical_recommendation(
        check_id, "No complete Event, ItemList, or JobPosting JSON-LD was found on sampled "
        "listing pages.",
        "Consider whether the schema type matching the marketplace's inventory would make "
        "individual listings and their relationships easier to interpret.",
        {"url": pages[0].get("url")} if pages else
        ({"url": _first_available_page(bundle).get("url")} if _first_available_page(bundle)
         else {"url": None, "scope": "site"}))


def check_d032_news_schema(bundle: dict) -> dict:
    check_id = "CHK-D-032"
    archetype = bundle.get("site", {}).get("archetype")
    if archetype != "news_editorial":
        return _vertical_na(check_id, archetype)
    pages = [p for p in bundle.get("pages", [])
             if p.get("extraction_ok", True) and p.get("page_type") == "article"]
    feed_page = next((p for p in bundle.get("pages", []) if _feed_hrefs(p)), None)
    malformed = []
    for page in pages:
        articles = _json_entities(page, {"newsarticle"})
        valid = False
        for article in articles:
            raw = _raw_dict(article)
            authors = raw.get("author")
            authors = authors if isinstance(authors, list) else [authors]
            has_author_name = any(isinstance(author, dict) and author.get("name")
                                  for author in authors)
            if raw.get("datePublished") and raw.get("headline") and has_author_name:
                valid = True
                break
        if not valid:
            malformed.append(page)
    if pages and not malformed and feed_page:
        return _vertical_pass(
            check_id, f"All {len(pages)} sampled articles have complete NewsArticle JSON-LD, "
            "and an RSS/Atom discovery link is present.", locus={"url": pages[0].get("url")})
    missing = []
    if not pages:
        missing.append("no sampled article pages")
    elif malformed:
        missing.append(f"{len(malformed)} article page(s) without complete NewsArticle data")
    if not feed_page:
        missing.append("no RSS/Atom discovery link")
    locus_page = malformed[0] if malformed else (
        pages[0] if pages else _first_available_page(bundle))
    return _vertical_recommendation(
        check_id, "; ".join(missing) + ".",
        "Consider whether complete NewsArticle authorship and publication fields together "
        "with feed discovery would improve machine-readable editorial provenance.",
        {"url": locus_page.get("url")} if locus_page else {"url": None, "scope": "site"})


def _author_names(raw: dict) -> set[str]:
    authors = raw.get("author")
    authors = authors if isinstance(authors, list) else [authors]
    return {str(author.get("name")).strip().lower() for author in authors
            if isinstance(author, dict) and author.get("name")}


def check_d033_personal_schema(bundle: dict) -> dict:
    check_id = "CHK-D-033"
    archetype = bundle.get("site", {}).get("archetype")
    if archetype not in PERSONAL_ARCHETYPES:
        return _vertical_na(check_id, archetype)
    pages = [p for p in bundle.get("pages", []) if p.get("extraction_ok", True)]
    feed_page = next((p for p in pages if _feed_hrefs(p)), None)
    people = []
    for page in pages:
        people.extend((page, entity) for entity in _person_blocks(page)
                      if _raw_dict(entity).get("name"))
    person_names = {_normalize_name(str(_raw_dict(entity).get("name")))
                    for _, entity in people}
    article_pages = [p for p in pages if p.get("page_type") == "article"]
    inconsistent = []
    for page in article_pages:
        article_names = set()
        for entity in _json_entities(page, _ARTICLE_TYPES):
            article_names.update(_normalize_name(name) for name in _author_names(_raw_dict(entity)))
        if not article_names or not article_names.intersection(person_names):
            inconsistent.append(page)
    if people and feed_page and not inconsistent:
        return _vertical_pass(
            check_id, "Person JSON-LD and RSS/Atom discovery are present; sampled article "
            "bylines are consistent with the declared person.",
            locus={"url": people[0][0].get("url")})
    missing = []
    if not people:
        missing.append("no named Person JSON-LD")
    if not feed_page:
        missing.append("no RSS/Atom discovery link")
    if inconsistent:
        missing.append(f"{len(inconsistent)} article byline(s) absent or inconsistent")
    return _vertical_recommendation(
        check_id, "; ".join(missing) + ".",
        "Consider whether a named Person declaration, feed discovery, and consistent "
        "article authorship would make the site's author identity easier to verify.",
        {"url": inconsistent[0].get("url")} if inconsistent else
        ({"url": _first_available_page(bundle).get("url")} if _first_available_page(bundle)
         else {"url": None, "scope": "site"}))


def check_d034_archive_schema(bundle: dict) -> dict:
    check_id = "CHK-D-034"
    archetype = bundle.get("site", {}).get("archetype")
    if archetype not in {"reference", "institutional"}:
        return _vertical_na(check_id, archetype)
    pages = [p for p in bundle.get("pages", []) if p.get("extraction_ok", True)]
    archive_pages = [p for p in pages if _ARCHIVE_SIGNAL_RE.search(
        " ".join((p.get("url", ""), p.get("title") or "", (p.get("main_text") or "")[:1500]))
    )]
    if not archive_pages:
        return _envelope(check_id, "not_applicable",
                         "No code or data archive was identified in the sampled pages.",
                         None, "NORMATIVE/PRACTITIONER", None, recommendation_only=True)
    for page in archive_pages:
        for entity in _json_entities(page, {"softwaresourcecode", "datacatalog"}):
            raw = _raw_dict(entity)
            entity_types = set(_org_type_names(entity))
            valid_code = "softwaresourcecode" in entity_types and raw.get("name") and (
                raw.get("codeRepository") or raw.get("programmingLanguage"))
            valid_catalog = "datacatalog" in entity_types and raw.get("name") and raw.get("dataset")
            if valid_code or valid_catalog:
                return _vertical_pass(
                    check_id, "Complete SoftwareSourceCode or DataCatalog JSON-LD is present "
                    "for a sampled archive.", locus={"url": page.get("url")})
    return _vertical_recommendation(
        check_id, "A code/data archive was identified, but no complete SoftwareSourceCode "
        "or DataCatalog JSON-LD was found.",
        "Consider whether archive-specific structured data would make repository or "
        "dataset identity, contents, and provenance easier to interpret.",
        locus={"url": archive_pages[0].get("url")})


def check_vertical_schema_family(bundle: dict) -> list[dict]:
    return [
        check_d029_ecommerce_schema(bundle),
        check_d030_saas_schema(bundle),
        check_d031_marketplace_schema(bundle),
        check_d032_news_schema(bundle),
        check_d033_personal_schema(bundle),
        check_d034_archive_schema(bundle),
    ]


def evaluate(bundle: dict) -> list[dict]:
    findings: list[dict] = [check_d006(bundle), check_d007(bundle)]
    findings.extend(check_d008(bundle))
    findings.extend(check_d012(bundle))
    d025, d026 = check_d025_d026(bundle)
    findings.extend([d025, d026])
    findings.append(check_d027(bundle))
    findings.extend(check_vertical_schema_family(bundle))
    return findings
