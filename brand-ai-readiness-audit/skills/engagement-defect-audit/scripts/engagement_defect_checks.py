"""The eleven checks owned by engagement-defect-audit: CHK-E-014 through CHK-E-024.
Pure functions over an evidence bundle; no network access.

Reference: engagement-defect-audit/SKILL.md and references/checks.md.
"""
from __future__ import annotations

import re

NON_DESCRIPTIVE_LINK_TEXT = {
    "click here", "here", "read more", "more", "learn more", "this link", "details",
    "info", "click", "tap", "view", "see",
}
COMMERCIAL_ARCHETYPES = {"ecommerce", "saas_marketing", "news_editorial", "local_business"}
PERSONAL_ARCHETYPES = {"personal", "hobby", "portfolio"}


def _envelope(check_id, state, evidence, severity, evidence_strength, suggested_action,
              locus=None, recommendation_only=False, subcheck=None):
    """`subcheck` distinguishes envelopes that share a check_id and a locus but are graded
    separately — CHK-E-014's static WCAG failures (ceiling `high`) and its contrast
    sub-check (ceiling `medium`, NORMATIVE) are two different judgments about one page,
    not a duplicate. The orchestrator's meta-evaluation keys its duplicate detection on
    (check_id, url, subcheck) for exactly this reason."""
    return {
        "check_id": check_id, "state": state, "locus": locus or {"url": None, "selector": None},
        "evidence": evidence, "severity": severity, "evidence_strength": evidence_strength,
        "suggested_action": suggested_action, "suppressed_by": [],
        "recommendation_only": recommendation_only, "subcheck": subcheck,
    }


def _rendered_for(bundle: dict, url: str) -> dict | None:
    return next((r for r in bundle.get("rendered", []) if r.get("url") == url), None)


# ---------------------------------------------------------------------------
# CHK-E-014 — machine-detectable WCAG failures (6 sub-checks)
# ---------------------------------------------------------------------------

