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


def _envelope(check_id, state, evidence, severity, evidence_strength, suggested_action,
              locus=None, suppressed_by=None):
    return {
        "check_id": check_id, "state": state, "locus": locus or {"url": None, "selector": None},
        "evidence": evidence, "severity": severity, "evidence_strength": evidence_strength,
        "suggested_action": suggested_action, "suppressed_by": suppressed_by or [],
    }


def _organization_blocks(page: dict) -> list[dict]:
    return [
        e for e in page.get("structured_data", {}).get("json_ld", [])
        if (e.get("type") or "").lower() in ("organization", "localbusiness", "corporation")
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

    definition_pattern = re.compile(r"\b(is|are)\s+(a|an|the)\s+\w+.{0,80}(that|which|providing|offering)", re.I)

    for page in candidates:
        if not page.get("extraction_ok", True):
            return _envelope("CHK-D-006", "not_determinable", "Content could not be extracted.",
                              None, "CORRELATIONAL", None, locus={"url": page.get("url")})
        if _organization_blocks(page):
            return _envelope("CHK-D-006", "not_applicable",
                              "Structured Organization data already states identity "
                              "machine-readably.", None, "CORRELATIONAL", None,
                              locus={"url": page.get("url")}, suppressed_by=["CHK-D-007"])
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
            "CHK-D-007", "present", "No Organization JSON-LD block found.", "medium",
            "THEORETICAL/PRACTITIONER",
            {"summary": "Add or complete an Organization JSON-LD block with at minimum "
                         "'name' and 'url'.", "priority": "medium"}, locus=locus)

    required = {"name", "url"}
    missing = required - set(blocks[0].get("fields_present", []))
    if missing:
        return _envelope(
            "CHK-D-007", "present", f"Found but missing: {sorted(missing)}.", "medium",
            "THEORETICAL/PRACTITIONER",
            {"summary": "Add or complete an Organization JSON-LD block with at minimum "
                         "'name' and 'url'.", "priority": "medium"}, locus=locus)

    return _envelope("CHK-D-007", "absent", "Organization JSON-LD present with required "
                      "fields.", None, "THEORETICAL/PRACTITIONER", None, locus=locus)


# ---------------------------------------------------------------------------
# CHK-D-008 — missing or cross-domain canonical
# ---------------------------------------------------------------------------

def check_d008(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
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
        classification = classify_time_sensitivity(page)
        if classification == "evergreen":
            continue
        dates = page.get("dates", {})
        if dates.get("header_last_modified") or dates.get("meta_published") or dates.get("visible_dates"):
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

    home_about = [p for p in bundle.get("pages", []) if p.get("page_type") in ("home", "about")]
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
    names = []
    for page in bundle.get("pages", []):
        for e in page.get("structured_data", {}).get("json_ld", []):
            raw = e.get("raw", {})
            if isinstance(raw, dict) and raw.get("name"):
                names.append(raw["name"])
        footer_name = page.get("contact_signals", {}).get("org_name_footer")
        if footer_name:
            names.append(footer_name)

    if len(names) < 2:
        return _envelope("CHK-D-027", "not_determinable",
                          "Fewer than 2 name instances found to compare.", None, "THEORETICAL", None)

    normalized = {_normalize_name(n) for n in names}
    if len(normalized) <= 1:
        return _envelope("CHK-D-027", "absent", "Organisation name is consistent across "
                          "all observed locations.", None, "THEORETICAL", None)

    return _envelope(
        "CHK-D-027", "present",
        f"Organisation name appears as {sorted(set(names))} across {len(names)} locations.",
        "medium", "THEORETICAL",
        {"summary": "State one canonical form of the organisation name, legal name, phone "
                     "and address, and use it identically everywhere.", "priority": "medium"},
    )


def evaluate(bundle: dict) -> list[dict]:
    findings: list[dict] = [check_d006(bundle), check_d007(bundle)]
    findings.extend(check_d008(bundle))
    findings.extend(check_d012(bundle))
    d025, d026 = check_d025_d026(bundle)
    findings.extend([d025, d026])
    findings.append(check_d027(bundle))
    return findings
