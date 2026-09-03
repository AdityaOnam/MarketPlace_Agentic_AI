"""The seven checks owned by render-extractability-audit: CHK-D-003, D-004, D-005, D-009,
D-010, D-011, D-013. Pure functions over an evidence bundle; no network access.

Reference: render-extractability-audit/SKILL.md and references/checks.md.
"""
from __future__ import annotations

import re

NON_INFORMATIONAL_PAGE_TYPES = {"contact", "login"}
LOW_STRUCTURE_ARCHETYPES = {"legal"}  # page_type, not site archetype, per checks.md guard
NARRATIVE_PAGE_TYPES = {"article"}
VARIANT_OR_LEGAL_PAGE_TYPES = {"legal"}

_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_PRONOUN_START_RE = re.compile(
    r"^(He|She|It|They|We|This|These|Him|Her|Them|Its|Their|His|Hers)\b", re.I
)
_DEFINITION_RE = re.compile(r"\b\w+\s+is\s+(a|an|the)\s+\w+", re.I)
_NUMBER_UNIT_RE = re.compile(
    r"\b\d[\d,.]*\s*(%|percent|million|billion|thousand|km|kg|mb|gb|tb|ms|seconds?|minutes?|"
    r"hours?|days?|years?|users?|customers?|countries?|dollars?|\$)", re.I
)
_COMPARISON_RE = re.compile(r"\b(than|compared to|vs\.?|versus|faster|slower|more than|less than|"
                             r"cheaper|better than|worse than)\b", re.I)


def _envelope(check_id, state, evidence, severity, evidence_strength, suggested_action,
              locus=None, suppressed_by=None):
    return {
        "check_id": check_id, "state": state, "locus": locus or {"url": None, "selector": None},
        "evidence": evidence, "severity": severity, "evidence_strength": evidence_strength,
        "suggested_action": suggested_action, "suppressed_by": suppressed_by or [],
    }


def _find_page(pages: list[dict], page_type: str) -> dict | None:
    for p in pages:
        if p.get("page_type") == page_type:
            return p
    return None


def _homepage(pages: list[dict]) -> dict | None:
    return _find_page(pages, "home")


# ---------------------------------------------------------------------------
# CHK-D-003 — raw-fetch content gap vs. rendered DOM (homepage only)
# ---------------------------------------------------------------------------

def check_d003(bundle: dict) -> dict:
    rendered_list = bundle.get("rendered", [])
    pages = bundle.get("pages", [])
    home = _homepage(pages)

    if home is None:
        return _envelope("CHK-D-003", "not_determinable", "No homepage in the sampled pages.",
                          None, "HARD-MECHANICAL", None)

    home_rendered = next((r for r in rendered_list if r.get("url") == home.get("url")), None)
    if home_rendered is None or home_rendered.get("status") != "ok":
        reason = (home_rendered or {}).get("reason") or "Rendered page evidence unavailable."
        return _envelope("CHK-D-003", "not_determinable", reason, None, "HARD-MECHANICAL", None,
                          locus={"url": home.get("url"), "selector": None})

    raw_words = home.get("main_text_words", 0)
    raw_h1 = sum(1 for h in home.get("headings", []) if h.get("level") == 1)
    rendered_words = home_rendered.get("main_text_words", 0)
    rendered_h1 = home_rendered.get("h1_count", 0)
    noscript_words = home.get("noscript", {}).get("words", 0)

    gap = (rendered_words - raw_words) / rendered_words if rendered_words > 0 else 0.0

    evidence = (
        f"Homepage: raw HTTP fetch contains {raw_words} words of main text and {raw_h1} h1; "
        f"rendered DOM contains {rendered_words} words and {rendered_h1} h1."
    )
    locus = {"url": home.get("url"), "selector": None}
    action = {"summary": "Implement server-side rendering or static generation for the "
                          "homepage; at minimum ensure primary content and the h1 are "
                          "present in the initial HTTP response.", "priority": None}

    if noscript_words > 50 or gap < 0.20:
        return _envelope("CHK-D-003", "absent", evidence, None, "HARD-MECHANICAL", None, locus=locus)

    if raw_h1 == 0 and raw_words < 50 and rendered_words >= 200:
        action["priority"] = "critical"
        return _envelope("CHK-D-003", "present", evidence, "critical", "HARD-MECHANICAL",
                          action, locus=locus)
    if raw_h1 >= 1 and gap >= 0.60:
        action["priority"] = "medium"
        return _envelope("CHK-D-003", "present", evidence, "medium", "HARD-MECHANICAL",
                          action, locus=locus)
    if gap >= 0.20:
        action["priority"] = "low"
        return _envelope("CHK-D-003", "present", evidence, "low", "HARD-MECHANICAL",
                          action, locus=locus)

    return _envelope("CHK-D-003", "absent", evidence, None, "HARD-MECHANICAL", None, locus=locus)


# ---------------------------------------------------------------------------
# CHK-D-004 — thin main content (per page)
# ---------------------------------------------------------------------------

