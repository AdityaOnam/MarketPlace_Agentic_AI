"""The seven checks owned by entity-identity-audit: CHK-D-006, D-007, D-008, D-012,
D-025, D-026, D-027. Pure functions over an evidence bundle; no network access.

Reference: entity-identity-audit/SKILL.md and references/checks.md.
"""
from __future__ import annotations

import re

PERSONAL_ARCHETYPES = {"personal", "hobby", "portfolio"}
LEGAL_SUFFIXES = ["ltd", "limited", "llc", "l.l.c", "inc", "incorporated", "corp",
                   "corporation", "gmbh", "s.a", "b.v"]

_TEMPORAL_WORD_RE = re.compile(
    r"\b(announced|released|launched|updated|published|last week|yesterday|"
    r"this (?:week|month|quarter)|in Q[1-4]|recently)\b", re.I
)
_YEAR_IN_URL_RE = re.compile(r"/(19|20)\d{2}([/-]|\b)")

# CHK-D-006's "does this page state what the organisation is" test.
#
# Widened by D-029 (2026-09-10). The previous pattern was
#     \b(is|are)\s+(a|an|the)\s+\w+.{0,80}(that|which|providing|offering)
# which additionally required the definition to continue with a relative clause or a
# participle from a four-word list. Measured against the dev corpus, that rejected every
# genuine self-definition in it:
#
#     "Hugo is one of the most popular open-source static site generators."   (also fails
#         at `is a|an|the` -- "is one of" was never accepted)
#     "Vite is a blazing fast frontend build tool powering the next generation..."
#     "LWN.net is a reader-supported news site dedicated to producing..."
#     "This is the official documentation for Python 3.13."
#
# It was not detecting "the page defines itself", it was detecting "the page defines itself
# in the shape `X is a Y that ...`". CHK-D-006 fired on 67% of sites labelled clean for it.
#
# The replacement keeps the copular construction (the thing that makes a sentence a
# definition) and drops the required continuation, accepting `one of` and `among` as
# determiners. `[^.!?]{12,}` keeps the predicate substantive enough to be a category claim
# rather than a bare "It is a start."
#
# Known trade-off, stated because it runs against this check's own purpose: a looser
# pattern accepts non-self-describing copulas ("Pricing is the same for all plans"), which
# can only *lower* recall by marking a page ABSENT that a labeller called PRESENT. That is
# the direction with the cheaper failure -- a missed finding rather than a false accusation
# against a site that did describe itself -- and D-004's severity cap already treats this
# check as CORRELATIONAL. Recall is re-measured after this change, not assumed.
_DEFINITION_SENTENCE_RE = re.compile(
    r"\b(?:is|are)\s+(?:a|an|the|one\s+of|among)\b[^.!?]{12,}", re.I
)


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
    if archetype in PERSONAL_ARCHETYPES:
        return _envelope("CHK-D-006", "not_applicable", "Personal/hobby archetype: exempt.",
                          None, "CORRELATIONAL", None)

    candidates = [p for p in bundle.get("pages", []) if p.get("page_type") in ("home", "about")]
    if not candidates:
        return _envelope("CHK-D-006", "not_determinable", "No home/about page in the sample.",
                          None, "CORRELATIONAL", None)

    # Organization JSON-LD anywhere on the site suppresses this check, not just on a page
    # the classifier happened to file as home/about. Widened by D-029 (2026-09-10): on
    # qonto.com the About page is classified `page_type="product"`, so 13 pages carrying a
    # complete Organization block (name, legalName, sameAs, foundingDate) suppressed
    # nothing and the check fired anyway. The markup was right; the page-type label was
    # wrong, and a misfiled page is not evidence that identity is unstated.
    org_page = next((p for p in bundle.get("pages", [])
                     if p.get("extraction_ok", True) and _organization_blocks(p)), None)
    if org_page is not None:
        return _envelope("CHK-D-006", "not_applicable",
                          "Structured Organization data already states identity "
                          "machine-readably.", None, "CORRELATIONAL", None,
                          locus={"url": org_page.get("url")}, suppressed_by=["CHK-D-007"])

    definition_pattern = _DEFINITION_SENTENCE_RE

    for page in candidates:
        if not page.get("extraction_ok", True):
            return _envelope("CHK-D-006", "not_determinable", "Content could not be extracted.",
                              None, "CORRELATIONAL", None, locus={"url": page.get("url")})
        first_300 = (page.get("main_text", "") or "")[:1800]  # ~300 words
        if definition_pattern.search(first_300):
            return _envelope("CHK-D-006", "absent", f"Explicit definition found on "
                              f"{page.get('url')}.", None, "CORRELATIONAL", None,
                              locus={"url": page.get("url")})

    return _envelope(
        "CHK-D-006", "present",
        "No sentence in the first 300 words explicitly names the organisation, its "
        "category, and its function.", "medium", "CORRELATIONAL",
        {"summary": "Add one clear declarative sentence near the top of the homepage or "
                     "about page naming the organisation, its category, and its function.",
         "priority": "medium"},
        locus={"url": candidates[0].get("url")},
    )


# ---------------------------------------------------------------------------
# CHK-D-007 — missing or incomplete Organization JSON-LD
# ---------------------------------------------------------------------------

def check_d007(bundle: dict) -> dict:
    """Severity capped at `low` (was `medium`) since Stage C (2026-09-04): fired on 26 of 34
    real dev/negative-control sites. Web Data Commons Oct 2024 measured only 44.1% of 37.4M
    domains carrying *any* structured data at all (PLAN.md §5), so absence is the majority
    condition on the open web, not a differentiated signal -- D-009's "findings conditioned
    on base rates" rule, applied in code rather than left as a design statement. Still a
    real, directly actionable defect, so it stays in `findings[]` rather than being demoted
    to `recommendations[]`.
    """
    archetype = bundle.get("site", {}).get("archetype")
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
            {"summary": "Add or complete an Organization JSON-LD block with at minimum "
                         "'name' and 'url'.", "priority": "low"}, locus=locus)

    required = {"name", "url"}
    missing = required - set(blocks[0].get("fields_present", []))
    if missing:
        return _envelope(
            "CHK-D-007", "present", f"Found but missing: {sorted(missing)}.", "low",
            "THEORETICAL/PRACTITIONER",
            {"summary": "Add or complete an Organization JSON-LD block with at minimum "
                         "'name' and 'url'.", "priority": "low"}, locus=locus)

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
                {"summary": "Add a consistent, self-referential rel=canonical to every "
                             "indexable page.", "priority": "medium"}, locus=locus))
        elif canonical.get("cross_domain"):
            findings.append(_envelope(
                "CHK-D-008", "present",
                f"Page {page.get('url')}: canonical points to a different domain.",
                "medium", "CAUSAL",
                {"summary": "Verify the cross-domain canonical points to the brand's own "
                             "authoritative domain, or correct it to be self-referential.",
                 "priority": "medium"}, locus=locus))
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


def evaluate(bundle: dict) -> list[dict]:
    findings: list[dict] = [check_d006(bundle), check_d007(bundle)]
    findings.extend(check_d008(bundle))
    findings.extend(check_d012(bundle))
    d025, d026 = check_d025_d026(bundle)
    findings.extend([d025, d026])
    findings.append(check_d027(bundle))
    return findings