def check_e014(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        violations: list[str] = []

        if page.get("lang") is None:
            violations.append("missing lang attribute")
        for img in page.get("images", []):
            if img.get("alt") is None:
                violations.append("missing alt on a non-decorative image")
        empty = page.get("interactive_empty", {})
        if empty.get("links_no_text", 0) > 0:
            violations.append(f"{empty['links_no_text']} link(s) with no accessible name")
        if empty.get("buttons_no_text", 0) > 0:
            violations.append(f"{empty['buttons_no_text']} button(s) with no accessible name")
        for fc in page.get("form_controls", []):
            if not fc.get("has_label") and not fc.get("aria_label"):
                violations.append("unlabelled form control")

        if violations:
            findings.append(_envelope(
                "CHK-E-014", "present",
                f"Page {page.get('url')}: {len(violations)} accessibility violation(s): "
                f"{'; '.join(violations)}.", "high", "HARD-MECHANICAL",
                {"summary": "Add lang, descriptive alt text, accessible names for controls, "
                             "and labels for all form inputs.", "priority": "high"}, locus=locus,
                subcheck="wcag_static"))
        else:
            findings.append(_envelope("CHK-E-014", "absent", f"Page {page.get('url')}: no "
                                       "hard-mechanical WCAG violations found.", None,
                                       "HARD-MECHANICAL", None, locus=locus,
                                       subcheck="wcag_static"))

        rendered = _rendered_for(bundle, page.get("url"))
        if rendered is None or rendered.get("status") != "ok":
            findings.append(_envelope("CHK-E-014", "not_determinable",
                                       "Rendered page evidence unavailable for contrast "
                                       "sub-check.",
                                       None, "NORMATIVE", None, locus=locus,
                                       subcheck="contrast"))
            continue
        low_contrast = [
            p for p in rendered.get("computed_styles", {}).get("contrast_pairs", [])
            if (p.get("ratio", 99) < 3.0 if (p.get("font_px", 0) >= 18 or p.get("bold"))
                else p.get("ratio", 99) < 4.5)
        ]
        if low_contrast:
            findings.append(_envelope(
                "CHK-E-014", "present",
                f"Page {page.get('url')}: {len(low_contrast)} low-contrast text pair(s).",
                "medium", "NORMATIVE",
                {"summary": "Increase foreground/background contrast to >=4.5:1 (normal "
                             "text) or >=3:1 (large text).", "priority": "medium"}, locus=locus,
                subcheck="contrast"))
        else:
            findings.append(_envelope("CHK-E-014", "absent", f"Page {page.get('url')}: "
                                       "contrast within WCAG AA.", None, "NORMATIVE", None,
                                       locus=locus, subcheck="contrast"))
    return findings


# ---------------------------------------------------------------------------
# CHK-E-015 — viewport meta missing or zoom-blocking
# ---------------------------------------------------------------------------

_MAX_SCALE_RE = re.compile(r"maximum-scale\s*=\s*([\d.]+)")


def check_e015(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        viewport = page.get("meta", {}).get("viewport")
        if viewport is None:
            findings.append(_envelope(
                "CHK-E-015", "present", f"Page {page.get('url')}: missing viewport meta "
                "tag.", "medium", "NORMATIVE",
                {"summary": "Add <meta name=\"viewport\" content=\"width=device-width, "
                             "initial-scale=1\">.", "priority": "medium"}, locus=locus,
                subcheck="viewport_meta"))
        else:
            scale_match = _MAX_SCALE_RE.search(viewport)
            zoom_blocked = "user-scalable=no" in viewport.replace(" ", "").lower() or \
                (scale_match and float(scale_match.group(1)) < 2)
            if zoom_blocked:
                findings.append(_envelope(
                    "CHK-E-015", "present", f"Page {page.get('url')}: viewport meta "
                    "disables user zoom. Violates WCAG 2.2 SC 1.4.4.", "high", "NORMATIVE",
                    {"summary": "Remove user-scalable=no and maximum-scale constraints.",
                     "priority": "high"}, locus=locus, subcheck="viewport_meta"))
            else:
                findings.append(_envelope("CHK-E-015", "absent", f"Page {page.get('url')}: "
                                           "viewport meta present, zoom not blocked.", None,
                                           "NORMATIVE", None, locus=locus,
                                           subcheck="viewport_meta"))

        rendered = _rendered_for(bundle, page.get("url"))
        if rendered is None or rendered.get("status") != "ok":
            continue
        overflow = rendered.get("viewports", {}).get("mobile_375", {}).get("horizontal_overflow")
        if overflow:
            findings.append(_envelope(
                "CHK-E-015", "present", f"Page {page.get('url')}: horizontal scroll at "
                "375px viewport width.", "medium", "NORMATIVE",
                {"summary": "Fix responsive CSS so no element overflows the viewport at "
                             "375px.", "priority": "medium"}, locus=locus,
                subcheck="overflow"))
    return findings


# ---------------------------------------------------------------------------
# CHK-E-016 — standalone tap targets below WCAG 2.2 minimum
# ---------------------------------------------------------------------------

def check_e016(bundle: dict) -> list[dict]:
    findings = []
    for rendered in bundle.get("rendered", []):
        locus = {"url": rendered.get("url")}
        if rendered.get("status") != "ok":
            findings.append(_envelope("CHK-E-016", "not_determinable",
                                       "Rendered page evidence unavailable.", None, "NORMATIVE", None,
                                       locus=locus))
            continue
        targets = rendered.get("viewports", {}).get("mobile_375", {}).get("tap_targets", [])
        small = [t for t in targets if t.get("standalone") and (t.get("w", 24) < 24 or t.get("h", 24) < 24)]
        if small:
            smallest = min(small, key=lambda t: t.get("w", 0) * t.get("h", 0))
            findings.append(_envelope(
                "CHK-E-016", "present",
                f"{len(small)} standalone interactive element(s) are below the WCAG 2.2 "
                f"SC 2.5.8 minimum of 24x24 CSS px (smallest: {smallest.get('w')}x"
                f"{smallest.get('h')} px).", "medium", "NORMATIVE",
                {"summary": "Increase target size or padding to at least 24x24 CSS px.",
                 "priority": "medium"}, locus=locus))
        else:
            findings.append(_envelope("CHK-E-016", "absent", "All standalone tap targets "
                                       "meet the WCAG 2.2 minimum.", None, "NORMATIVE", None,
                                       locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-E-017 — non-descriptive anchor text
# ---------------------------------------------------------------------------

def check_e017(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        links = page.get("links", [])
        if not links:
            findings.append(_envelope("CHK-E-017", "absent", "No links on page.", None,
                                       "NORMATIVE/THEORETICAL", None, locus=locus))
            continue
        non_descriptive = [
            l for l in links
            if not l.get("aria_label") and (l.get("text") or "").strip().lower() in NON_DESCRIPTIVE_LINK_TEXT
        ]
        pct = round(len(non_descriptive) / len(links) * 100)
        if pct > 10:
            findings.append(_envelope(
                "CHK-E-017", "present", f"Page {page.get('url')}: {len(non_descriptive)} "
                f"link(s) ({pct}%) have non-descriptive anchor text.", "medium",
                "NORMATIVE/THEORETICAL",
                {"summary": "Replace non-descriptive anchor text with text that describes "
                             "the destination or action.", "priority": "medium"}, locus=locus))
        else:
            findings.append(_envelope("CHK-E-017", "absent", f"Page {page.get('url')}: "
                                       f"{pct}% non-descriptive links, below threshold.",
                                       None, "NORMATIVE/THEORETICAL", None, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-E-018 — content-blocking overlay at load
# ---------------------------------------------------------------------------

def check_e018(bundle: dict) -> list[dict]:
    findings = []
    for rendered in bundle.get("rendered", []):
        locus = {"url": rendered.get("url")}
        if rendered.get("status") != "ok":
            findings.append(_envelope("CHK-E-018", "not_determinable",
                                       "Rendered page evidence unavailable.", None, "NORMATIVE", None,
                                       locus=locus))
            continue
        viewport = rendered.get("viewports", {}).get("mobile_375", {})
        overlays = [o for o in viewport.get("overlays", []) if o.get("dismissible_hint") == "none"]
        if overlays and viewport.get("body_scroll_locked"):
            findings.append(_envelope(
                "CHK-E-018", "present",
                f"An overlay covering ~{overlays[0].get('viewport_coverage_pct')}% of "
                f"viewport with scroll-lock is present at load.", "high", "NORMATIVE",
                {"summary": "Trigger overlays via user interaction; remove scroll-lock.",
                 "priority": "high"}, locus=locus))
        else:
            findings.append(_envelope("CHK-E-018", "absent", "No content-blocking overlay "
                                       "at load.", None, "NORMATIVE", None, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-E-019 — blank first paint, no fallback
# ---------------------------------------------------------------------------

def check_e019(bundle: dict) -> dict:
    home = next((p for p in bundle.get("pages", []) if p.get("page_type") == "home"), None)
    if home is None:
        return _envelope("CHK-E-019", "not_determinable", "No homepage in sample.", None,
                          "HARD-MECHANICAL/CAUSAL", None)
    rendered = _rendered_for(bundle, home.get("url"))
    locus = {"url": home.get("url")}
    if rendered is None or rendered.get("status") != "ok":
        return _envelope("CHK-E-019", "not_determinable", "Rendered page evidence unavailable.", None,
                          "HARD-MECHANICAL/CAUSAL", None, locus=locus)

    raw_words = home.get("main_text_words", 0)
    rendered_words = rendered.get("main_text_words", 0)
    noscript_words = home.get("noscript", {}).get("words", 0)

    if noscript_words >= 50:
        return _envelope("CHK-E-019", "absent", "Noscript fallback carries substantive "
                          "content.", None, "HARD-MECHANICAL/CAUSAL", None, locus=locus)

    if raw_words < 50 and rendered_words >= 200:
        return _envelope(
            "CHK-E-019", "present",
            f"Homepage: plain HTTP fetch yielded {raw_words} words; no loading indicator "
            f"or noscript present.", "high", "HARD-MECHANICAL/CAUSAL",
            {"summary": "Implement SSR/SSG or a meaningful loading state and noscript "
                         "fallback.", "priority": "high"}, locus=locus)

    return _envelope("CHK-E-019", "absent", "No blank-first-paint pattern detected.", None,
                      "HARD-MECHANICAL/CAUSAL", None, locus=locus)


# ---------------------------------------------------------------------------
# CHK-E-020 — autoplaying media with sound
# ---------------------------------------------------------------------------

def check_e020(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        offenders = [m for m in page.get("media", [])
                     if m.get("autoplay") and not m.get("muted") and not m.get("controls")]
        if offenders:
            findings.append(_envelope(
                "CHK-E-020", "present", f"{len(offenders)} video/audio element(s) autoplay "
                "with sound and no pause/stop mechanism (WCAG 2.2 SC 1.4.2).", "medium",
                "NORMATIVE",
                {"summary": "Add muted to autoplaying video; remove autoplay from audio.",
                 "priority": "medium"}, locus=locus))
        else:
            findings.append(_envelope("CHK-E-020", "absent", "No unmuted autoplaying "
                                       "media without controls.", None, "NORMATIVE", None,
                                       locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-E-021 — images/iframes missing dimensions
# ---------------------------------------------------------------------------

def check_e021(bundle: dict) -> dict:
    affected_pages = set()
    total = 0
    for page in bundle.get("pages", []):
        for img in page.get("images", []):
            if img.get("in_picture"):
                continue
            if img.get("width_attr") is None and img.get("height_attr") is None and \
                    not img.get("css_aspect_ratio"):
                total += 1
                affected_pages.add(page.get("url"))
        for f in page.get("iframes", []):
            if f.get("width_attr") is None and f.get("height_attr") is None:
                total += 1
                affected_pages.add(page.get("url"))

    if total < 3:
        return _envelope("CHK-E-021", "absent", f"{total} affected element(s), below the "
                          "noise floor.", None, "THEORETICAL", None)

    severity = "medium" if (total >= 10 and len(affected_pages) >= 2) else "low"
    return _envelope(
        "CHK-E-021", "present", f"{total} image(s)/iframe(s) lack explicit width/height "
        f"or aspect-ratio, so content reflows during load.", severity, "THEORETICAL",
        {"summary": "Add width/height attributes or CSS aspect-ratio to reserve layout "
                     "space before the resource loads.", "priority": severity})


# ---------------------------------------------------------------------------
# CHK-E-022 — missing landmark/heading integrity
# ---------------------------------------------------------------------------

def check_e022(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        h1_count = sum(1 for h in page.get("headings", []) if h.get("level") == 1)
        no_main = page.get("landmarks", {}).get("main", 0) == 0
        levels = [h["level"] for h in sorted(page.get("headings", []), key=lambda h: h.get("order", 0))]
        skips = any(b - a > 1 for a, b in zip(levels, levels[1:]) if b > a)

        if h1_count == 0 or h1_count > 1:
            findings.append(_envelope(
                "CHK-E-022", "present", f"Page {page.get('url')}: {h1_count} <h1> elements "
                "found. Violates structural conventions (WCAG 2.2 SC 2.4.6).", "high",
                "NORMATIVE/PRACTITIONER",
                {"summary": "Ensure exactly one <h1> per page.", "priority": "high"}, locus=locus))
        elif no_main or skips:
            reason = "missing <main> landmark" if no_main else "heading level skip detected"
            findings.append(_envelope(
                "CHK-E-022", "present", f"Page {page.get('url')}: {reason}. Violates "
                "structural conventions (WCAG 2.2 SC 1.3.1).", "medium",
                "NORMATIVE/PRACTITIONER",
                {"summary": "Add <main> to wrap primary content; fix heading level skips.",
                 "priority": "medium"}, locus=locus))
        else:
            findings.append(_envelope("CHK-E-022", "absent", f"Page {page.get('url')}: "
                                       "landmark and heading structure intact.", None,
                                       "NORMATIVE/PRACTITIONER", None, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-E-023 — ad/promo density exceeds 30% of mobile viewport
# ---------------------------------------------------------------------------

def check_e023(bundle: dict) -> list[dict]:
    findings = []
    for rendered in bundle.get("rendered", []):
        locus = {"url": rendered.get("url")}
        if rendered.get("status") != "ok":
            findings.append(_envelope("CHK-E-023", "not_determinable",
                                       "Rendered page evidence unavailable.", None,
                                       "CORRELATIONAL/NORMATIVE", None, locus=locus))
            continue
        viewport = rendered.get("viewports", {}).get("mobile_375", {})
        regions = viewport.get("ad_regions", [])
        detectors = {r.get("detector") for r in regions}
        total_pct = viewport.get("ad_area_pct_total", 0.0)

        if not regions:
            findings.append(_envelope("CHK-E-023", "absent", "No ad regions detected.",
                                       None, "CORRELATIONAL/NORMATIVE", None, locus=locus))
        elif len(detectors) < 2:
            findings.append(_envelope("CHK-E-023", "not_determinable",
                                       "Only one detection method agrees — insufficient "
                                       "confidence.", None, "CORRELATIONAL/NORMATIVE", None,
                                       locus=locus))
        elif total_pct > 30:
            findings.append(_envelope(
                "CHK-E-023", "present", f"First viewport: ~{total_pct}% of visible area "
                "occupied by advertisements. Exceeds the Better Ads Standard threshold of "
                "30%.", "medium", "CORRELATIONAL/NORMATIVE",
                {"summary": "Reduce ad density below the Better Ads mobile threshold, or "
                             "move ad regions below the fold.", "priority": "medium"},
                locus=locus))
        else:
            findings.append(_envelope("CHK-E-023", "absent", f"Ad density {total_pct}%, "
                                       "within threshold.", None, "CORRELATIONAL/NORMATIVE",
                                       None, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-E-024 — missing trust signals (recommendation-only, single-source rule)
# ---------------------------------------------------------------------------

def check_e024(bundle: dict) -> dict:
    archetype = bundle.get("site", {}).get("archetype")
    if archetype not in COMMERCIAL_ARCHETYPES:
        return _envelope("CHK-E-024", "not_applicable", "Non-commercial archetype: exempt.",
                          None, "CORRELATIONAL", None, recommendation_only=True)

    pages = [p for p in bundle.get("pages", []) if p.get("page_type") in ("home", "about", "contact")]
    missing = []
    if not any(p.get("contact_signals", {}).get("email") or p.get("contact_signals", {}).get("phone")
               for p in pages):
        missing.append("contact information")
    if bundle.get("site", {}).get("scheme") != "https":
        missing.append("HTTPS")

    if missing:
        return _envelope(
            "CHK-E-024", "present", f"Commercial site: no detectable {', '.join(missing)}.",
            None, "CORRELATIONAL",
            {"summary": "Add contact information, organisation name in footer, HTTPS, and "
                         "byline dates on articles. (Proactive — not a confirmed defect.)",
             "priority": "low"}, recommendation_only=True)
    return _envelope("CHK-E-024", "absent", "Commercial trust signals present.", None,
                      "CORRELATIONAL", None, recommendation_only=True)


def evaluate(bundle: dict) -> list[dict]:
    findings: list[dict] = []
    findings.extend(check_e014(bundle))
    findings.extend(check_e015(bundle))
    findings.extend(check_e016(bundle))
    findings.extend(check_e017(bundle))
    findings.extend(check_e018(bundle))
    findings.append(check_e019(bundle))
    findings.extend(check_e020(bundle))
    findings.append(check_e021(bundle))
    findings.extend(check_e022(bundle))
    findings.extend(check_e023(bundle))
    findings.append(check_e024(bundle))
    return findings
