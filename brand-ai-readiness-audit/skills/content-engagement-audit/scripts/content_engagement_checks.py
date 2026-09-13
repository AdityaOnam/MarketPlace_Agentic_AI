"""The seventeen checks owned by content-engagement-audit: CHK-D-003, D-004, D-005,
D-009, D-010, D-011, D-013 (content extractability, mechanisms B/C) and CHK-E-014 through
CHK-E-024 except E-023 (on-site engagement defects, mechanisms E/F). Pure functions over an
evidence bundle; no network access.

Merged from the formerly-separate render-extractability-audit and engagement-defect-audit
skills on 2026-09-04 (D-025), after the leave-one-skill-out ablation
(harness/ablation.py) found the one genuine cross-skill rule between them -- O-1,
CHK-E-019 deferring to CHK-D-003 -- never actually changed CHK-E-019's outcome on any of
36 real sites, matching D-016's earlier synthetic-scenario finding. O-1 is now applied
in-skill, inline in evaluate() below, the same way CHK-D-004 already self-suppresses
against CHK-D-003 and CHK-D-010 against CHK-D-004 -- there is no longer a reason for these
two mechanisms to be blind to each other, since they are computed by the same evaluate()
call. compose_report.py's cross-skill apply_suppression() is retired accordingly.

CHK-E-023 (mobile ad density) was cut 2026-09-04 as D-018: see the check-level note below.

Reference: content-engagement-audit/SKILL.md and references/checks.md.
"""
from __future__ import annotations

import re

# `home` added in Stage C (2026-09-04): a homepage's job is navigation and framing, not
# comprehensive information, so applying the same word-count/evidence-density bar as a
# content page misjudges it by design. Found firing CHK-D-004 (thin content) on gohugo.io's
# 197-word hero-plus-feature-list homepage -- exactly the kind of terse-by-design page this
# exclusion is for, without touching the checks' behaviour on actual content pages.
NON_INFORMATIONAL_PAGE_TYPES = {"contact", "login", "home"}

# URL fallback for the exclusion above, added by D-030 (2026-09-10). The exclusion is by
# page_type, so it silently stops working when the classifier misfiles a page -- qonto.com's
# `/en/contact-form` is classified `page_type="product"`, so CHK-D-004 called a contact form
# "thin content" at 183 words. Same failure D-029 fixed for CHK-D-006's Organization-JSON-LD
# suppression: the page was what it was, the label was wrong, and a misfiled page is not a
# defect. Deliberately narrow -- three pages corpus-wide match, all on one site.
_NON_INFORMATIONAL_URL_RE = re.compile(
    r"/(contact|contact-us|contact-form|get-in-touch|login|signin|sign-in|log-in)(/|$|\?)", re.I
)


def _is_non_english(page: dict) -> bool:
    """True only when the page *declares* a non-English language. D-031.

    Deliberately one-sided: a missing or malformed `lang` is treated as English, because
    most of this corpus is English and guessing language from text would be a second
    detector to get wrong. This only suppresses a claim where the page itself says the
    English-only detectors do not apply.
    """
    lang = (page.get("lang") or "").strip().lower()
    return bool(lang) and not lang.startswith("en")


# Mirrors the collector's JS_PAYLOAD_BYTES_PER_WORD (extract_page.py); quoted in evidence
# text only, the decision itself is the collector's `js_payload_heavy` flag.
JS_PAYLOAD_BYTES_PER_WORD = 250

JS_RENDER_REASON = ("Page content is not present in the static HTML (a large document with "
                    "almost no extractable text); it appears to be rendered by JavaScript. "
                    "Content density cannot be judged from markup alone -- see CHK-D-003.")


def _content_unmeasurable(page: dict) -> str | None:
    """Why a content-density check cannot judge this page, or None if it can.

    Two conditions, in order: the collector could not extract anything usable
    (`extraction_ok` false), or it extracted a hydration shell (`js_render_suspected`).
    The second is the case CHK-D-003 exists to report; D-004 / D-005 / D-010 / D-013
    calling the same page "thin" or "duplicated" on top of it is the same defect counted
    four times, and on kernel.org-shaped sites it was simply wrong (2026-09-13).
    """
    if not page.get("extraction_ok", True):
        return "Content could not be extracted."
    if page.get("js_render_suspected"):
        return JS_RENDER_REASON
    return None


def _is_non_informational(page: dict) -> bool:
    """A page whose job is a form or a front door, not conveying information -- so the
    word-count checks (CHK-D-004, CHK-D-010) must not grade it as content."""
    if page.get("page_type") in NON_INFORMATIONAL_PAGE_TYPES:
        return True
    if _NON_INFORMATIONAL_URL_RE.search(page.get("url", "") or ""):
        return True
    return _is_variant_of_home(page.get("url", "") or "")