def check_d004(bundle: dict, d003_result: dict | None = None) -> list[dict]:
    pages = bundle.get("pages", [])
    d003_fired = bool(d003_result and d003_result.get("state") == "present")
    findings = []

    for page in pages:
        if page.get("page_type") in NON_INFORMATIONAL_PAGE_TYPES:
            continue
        locus = {"url": page.get("url"), "selector": None}
        if not page.get("extraction_ok", True):
            findings.append(_envelope("CHK-D-004", "not_determinable",
                                       "Content could not be extracted.", None,
                                       "CORRELATIONAL", None, locus=locus))
            continue
        if d003_fired and page.get("page_type") == "home":
            findings.append(_envelope("CHK-D-004", "not_applicable",
                                       "Suppressed: CHK-D-003 fired for this JS-SPA homepage.",
                                       None, "CORRELATIONAL", None, locus=locus,
                                       suppressed_by=["CHK-D-003"]))
            continue
        words = page.get("main_text_words", 0)
        if words < 200:
            findings.append(_envelope(
                "CHK-D-004", "present",
                f"Page {page.get('url')}: main-content extraction yielded {words} words "
                f"after boilerplate removal.",
                "medium", "CORRELATIONAL",
                {"summary": "Add substantive, explicitly-stated content naming the specific "
                             "facts the page exists to convey.", "priority": "medium"},
                locus=locus,
            ))
        else:
            findings.append(_envelope("CHK-D-004", "absent",
                                       f"Page {page.get('url')}: {words} words, above the "
                                       f"thin-content threshold.", None, "CORRELATIONAL",
                                       None, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-D-005 — absent or generic headings (per page, >500 words)
# ---------------------------------------------------------------------------

_GENERIC_HEADING_RE = re.compile(r"^(more|details|info|learn more|read more)$", re.I)


def check_d005(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        if page.get("page_type") in LOW_STRUCTURE_ARCHETYPES or page.get("page_type") in ("faq",):
            continue
        words = page.get("main_text_words", 0)
        if words <= 500:
            continue
        locus = {"url": page.get("url"), "selector": None}
        if not page.get("extraction_ok", True):
            findings.append(_envelope("CHK-D-005", "not_determinable",
                                       "Content could not be extracted.", None, "THEORETICAL",
                                       None, locus=locus))
            continue
        subheadings = [h for h in page.get("headings", []) if h.get("level") in (2, 3)]
        descriptive = [h for h in subheadings if not _GENERIC_HEADING_RE.match((h.get("text") or "").strip())]
        if not descriptive:
            findings.append(_envelope(
                "CHK-D-005", "present",
                f"Page {page.get('url')}: {words} words of body text with "
                f"{len(descriptive)} descriptive subheadings.",
                "low", "THEORETICAL",
                {"summary": "Add descriptive subheadings that state the fact or topic of "
                             "each section.", "priority": "low"},
                locus=locus,
            ))
        else:
            findings.append(_envelope("CHK-D-005", "absent",
                                       f"Page {page.get('url')}: {len(descriptive)} "
                                       f"descriptive subheadings present.", None,
                                       "THEORETICAL", None, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-D-009 — broken internal links
# ---------------------------------------------------------------------------

def check_d009(bundle: dict) -> dict:
    links = bundle.get("links", {})
    if links.get("status") != "ok":
        return _envelope("CHK-D-009", "not_determinable", links.get("reason") or
                          "Internal link check unavailable.", None, "THEORETICAL/CORRELATIONAL", None)

    broken = [r for r in links.get("results", []) if isinstance(r.get("http_status"), int)
              and r["http_status"] >= 400]
    if broken:
        return _envelope(
            "CHK-D-009", "present", f"Found {len(broken)} broken internal link(s).",
            "low", "THEORETICAL/CORRELATIONAL",
            {"summary": "Repair the link's target or replace it; add a 301 redirect if the "
                         "target is genuinely gone.", "priority": "low"},
        )
    return _envelope("CHK-D-009", "absent", "No broken internal links found among "
                      f"{links.get('checked_count', 0)} checked.", None,
                      "THEORETICAL/CORRELATIONAL", None)


# ---------------------------------------------------------------------------
# CHK-D-010 — low extractable-evidence density
# ---------------------------------------------------------------------------

def check_d010(bundle: dict, d004_results: list[dict] | None = None) -> list[dict]:
    d004_by_url = {f["locus"]["url"]: f for f in (d004_results or [])}
    findings = []
    for page in bundle.get("pages", []):
        if page.get("page_type") in NON_INFORMATIONAL_PAGE_TYPES:
            continue
        locus = {"url": page.get("url"), "selector": None}
        d004 = d004_by_url.get(page.get("url"))
        if d004 and d004.get("state") == "present":
            findings.append(_envelope("CHK-D-010", "not_applicable",
                                       "Suppressed: CHK-D-004 (thin content) fired for this page.",
                                       None, "CORRELATIONAL", None, locus=locus,
                                       suppressed_by=["CHK-D-004"]))
            continue
        if not page.get("extraction_ok", True):
            findings.append(_envelope("CHK-D-010", "not_determinable",
                                       "Content could not be extracted.", None, "CORRELATIONAL",
                                       None, locus=locus))
            continue
        text = page.get("main_text", "")
        has_evidence = bool(_DEFINITION_RE.search(text) or _NUMBER_UNIT_RE.search(text)
                             or _COMPARISON_RE.search(text))
        if not has_evidence:
            findings.append(_envelope(
                "CHK-D-010", "present",
                "None of the checked pages contain a definition, numerical fact, or "
                "comparison.", "medium", "CORRELATIONAL",
                {"summary": "Add explicit definitions, numerical facts, or comparisons — the "
                             "shapes an assistant can lift verbatim into an answer.",
                 "priority": "medium"},
                locus=locus,
            ))
        else:
            findings.append(_envelope("CHK-D-010", "absent",
                                       "Page contains at least one definition, numerical "
                                       "fact, or comparison.", None, "CORRELATIONAL", None,
                                       locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-D-011 — pronoun-saturated key claims (home/about only)
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def check_d011(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        if page.get("page_type") not in ("home", "about"):
            continue
        if page.get("page_type") in NARRATIVE_PAGE_TYPES:
            continue
        locus = {"url": page.get("url"), "selector": None}
        if not page.get("extraction_ok", True):
            findings.append(_envelope("CHK-D-011", "not_determinable",
                                       "Content could not be extracted.", None,
                                       "THEORETICAL/HEURISTIC", None, locus=locus))
            continue
        sentences = _split_sentences(page.get("main_text", ""))
        if not sentences:
            findings.append(_envelope("CHK-D-011", "absent", "No sentences to evaluate.",
                                       None, "THEORETICAL/HEURISTIC", None, locus=locus))
            continue
        pronoun_starts = sum(1 for s in sentences if _PRONOUN_START_RE.match(s))
        pct = round(pronoun_starts / len(sentences) * 100)
        if pct > 60:
            findings.append(_envelope(
                "CHK-D-011", "present",
                f"{pct}% of sentences use a pronoun as subject without a preceding "
                f"explicit mention.", "low", "THEORETICAL/HEURISTIC",
                {"summary": "Ensure the first occurrence of each key claim explicitly "
                             "names its subject before any pronoun stands in for it.",
                 "priority": "low"},
                locus=locus,
            ))
        else:
            findings.append(_envelope("CHK-D-011", "absent",
                                       f"{pct}% pronoun-initial sentences, below threshold.",
                                       None, "THEORETICAL/HEURISTIC", None, locus=locus))
    return findings


# ---------------------------------------------------------------------------
# CHK-D-013 — near-duplicate templated content (Jaccard over main_text trigrams)
# ---------------------------------------------------------------------------

def _trigram_set(text: str) -> set[str]:
    words = _WORD_RE.findall(text.lower())
    return {" ".join(words[i:i + 3]) for i in range(len(words) - 2)} if len(words) >= 3 else set()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def check_d013(bundle: dict) -> dict:
    eligible = [p for p in bundle.get("pages", [])
                if p.get("page_type") not in VARIANT_OR_LEGAL_PAGE_TYPES
                and p.get("extraction_ok", True)]
    if len(eligible) < 3:
        return _envelope("CHK-D-013", "not_determinable",
                          "Fewer than 3 eligible pages to compare.", None, "CORRELATIONAL", None)

    trigram_sets = [(p["url"], _trigram_set(p.get("main_text", ""))) for p in eligible]
    high_similarity_pairs = []
    for i in range(len(trigram_sets)):
        for j in range(i + 1, len(trigram_sets)):
            sim = _jaccard(trigram_sets[i][1], trigram_sets[j][1])
            if sim > 0.8:
                high_similarity_pairs.append((trigram_sets[i][0], trigram_sets[j][0], sim))

    if len(high_similarity_pairs) >= 2:  # >=3 pages mutually similar implies >=2 pairs among them
        avg_pct = round(sum(p[2] for p in high_similarity_pairs) / len(high_similarity_pairs) * 100)
        return _envelope(
            "CHK-D-013", "present",
            f"Pages share {avg_pct}% of word trigrams in their main content.", "low",
            "CORRELATIONAL",
            {"summary": "Add unique content to each variant page that answers the specific "
                         "question a reader would have about that variant.", "priority": "low"},
        )
    return _envelope("CHK-D-013", "absent", "No cluster of near-duplicate pages found.",
                      None, "CORRELATIONAL", None)


def evaluate(bundle: dict) -> list[dict]:
    """Run all seven checks in the dependency order the SKILL.md procedure requires
    (D-004 needs D-003's result; D-010 needs D-004's results)."""
    findings: list[dict] = []

    d003 = check_d003(bundle)
    findings.append(d003)

    d004_list = check_d004(bundle, d003_result=d003)
    findings.extend(d004_list)

    findings.extend(check_d005(bundle))
    findings.append(check_d009(bundle))
    findings.extend(check_d010(bundle, d004_results=d004_list))
    findings.extend(check_d011(bundle))
    findings.append(check_d013(bundle))

    return findings