def _is_variant_of_home(url: str) -> bool:
    """`/3.12/`, `/en/`, `/v2/` -- a single version or locale segment and nothing else is
    the homepage of that version or locale, a hub, and is excluded for the same reason
    `home` is. docs.python.org's per-version index pages were being called thin at ~165
    words once the extractor started reading their real `role="main"` region (2026-09-13).
    """
    segs = _path_segments(url)
    return len(segs) == 1 and bool(_VERSION_SEG_RE.match(segs[0]) or _LOCALE_SEG_RE.match(segs[0]))


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
              locus=None, suppressed_by=None, recommendation_only=False, subcheck=None):
    """`subcheck` distinguishes envelopes that share a check_id and a locus but are graded
    separately -- CHK-E-014's static WCAG failures (ceiling `high`) and its contrast
    sub-check (ceiling `medium`, NORMATIVE) are two different judgments about one page,
    not a duplicate. The orchestrator's meta-evaluation keys its duplicate detection on
    (check_id, url, subcheck) for exactly this reason."""
    return {
        "check_id": check_id, "state": state, "locus": locus or {"url": None, "selector": None},
        "evidence": evidence, "severity": severity, "evidence_strength": evidence_strength,
        "suggested_action": suggested_action, "suppressed_by": suppressed_by or [],
        "recommendation_only": recommendation_only, "subcheck": subcheck,
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
    if not home.get("extraction_ok", True):
        # A page whose HTTP fetch failed outright (`status != "ok"`) carries
        # main_text_words=0/headings=[] by construction, which this check's own
        # "raw_h1==0 and raw_words<50" rule would otherwise read as a confirmed render-gap
        # finding -- "we never got the page" is not "the page is empty". Found live on
        # www.gnu.org in the adversarial set (2026-09-04): a fetch failure produced a
        # false 'high' CHK-D-003 finding. `_unavailable_page` sets extraction_ok=False for
        # exactly this reason.
        return _envelope("CHK-D-003", "not_determinable", "Homepage could not be fetched.",
                          None, "HARD-MECHANICAL", None, locus={"url": home.get("url"), "selector": None})

    raw_words = home.get("main_text_words", 0)
    raw_h1 = sum(1 for h in home.get("headings", []) if h.get("level") == 1)
    noscript_words = home.get("noscript", {}).get("words", 0)
    locus = {"url": home.get("url"), "selector": None}

    home_rendered = next((r for r in rendered_list if r.get("url") == home.get("url")), None)
    if home_rendered is None or home_rendered.get("status") != "ok":
        # No rendered evidence available (no headless-browser tool in this environment, or
        # that page's render was abandoned). Per the officials' Q&A, this is re-derived
        # one-sidedly: a static fetch with no h1 and near-no text is a finding on its own —
        # we just cannot confirm whether client-side rendering would have fixed it.
        if noscript_words > 50:
            return _envelope("CHK-D-003", "absent", "Homepage: noscript fallback carries "
                              "substantive content; rendered-DOM comparison unavailable.",
                              None, "HARD-MECHANICAL", None, locus=locus)
        if raw_h1 == 0 and raw_words < 50:
            evidence = (
                f"Homepage: raw HTTP fetch contains {raw_words} words of main text and "
                f"{raw_h1} h1. Rendered page evidence is unavailable in this environment, "
                "so this is a one-sided finding: static HTML alone has no meaningful "
                "content for a non-rendering fetch. It does not confirm the client-rendered "
                "version is broken, only that a fetch without JavaScript execution gets "
                "nothing usable."
            )
            # D-6 (2026-09-12): softened from "Implement SSR/SSG" -- a whole-architecture
            # prescription -- to describing what the audit actually observed and letting
            # the site owner pick the mechanism. Static HTML with no h1 and no text is the
            # observation; how to give a non-rendering crawler something to read
            # (SSR, SSG, pre-render, or a substantive <noscript>) is a choice.
            # Phase 10 P10-3: on the one-sided branch we did NOT measure the rendered
            # DOM, so the action cannot claim the content "materialises only after JS
            # executes". Reword to describe only what we observed: primary content and
            # top-level heading are not present in the static response; the
            # client-rendered state was not measured.
            return _envelope("CHK-D-003", "present", evidence, "high", "HARD-MECHANICAL",
                              {"summary": "Primary content and a top-level heading were "
                                          "not found in the static HTML response for the "
                                          "homepage; the client-rendered state was not "
                                          "measured in this environment. Non-rendering "
                                          "clients see nothing usable from this response. "
                                          "Options the site could consider include "
                                          "server-side rendering, static generation, a "
                                          "partial pre-render of the hero block, or a "
                                          "substantive noscript fallback.",
                                "priority": "high"},
                              locus=locus)
        return _envelope("CHK-D-003", "not_determinable",
                          "Rendered page evidence unavailable, and static HTML has enough "
                          "content that a render gap cannot be inferred one-sidedly.",
                          None, "HARD-MECHANICAL", None, locus=locus)

    rendered_words = home_rendered.get("main_text_words", 0)
    rendered_h1 = home_rendered.get("h1_count", 0)

    gap = (rendered_words - raw_words) / rendered_words if rendered_words > 0 else 0.0

    evidence = (
        f"Homepage: raw HTTP fetch contains {raw_words} words of main text and {raw_h1} h1; "
        f"rendered DOM contains {rendered_words} words and {rendered_h1} h1."
    )
    # D-6 (2026-09-12): softened prescription -- see the note above.
    action = {"summary": "The homepage's primary content and top-level heading are not "
                          "present in the raw HTML the server returns; they materialise "
                          "only after JavaScript executes. Non-rendering clients see "
                          "nothing usable. Options for the site to consider include "
                          "server-side rendering, static generation, a partial pre-render "
                          "of the hero block, or a substantive noscript fallback.",
              "priority": None}

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
    """`d003_result` is accepted but no longer consulted: since Stage C (2026-09-04) `home`
    is in `NON_INFORMATIONAL_PAGE_TYPES` and is skipped below regardless of whether
    CHK-D-003 fired, which is a strict superset of the old `d003_fired`-gated suppression
    -- D-004 now never evaluates the homepage at all, so the "four findings for one defect"
    case D-016 already proved unreachable stays unreachable. Kept as a parameter rather than
    removed so the orchestrator's call site (which still passes it for CHK-D-010's own
    `d004_results` chaining) does not need a matching signature change.
    """
    pages = bundle.get("pages", [])
    findings = []

    for page in pages:
        if _is_non_informational(page):
            continue
        locus = {"url": page.get("url"), "selector": None}
        unmeasurable = _content_unmeasurable(page)
        if unmeasurable:
            findings.append(_envelope("CHK-D-004", "not_determinable", unmeasurable, None,
                                       "CORRELATIONAL", None, locus=locus))
            continue
        words = page.get("main_text_words", 0)
        if words < 200:
            findings.append(_envelope(
                "CHK-D-004", "present",
                f"Page {page.get('url')}: main-content extraction yielded {words} words "
                f"after boilerplate removal.",
                "medium", "CORRELATIONAL",
                {"summary": "The page's main content is thin; a machine reader would "
                             "benefit from additional substantive text that explicitly "
                             "names the facts the page exists to convey.",
                             "priority": "medium"},
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
        unmeasurable = _content_unmeasurable(page)
        if unmeasurable:
            findings.append(_envelope("CHK-D-005", "not_determinable", unmeasurable, None,
                                       "THEORETICAL", None, locus=locus))
            continue
        subheadings = [h for h in page.get("headings", []) if h.get("level") in (2, 3)]
        descriptive = [h for h in subheadings if not _GENERIC_HEADING_RE.match((h.get("text") or "").strip())]
        if not descriptive:
            findings.append(_envelope(
                "CHK-D-005", "present",
                f"Page {page.get('url')}: {words} words of body text with "
                f"{len(descriptive)} descriptive subheadings.",
                "low", "THEORETICAL",
                {"summary": "Consider whether clearer descriptive subheadings would help "
                             "readers identify the fact or topic of each section.",
                 "priority": "low"},
                locus=locus, recommendation_only=True,
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
        # Phase 10 P10-2: enumerate up to three affected destinations with their
        # response codes and where they were linked from, so the evidence names the
        # actual failing pairs rather than only a count. The recommendation locus
        # points at the source page of the first affected link (or the destination
        # if that is not recorded), never `null`.
        broken_sorted = sorted(
            broken,
            key=lambda r: (r.get("from_page") or "", r.get("url") or ""),
        )
        sample = broken_sorted[:3]
        parts = []
        for r in sample:
            parts.append(
                f"{r.get('url')} responded {r.get('http_status')} "
                f"when followed from {r.get('from_page') or 'the sample'}"
            )
        more = ""
        if len(broken) > len(sample):
            more = f"; {len(broken) - len(sample)} further broken link(s) not enumerated"
        evidence = (f"Found {len(broken)} broken internal link(s): "
                    + "; ".join(parts) + more + ".")
        first_locus_url = sample[0].get("from_page") or sample[0].get("url")
        return _envelope(
            "CHK-D-009", "present", evidence,
            "low", "THEORETICAL/CORRELATIONAL",
            {"summary": "The site would benefit from reviewing the affected internal "
                         "links: possible responses include updating each destination, "
                         "replacing the link, or using a permanent redirect when a "
                         "resource has moved. The observed response codes describe "
                         "what the checker saw, not the reason a page is unavailable.",
             "priority": "low"},
            recommendation_only=True,
            locus={"url": first_locus_url, "selector": None} if first_locus_url else None,
        )
    return _envelope("CHK-D-009", "absent", "No broken internal links found among "
                      f"{links.get('checked_count', 0)} checked.", None,
                      "THEORETICAL/CORRELATIONAL", None)


# ---------------------------------------------------------------------------
# CHK-D-010 — low extractable-evidence density
# ---------------------------------------------------------------------------

def check_d010(bundle: dict, d004_results: list[dict] | None = None) -> list[dict]:
    """Demoted to recommendation-only in Stage C (2026-09-04): the three-pattern regex
    proxy for 'evidence density' (`_DEFINITION_RE`/`_NUMBER_UNIT_RE`/`_COMPARISON_RE`) fired
    on 17 of 34 real dev/negative-control sites, including developer.mozilla.org and
    docs.djangoproject.com -- narrative-but-well-written pages that legitimately lack the
    three literal sentence shapes without being defective. The underlying mechanism
    (evidence density correlates with GEO absorption) is real and cited; this narrow
    proxy is too imprecise to assert as a confirmed defect, the same class of demotion
    D-012 already applied to CHK-E-024.
    """
    archetype = bundle.get("site", {}).get("archetype")
    if archetype in {"unknown", "brochure"}:
        return [_envelope(
            "CHK-D-010", "not_applicable",
            f"Archetype {archetype!r} carries insufficient signal for this check.",
            None, "NORMATIVE", None, recommendation_only=True,
        )]

    d004_by_url = {f["locus"]["url"]: f for f in (d004_results or [])}
    findings = []
    for page in bundle.get("pages", []):
        if _is_non_informational(page):
            continue
        locus = {"url": page.get("url"), "selector": None}
        d004 = d004_by_url.get(page.get("url"))
        if d004 and d004.get("state") == "present":
            findings.append(_envelope("CHK-D-010", "not_applicable",
                                       "Suppressed: CHK-D-004 (thin content) fired for this page.",
                                       None, "CORRELATIONAL", None, locus=locus,
                                       suppressed_by=["CHK-D-004"]))
            continue
        unmeasurable = _content_unmeasurable(page)
        if unmeasurable:
            findings.append(_envelope("CHK-D-010", "not_determinable", unmeasurable, None,
                                       "CORRELATIONAL", None, locus=locus))
            continue
        if _is_non_english(page):
            # D-031 (2026-09-10): all three evidence-shape detectors are English-only --
            # `_DEFINITION_RE` wants "is a/an/the", `_NUMBER_UNIT_RE`'s unit list is English
            # words, `_COMPARISON_RE` wants "than"/"vs"/"faster". On a German or Japanese
            # page they cannot match no matter how evidence-dense the writing is, so
            # "no definition, numerical fact, or comparison" is a claim about the detector,
            # not about the page. Found on qonto.com's `/de-at` pages, whose text carries
            # "Ab 9 EUR/Monat" and "2.000+ Integrationen" and was reported as evidence-free.
            # Not measurable is not the same as absent.
            findings.append(_envelope(
                "CHK-D-010", "not_determinable",
                f"Page language is {page.get('lang')!r}; this check's definition, "
                "number-unit and comparison detectors are English-only.",
                None, "CORRELATIONAL", None, locus=locus, recommendation_only=True))
            continue
        text = page.get("main_text", "")
        has_evidence = bool(_DEFINITION_RE.search(text) or _NUMBER_UNIT_RE.search(text)
                             or _COMPARISON_RE.search(text))
        if not has_evidence:
            # Phase 10 P10-3: what we actually observed is that this page's static
            # text matched none of the English detector's three sentence patterns
            # (definition, number+unit, comparison). Do not overstate that as "no
            # facts" or "none of the pages" — the evidence is page- and
            # detector-scoped.
            findings.append(_envelope(
                "CHK-D-010", "present",
                "This page's static text did not match any of the check's three "
                "English sentence-shape detectors (is-a-definition, number+unit, "
                "comparison).", None, "CORRELATIONAL",
                {"summary": "The static text on this page did not surface the "
                             "quotable sentence shapes — a definition, a number "
                             "with a unit, or a comparison — that assistants can "
                             "lift verbatim into an answer. Consider whether the "
                             "page would benefit from more of that structure. "
                             "(Proactive — not a confirmed defect.)", "priority": "low"},
                locus=locus, recommendation_only=True,
            ))
        else:
            findings.append(_envelope("CHK-D-010", "absent",
                                       "Page contains at least one definition, numerical "
                                       "fact, or comparison.", None, "CORRELATIONAL",
                                       None, locus=locus, recommendation_only=True))
    return findings


# ---------------------------------------------------------------------------
# CHK-D-011 — pronoun-saturated key claims (home/about only)
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def check_d011(bundle: dict) -> list[dict]:
    """Demoted to recommendation-only by D-027 (2026-09-09): R-1 hand-verification opened
    all three cited sources (P-01.05, P-01.02, P-06.04) and found none discuss pronouns,
    ambiguous subjects, or unclear referents -- a genuine evidence gap, not a citation
    mismatch. Kept as a proactive recommendation rather than cut, since the underlying
    advice is defensible on its own terms even without academic support (same demotion
    class as CHK-D-010 and CHK-E-024, for a different reason: those had weak/single-source
    support, this has none at all)."""
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
                                       None, "THEORETICAL/HEURISTIC", None, locus=locus,
                                       recommendation_only=True))
            continue
        pronoun_starts = sum(1 for s in sentences if _PRONOUN_START_RE.match(s))
        pct = round(pronoun_starts / len(sentences) * 100)
        if pct > 60:
            findings.append(_envelope(
                "CHK-D-011", "present",
                f"{pct}% of sentences use a pronoun as subject without a preceding "
                f"explicit mention.", "low", "THEORETICAL/HEURISTIC",
                {"summary": "Ensure the first occurrence of each key claim explicitly "
                             "names its subject before any pronoun stands in for it. "
                             "(Proactive — not a confirmed defect.)",
                 "priority": "low"},
                locus=locus, recommendation_only=True,
            ))
        else:
            findings.append(_envelope("CHK-D-011", "absent",
                                       f"{pct}% pronoun-initial sentences, below threshold.",
                                       None, "THEORETICAL/HEURISTIC", None, locus=locus,
                                       recommendation_only=True))
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


# D-10 (2026-09-12): two page URLs whose paths differ only in a version-like segment
# (`/en/5.0/x` vs `/en/5.1/x`, `/en/stable/x` vs `/en/dev/x`) or a locale-like segment
# (`/x` vs `/in/x`, `/en/x` vs `/de/x`) are describing the same document for a different
# release or a different language, not a duplicate content problem. D-013 fired on
# versioned Django docs and locale-variant weebly pages; the fix is `rel=canonical`, not
# "add unique content to each variant". These pairs are exempt from the near-duplicate
# count; when the resulting cluster is versioned, the recommendation says so.
_VERSION_SEG_RE = re.compile(
    r"^(v?\d+(?:\.\d+)*|stable|latest|current|dev|main|master|next|beta|alpha|rc\d*)$",
    re.I,
)
_LOCALE_SEG_RE = re.compile(
    # Phase 10 P10-6: also match ISO 639 three-letter language codes and BCP-47
    # tags with a script subtag ("zh-Hans", "sr-Latn"). Mozilla's root sample contains
    # /ach/, /af/, /an/, /ar/ — the earlier two-letter-only regex missed /ach/ (three
    # letters), which was one root cause of the false 100%-duplicate report.
    r"^([a-z]{2,3}([_-][a-z]{2,4})?|in|us|uk|eu|au|ca|nz|asia|emea|apac)$",
    re.I,
)


def _path_segments(url: str) -> list[str]:
    from urllib.parse import urlparse
    return [s for s in (urlparse(url).path or "").split("/") if s]


def _variant_kind(url_a: str, url_b: str) -> str | None:
    """Return 'versioned', 'localised', or None. Two URLs are a version/locale variant
    pair iff their path segments are equal length and differ at exactly one position,
    where both differing segments match the same version or locale pattern.

    Phase 10 P10-6: additionally, `/` (site root) vs `/<locale>/` (locale-root) counts
    as a `localised` variant — Mozilla's root sample paired `www.mozilla.org/` with
    `www.mozilla.org/ach/` etc., which the earlier equal-length rule refused to
    classify as a variant even though they are alternate roots of the same document."""
    a = _path_segments(url_a)
    b = _path_segments(url_b)
    # Root vs single-locale-segment: /  and  /<locale>/  are localised roots.
    if (len(a) == 0 and len(b) == 1 and _LOCALE_SEG_RE.match(b[0])) or \
       (len(b) == 0 and len(a) == 1 and _LOCALE_SEG_RE.match(a[0])):
        return "localised"
    if len(a) != len(b) or len(a) < 1:
        return None
    diffs = [(i, a[i], b[i]) for i in range(len(a)) if a[i] != b[i]]
    if len(diffs) != 1:
        return None
    _, sa, sb = diffs[0]
    if _VERSION_SEG_RE.match(sa) and _VERSION_SEG_RE.match(sb):
        return "versioned"
    if _LOCALE_SEG_RE.match(sa) and _LOCALE_SEG_RE.match(sb):
        return "localised"
    return None


def check_d013(bundle: dict) -> dict:
    """Demoted to recommendation-only by D-027 (2026-09-09): R-1 hand-verification opened
    both cited sources (P-01.09, P-06.03) and found neither discusses duplicate/templated
    content or cross-page text similarity -- a genuine evidence gap, not a citation
    mismatch. Kept as a proactive recommendation rather than cut; see check_d011's
    docstring for the same reasoning."""
    eligible = [p for p in bundle.get("pages", [])
                if p.get("page_type") not in VARIANT_OR_LEGAL_PAGE_TYPES
                and p.get("extraction_ok", True)
                and not p.get("js_render_suspected")]
    if len(eligible) < 3:
        return _envelope("CHK-D-013", "not_determinable",
                          "Fewer than 3 eligible pages to compare.", None, "CORRELATIONAL", None)

    heavy = {p["url"] for p in eligible if p.get("js_payload_heavy")}
    trigram_sets = [(p["url"], _trigram_set(p.get("main_text", ""))) for p in eligible]
    high_similarity_pairs = []  # (ua, ub, sim, inter, union)
    variant_pairs = []  # (url_a, url_b, sim, kind) -- excluded from the count, reported
    js_pairs = []       # identical static text where at least one side is a script shell
    for i in range(len(trigram_sets)):
        for j in range(i + 1, len(trigram_sets)):
            a_set = trigram_sets[i][1]
            b_set = trigram_sets[j][1]
            # Phase 10 P10-6: guard against empty trigram sets producing a bogus 100%
            # via _jaccard's a==b==empty branch. Empty trigram sets are unmeasurable,
            # not identical: skip the pair rather than assert similarity.
            if not a_set or not b_set:
                continue
            sim = _jaccard(a_set, b_set)
            if sim <= 0.8:
                continue
            ua, ub = trigram_sets[i][0], trigram_sets[j][0]
            kind = _variant_kind(ua, ub)
            if kind:
                variant_pairs.append((ua, ub, sim, kind))
            elif ua in heavy or ub in heavy:
                js_pairs.append((ua, ub, sim))
            else:
                inter = len(a_set & b_set)
                union = len(a_set | b_set)
                high_similarity_pairs.append((ua, ub, sim, inter, union))

    # Identical static text between an index and its detail pages, where the detail pages
    # are hundreds of bytes of script per extracted word, is not duplicated content -- it
    # is content the markup does not carry. brianlovin.com's /ama and /ama/<id> pages
    # share the same 236-word question list in HTML while each answer lives in a JSON
    # payload (judge review, 2026-09-13). Judging duplication from that would be a
    # measurement of the crawler's blindness, not of the site.
    if js_pairs and not high_similarity_pairs:
        urls = sorted({u for pair in js_pairs for u in pair[:2]})
        return _envelope(
            "CHK-D-013", "not_determinable",
            f"{len(urls)} pages share the same static text, but their HTML is dominated by "
            f"script payload (over {JS_PAYLOAD_BYTES_PER_WORD} bytes per extracted word). "
            f"Their content appears to be delivered by JavaScript, so duplication cannot be "
            f"judged from the markup a non-rendering crawler receives.",
            None, "CORRELATIONAL", None, recommendation_only=True)

    if len(high_similarity_pairs) >= 2:  # >=3 pages mutually similar implies >=2 pairs among them
        avg_pct = round(sum(p[2] for p in high_similarity_pairs) / len(high_similarity_pairs) * 100)
        # Phase 10 P10-6: name the actual matched pairs (up to three) with their
        # intersection/union counts so the reader can recompute the similarity and see
        # which URLs were compared. Locus points at the first matched pair's first URL.
        sorted_pairs = sorted(high_similarity_pairs, key=lambda p: -p[2])
        sample = sorted_pairs[:3]
        pair_evidence = []
        for ua, ub, sim, inter, union in sample:
            pair_evidence.append(
                f"{ua} and {ub}: {inter}/{union} trigrams shared ({round(sim*100)}%)"
            )
        more = ""
        if len(sorted_pairs) > len(sample):
            more = f"; {len(sorted_pairs) - len(sample)} further high-similarity pair(s) not enumerated"
        evidence = (
            f"{len(sorted_pairs)} page pair(s) share more than 80% of word trigrams "
            f"in their main content (average {avg_pct}%): "
            + "; ".join(pair_evidence) + more + "."
        )
        first_url = sample[0][0] if sample else None
        return _envelope(
            "CHK-D-013", "present", evidence, "low",
            "CORRELATIONAL",
            {"summary": "Consider whether each page would benefit from content that "
                         "answers the distinct question a reader brings to it. The "
                         "similarity was measured over the static main-text trigrams "
                         "recorded above; the counts are recomputable from the same "
                         "text. (Proactive — not a confirmed defect.)",
             "priority": "low"},
            recommendation_only=True,
            locus={"url": first_url, "selector": None} if first_url else None,
        )
    # D-10 (2026-09-12): a cluster made entirely of version or locale variants is not a
    # duplicate-content defect and telling the owner to "add unique content" is actively
    # wrong -- version and locale variants are supposed to be near-identical. When only
    # variant pairs cross the threshold, report the pattern and steer to a canonical fix.
    if variant_pairs:
        kinds = sorted({k for _, _, _, k in variant_pairs})
        kind_label = " and ".join(kinds)
        return _envelope(
            "CHK-D-013", "present",
            f"Near-duplicate pairs on this site are {kind_label} variants of the same "
            f"underlying document ({len(variant_pairs)} pair(s) found). This is expected "
            f"structure, not duplicated content.",
            "low", "CORRELATIONAL",
            {"summary": "Consider whether the variants would benefit from a documented "
                         "canonical-URL strategy: one current or stable release for versions, "
                         "and a language selector with per-locale self-canonicals for locales. "
                         "The content itself is expected to remain near-identical. "
                         "(Proactive — not a confirmed defect.)", "priority": "low"},
            recommendation_only=True,
        )
    return _envelope("CHK-D-013", "absent", "No cluster of near-duplicate pages found.",
                      None, "CORRELATIONAL", None, recommendation_only=True)


NON_DESCRIPTIVE_LINK_TEXT = {
    "click here", "here", "read more", "more", "learn more", "this link", "details",
    "info", "click", "tap", "view", "see",
}
COMMERCIAL_ARCHETYPES = {"ecommerce", "saas_marketing", "news_editorial", "local_business"}
PERSONAL_ARCHETYPES = {"personal", "hobby", "portfolio"}


def _rendered_for(bundle: dict, url: str) -> dict | None:
    return next((r for r in bundle.get("rendered", []) if r.get("url") == url), None)


# ---------------------------------------------------------------------------
# CHK-E-014 — machine-detectable WCAG failures (6 sub-checks)
# ---------------------------------------------------------------------------

_E014_FIX_MAP = {
    "missing lang attribute":
        "a declared page language",
    "missing alt on a non-decorative image":
        "descriptive alternative text for informative images",
    "link with no accessible name":
        "accessible names for links",
    "button with no accessible name":
        "accessible names for buttons",
    "unlabelled form control":
        "programmatic labels for form controls",
}


def _e014_action_for(violations: list[str]) -> str:
    """Build the E-014 fix summary from only the violations that fired. D-7 (2026-09-12):
    the previous bundled action ("Add lang, alt text, accessible names, labels") named
    fixes for defects that didn't fire on that page -- flagged as "broader than the
    demonstrated defect" by outside review."""
    fixes = []
    for v in violations:
        # Strip an "N link(s)"/"N button(s)" count prefix so plural variants share one
        # fix template.
        key = re.sub(r"^\d+\s+", "", v).replace("(s)", "")
        key = re.sub(r"^(link|button)s? with", r"\1 with", key)
        fix = _E014_FIX_MAP.get(key)
        if fix and fix not in fixes:
            fixes.append(fix)
    if not fixes:
        return "Consider how the accessibility violations named in the evidence affect this page."
    if len(fixes) == 1:
        return f"Consider whether this page would benefit from {fixes[0]}."
    return "Consider whether this page would benefit from " + "; ".join(fixes) + "."


def check_e014(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        if not page.get("extraction_ok", True):
            # A page whose fetch failed outright has lang=None, images=[], form_controls=[]
            # by construction, which this loop would otherwise read as confirmed WCAG
            # violations on a page we never actually got. Found live on www.gnu.org in the
            # adversarial set (2026-09-04).
            findings.append(_envelope("CHK-E-014", "not_determinable",
                                       "Page could not be fetched.", None, "HARD-MECHANICAL",
                                       None, locus=locus, subcheck="wcag_static"))
            continue
        violations: list[str] = []

        if page.get("lang") is None:
            violations.append("missing lang attribute")
        for img in page.get("images", []):
            # `decorative_hint` is aria-hidden/role=presentation: an explicit, correct
            # marking that the image carries no information. Treating it as a violation
            # penalises exactly the sites that got accessibility right.
            if img.get("alt") is None and not img.get("decorative_hint"):
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
                {"summary": _e014_action_for(violations), "priority": "high"}, locus=locus,
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
                {"summary": "Consider whether stronger foreground/background contrast "
                             "would improve readability; WCAG AA uses 4.5:1 for normal "
                             "text and 3:1 for large text.", "priority": "medium"}, locus=locus,
                recommendation_only=True,
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
        if not page.get("extraction_ok", True):
            findings.append(_envelope("CHK-E-015", "not_determinable",
                                       "Page could not be fetched.", None, "NORMATIVE", None,
                                       locus=locus, subcheck="viewport_meta"))
            continue
        viewport = page.get("meta", {}).get("viewport")
        if viewport is None:
            findings.append(_envelope(
                "CHK-E-015", "present", f"Page {page.get('url')}: missing viewport meta "
                "tag.", "medium", "NORMATIVE",
                {"summary": "Consider whether declaring a mobile viewport would help the "
                             "page match the device width at its initial scale.",
                 "priority": "medium"}, locus=locus, recommendation_only=True,
                subcheck="viewport_meta"))
        else:
            scale_match = _MAX_SCALE_RE.search(viewport)
            zoom_blocked = "user-scalable=no" in viewport.replace(" ", "").lower() or \
                (scale_match and float(scale_match.group(1)) < 2)
            if zoom_blocked:
                findings.append(_envelope(
                    "CHK-E-015", "present", f"Page {page.get('url')}: viewport meta "
                    "disables user zoom. Violates WCAG 2.2 SC 1.4.4.", "high", "NORMATIVE",
                    {"summary": "Consider whether allowing user zoom by avoiding restrictive "
                                 "scaling constraints would better support WCAG 2.2 SC 1.4.4.",
                     "priority": "high"}, locus=locus, recommendation_only=True,
                    subcheck="viewport_meta"))
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
                {"summary": "Consider whether responsive-layout adjustments would prevent "
                             "content from overflowing a 375px viewport.",
                 "priority": "medium"}, locus=locus, recommendation_only=True,
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
        if not page.get("extraction_ok", True):
            findings.append(_envelope("CHK-E-017", "not_determinable",
                                       "Page could not be fetched.", None,
                                       "NORMATIVE/THEORETICAL", None, locus=locus))
            continue
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
                {"summary": "A material share of the page's link text is non-descriptive "
                             "('click here', 'read more', 'here'), which reduces both "
                             "screen-reader and crawler comprehension of what each link "
                             "leads to.", "priority": "medium"}, locus=locus))
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

    locus = {"url": home.get("url")}
    if not home.get("extraction_ok", True):
        # Mirrors CHK-D-003's same fix: a homepage whose fetch failed outright has
        # main_text_words=0 by construction, which this check's own "raw_words<50" rule
        # would otherwise read as a confirmed blank-first-paint finding. Found live on
        # www.gnu.org in the adversarial set (2026-09-04) -- masked there only by O-1
        # deferring to CHK-D-003, which does not protect a site where D-003 doesn't
        # independently fire.
        return _envelope("CHK-E-019", "not_determinable", "Homepage could not be fetched.",
                          None, "HARD-MECHANICAL/CAUSAL", None, locus=locus)
    raw_words = home.get("main_text_words", 0)
    noscript_words = home.get("noscript", {}).get("words", 0)

    if noscript_words >= 50:
        return _envelope("CHK-E-019", "absent", "Noscript fallback carries substantive "
                          "content.", None, "HARD-MECHANICAL/CAUSAL", None, locus=locus)

    rendered = _rendered_for(bundle, home.get("url"))
    if rendered is None or rendered.get("status") != "ok":
        # No rendered evidence available. Re-derived one-sidedly from static HTML + noscript
        # per the officials' Q&A: a near-empty raw fetch with no noscript fallback is itself
        # the finding — we just cannot confirm the rendered DOM would have filled it in.
        if raw_words < 50:
            return _envelope(
                "CHK-E-019", "present",
                f"Homepage: plain HTTP fetch yielded {raw_words} words and no noscript "
                f"fallback ({noscript_words} words). Rendered page evidence is unavailable "
                "in this environment, so this is a one-sided finding: static HTML alone is "
                "effectively blank to a non-rendering client.", "high",
                "HARD-MECHANICAL/CAUSAL",
                {"summary": "Non-rendering clients receive a near-empty page and no "
                             "noscript fallback. Consider whether server-side rendering, "
                             "static generation, or a noscript block would improve "
                             "availability to those clients.", "priority": "high"},
                locus=locus)
        return _envelope("CHK-E-019", "not_determinable",
                          "Rendered page evidence unavailable, and static HTML has enough "
                          "content that a blank-first-paint gap cannot be inferred "
                          "one-sidedly.", None, "HARD-MECHANICAL/CAUSAL", None, locus=locus)

    rendered_words = rendered.get("main_text_words", 0)
    if raw_words < 50 and rendered_words >= 200:
        return _envelope(
            "CHK-E-019", "present",
            f"Homepage: plain HTTP fetch yielded {raw_words} words; no loading indicator "
            f"or noscript present.", "high", "HARD-MECHANICAL/CAUSAL",
            {"summary": "A non-rendering client sees a near-empty page while the "
                         "rendered DOM has substantial content. Consider whether "
                         "server-side rendering, static generation, a loading state, "
                         "or a noscript fallback would improve availability to those "
                         "clients.", "priority": "high"}, locus=locus)

    return _envelope("CHK-E-019", "absent", "No blank-first-paint pattern detected.", None,
                      "HARD-MECHANICAL/CAUSAL", None, locus=locus)


# ---------------------------------------------------------------------------
# CHK-E-020 — autoplaying media with sound
# ---------------------------------------------------------------------------

def check_e020(bundle: dict) -> list[dict]:
    findings = []
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        if not page.get("extraction_ok", True):
            findings.append(_envelope("CHK-E-020", "not_determinable",
                                       "Page could not be fetched.", None, "NORMATIVE", None,
                                       locus=locus))
            continue
        offenders = [m for m in page.get("media", [])
                     if m.get("autoplay") and not m.get("muted") and not m.get("controls")]
        if offenders:
            findings.append(_envelope(
                "CHK-E-020", "present", f"{len(offenders)} video/audio element(s) autoplay "
                "with sound and no pause/stop mechanism (WCAG 2.2 SC 1.4.2).", "medium",
                "NORMATIVE",
                {"summary": "Sound-on autoplay violates WCAG 2.2 SC 1.4.2 and typically "
                             "drives away visitors without a pause/stop control.",
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
    """Demoted to recommendation-only in Stage C (2026-09-04): fired on 26 of 34 real
    dev/negative-control sites -- near-universal, exactly as PLAN.md §5 already predicted
    ("CLS has no perception research behind it -- Google's own threshold documentation says
    so"). `THEORETICAL` evidence strength was already the lowest tier and severity was
    already capped below high, but a signal this common cannot function as a differentiated
    defect claim; explicit dimensions remain good, actionable advice, so it moves to
    `recommendations[]` rather than being cut outright.
    """
    # Phase 10 P10-2 + P10-3: count per page so the report can name the first
    # affected page as the locus, list per-page counts as instances, and phrase the
    # evidence in terms of the static markup we can measure — not in terms of layout
    # shift, which requires rendered geometry we do not have.
    per_page: list[tuple[str, int]] = []
    total = 0
    for page in bundle.get("pages", []):
        page_count = 0
        for img in page.get("images", []):
            if img.get("in_picture"):
                continue
            if img.get("width_attr") is None and img.get("height_attr") is None and \
                    not img.get("css_aspect_ratio"):
                page_count += 1
        for f in page.get("iframes", []):
            if f.get("width_attr") is None and f.get("height_attr") is None:
                page_count += 1
        if page_count:
            per_page.append((page.get("url") or "", page_count))
            total += page_count

    if total < 3:
        return _envelope("CHK-E-021", "absent", f"{total} affected element(s), below the "
                          "noise floor.", None, "THEORETICAL", None, recommendation_only=True)

    per_page.sort(key=lambda t: t[0])
    first_url = per_page[0][0] if per_page else None
    instances = [{"url": u, "count": c} for u, c in per_page]
    severity = "low"
    return _envelope(
        "CHK-E-021", "present",
        f"{total} image(s)/iframe(s) across {len(per_page)} page(s) declare no explicit "
        f"width/height attributes and no CSS aspect-ratio in their static markup.",
        severity, "THEORETICAL",
        {"summary": "Some images and iframes lack explicit width/height or CSS "
                     "aspect-ratio in the static markup, which is a possible "
                     "layout-stability risk during load. Actual rendered layout shift "
                     "was not measured. (Proactive — not a confirmed defect.)",
         "priority": severity}, recommendation_only=True,
        locus={"url": first_url, "selector": None, "instances": instances}
              if first_url else None)


# ---------------------------------------------------------------------------
# CHK-E-022 — missing landmark/heading integrity
# ---------------------------------------------------------------------------

def check_e022(bundle: dict) -> list[dict]:
    findings = []
    archetype = bundle.get("site", {}).get("archetype")
    for page in bundle.get("pages", []):
        locus = {"url": page.get("url")}
        if not page.get("extraction_ok", True):
            # A page whose fetch failed outright has headings=[]/landmarks={} by
            # construction, which read as "no h1 element found" -- a confirmed 'high'
            # finding on a page we never actually got. Found live on www.gnu.org in the
            # adversarial set (2026-09-04).
            findings.append(_envelope("CHK-E-022", "not_determinable",
                                       "Page could not be fetched.", None,
                                       "NORMATIVE/PRACTITIONER", None, locus=locus))
            continue
        h1_count = sum(1 for h in page.get("headings", []) if h.get("level") == 1)
        no_main = page.get("landmarks", {}).get("main", 0) == 0
        levels = [h["level"] for h in sorted(page.get("headings", []), key=lambda h: h.get("order", 0))]
        skips = any(b - a > 1 for a, b in zip(levels, levels[1:]) if b > a)

        # Only *zero* h1 is a defect. The multiple-h1 branch was removed on 2026-09-04
        # after the Stage B screen: it cited WCAG 2.2 SC 2.4.6, which requires headings to
        # *describe topic or purpose* and says nothing about how many h1 elements a page
        # may have. HTML5 sectioning permits more than one. The check was enforcing a style
        # preference under a normative citation that does not support it -- a false
        # positive at the framing level, which D-011 exists to prevent.
        # D-17 (2026-09-12): four judges across four sites said "exactly one h1" and
        # "Violates WCAG 2.2 SC 1.3.1" over-state the normative basis. WCAG 2.4.6 asks
        # for descriptive headings, not a count. Missing <h1>, <main> absence, and
        # heading skips are structural conventions of HTML5 sectioning aligned with
        # WCAG 1.3.1/2.4.6, not direct failures of them. Severity/strength are already
        # NORMATIVE/PRACTITIONER; the prose is now matched to that label.
        if h1_count == 0:
            # Phase 8 judge review called this D-005, but the missing-h1 detector is
            # actually E-022; D-005 is the already-low long-page subheading check.
            # Preserve the stronger ceiling only where page hierarchy is central to the
            # vertical, cap it at medium elsewhere, and keep personal sites low.
            if archetype in PERSONAL_ARCHETYPES:
                severity = "low"
            elif archetype in {"ecommerce", "news_editorial", "documentation"}:
                severity = "high"
            else:
                severity = "medium"
            findings.append(_envelope(
                "CHK-E-022", "present",
                f"Page {page.get('url')}: no <h1> element found, so the page states no "
                "primary topic. Structural convention aligned with WCAG 2.2 SC 1.3.1 "
                f"(Info and Relationships) and 2.4.6 (Headings and Labels).", severity,
                "NORMATIVE/PRACTITIONER",
                {"summary": "The page has no top-level heading, so a crawler cannot "
                             "identify its primary topic from the document structure.",
                 "priority": severity}, locus=locus, subcheck="no_h1"))
        elif no_main or skips:
            # B-3 (2026-09-12): action is built from only the condition that fired, not
            # a bundled string naming both fixes. A page with <main> present and only a
            # heading skip was being told to "Add <main>" -- a fix for a defect the
            # page didn't have, the disconnected-action pattern the officials called
            # out (OFFICIALS-QA.md §3.4).
            reasons = []
            advice = []
            subcheck_parts = []
            if no_main:
                reasons.append("no <main> landmark wraps the primary content")
                advice.append("the primary content is not wrapped in a <main> landmark")
                subcheck_parts.append("no_main")
            if skips:
                reasons.append("heading levels skip (e.g. h2 -> h4 with no h3 between)")
                advice.append("heading levels skip, breaking the outline a crawler builds")
                subcheck_parts.append("heading_skip")
            findings.append(_envelope(
                "CHK-E-022", "present",
                f"Page {page.get('url')}: {'; '.join(reasons)}. Structural convention "
                "aligned with WCAG 2.2 SC 1.3.1 (Info and Relationships).",
                "medium", "NORMATIVE/PRACTITIONER",
                {"summary": "On this page: " + " and ".join(advice) + ".",
                 "priority": "medium"}, locus=locus,
                subcheck="+".join(subcheck_parts)))
        else:
            findings.append(_envelope("CHK-E-022", "absent", f"Page {page.get('url')}: "
                                       "landmark and heading structure intact.", None,
                                       "NORMATIVE/PRACTITIONER", None, locus=locus))
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
            {"summary": "Commercial and news sites gain credibility with visible contact "
                         "information, organisation name in the footer, HTTPS, and byline "
                         "dates on articles. Consider whether the missing signals above "
                         "should be surfaced. (Proactive — not a confirmed defect.)",
             "priority": "low"}, recommendation_only=True)
    return _envelope("CHK-E-024", "absent", "Commercial trust signals present.", None,
                      "CORRELATIONAL", None, recommendation_only=True)



def evaluate(bundle: dict) -> list[dict]:
    """Run all seventeen checks. D-004 needs D-003's result; D-010 needs D-004's -- same
    dependency order the two skills' procedures required before the merge. O-1 (CHK-E-019
    defers to CHK-D-003) is applied last, in-skill: see the module docstring for why this
    moved out of the orchestrator's compose_report.apply_suppression().
    """
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

    findings.extend(check_e014(bundle))
    findings.extend(check_e015(bundle))
    findings.extend(check_e016(bundle))
    findings.extend(check_e017(bundle))
    findings.extend(check_e018(bundle))
    e019 = check_e019(bundle)
    findings.append(e019)
    findings.extend(check_e020(bundle))
    findings.append(check_e021(bundle))
    findings.extend(check_e022(bundle))
    findings.append(check_e024(bundle))

    # Rule O-1: CHK-E-019 yields to CHK-D-003 when both are present for the homepage --
    # both independently measure the same raw-vs-rendered gap by design (the two checks
    # were authored blind to each other before the merge, and stay that way logically;
    # this suppression is the one place their outputs are reconciled).
    if d003.get("state") == "present" and e019.get("state") == "present":
        e019["state"] = "suppressed"
        e019["suppressed_by"] = list(set(e019.get("suppressed_by") or []) | {"CHK-D-003"})

    return findings
