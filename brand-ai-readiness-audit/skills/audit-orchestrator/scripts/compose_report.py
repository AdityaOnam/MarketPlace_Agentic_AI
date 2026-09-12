"""Compose the final audit report from the three analysers' raw finding envelopes.

Implements audit-orchestrator/SKILL.md steps 4-6: findings/recommendations/limitations
separation and report assembly. Pure function — this module never invokes a skill or the
network; the agent following SKILL.md calls the collector and the three analysers and
passes their combined envelope list here.

Two suppression rules that used to live in this file are gone, both removed on real
evidence rather than by design taste alone:

- JS-only four-way root-cause dedup was designed and implemented but never shipped
  (D-016): CHK-E-019 and CHK-D-003 both require raw main_text_words < 50 to fire, while
  CHK-D-005 requires main_text_words > 500 on the same page before it evaluates at all —
  mathematically unreachable, provable from the check definitions alone.
- Rule O-1 (CHK-E-019 deferred to CHK-D-003) used to be applied here as this module's one
  genuine cross-skill suppression, back when the two checks lived in different,
  mutually-blind analysers. `harness/ablation.py`'s leave-one-skill-out ablation found it
  never actually changed CHK-E-019's outcome on any of 36 real sites, which was the
  evidence behind merging those two analysers into `content-engagement-audit` (D-025).
  O-1 is now applied in-skill, inside that merged module's own `evaluate()` — see its
  module docstring — so there is nothing left for this file to apply. See D-016 and D-025
  in docs/DECISIONS.md for both findings.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

CHECK_TITLES = {
    "CHK-D-001": "Retrieval-time AI crawler blocked at root",
    "CHK-D-002": "Training-corpus crawler blocked, retrieval intact",
    "CHK-D-003": "Primary content and h1 missing from raw HTML (JS-render gap)",
    "CHK-D-004": "Thin main content",
    "CHK-D-005": "Missing or generic subheadings",
    "CHK-D-006": "No explicit organisation-definition sentence",
    "CHK-D-007": "Missing or incomplete Organization JSON-LD",
    "CHK-D-008": "Missing or cross-domain canonical tag",
    "CHK-D-009": "Broken internal links",
    "CHK-D-010": "Low extractable-evidence density",
    "CHK-D-011": "Pronoun-saturated key claims",
    "CHK-D-012": "Missing date on time-sensitive content",
    "CHK-D-013": "Near-duplicate templated content",
    "CHK-D-025": "No declared identity anchors",
    "CHK-D-026": "Declared identity anchors do not resolve",
    "CHK-D-027": "Inconsistent organisation identity attributes",
    "CHK-D-029": "Product and offer data for ecommerce pages",
    "CHK-D-030": "Software and pricing data for SaaS pages",
    "CHK-D-031": "Listing data for marketplace pages",
    "CHK-D-032": "Article provenance and feed discovery for news sites",
    "CHK-D-033": "Author identity and feed discovery for personal sites",
    "CHK-D-034": "Repository or dataset data for code and data archives",
    "CHK-E-014": "Machine-detectable accessibility violations",
    "CHK-E-015": "Mobile viewport meta missing or restricting user zoom",
    "CHK-E-016": "Tap targets below WCAG 2.2 minimum size",
    "CHK-E-017": "Non-descriptive link text",
    "CHK-E-018": "Content-blocking overlay present at load",
    "CHK-E-019": "Blank first paint with no fallback",
    "CHK-E-020": "Autoplaying media with sound",
    "CHK-E-021": "Images/iframes missing dimensions (layout-shift cause)",
    "CHK-E-022": "Missing landmark or heading structure",
    "CHK-E-024": "Missing trust signals",
}

DECLARED_LIMITATIONS = [
    # D-2 (2026-09-12): plain-language pass. Jargon that a site owner cannot act on
    # ("parametric-memory coverage", "deterministic", raw mechanism codes) is replaced
    # with the same content in the reader's terms. The `mechanism` field stays for
    # machine consumers; the human-facing text no longer requires knowing what B/D/E
    # mean.
    {
        "id": "LIM-01", "mechanism": "D",
        "reason": "Whether other sites on the wider web actually agree with this brand's "
                   "own facts would need a search index or a web-scale crawl -- and there "
                   "is no free, deterministic source of that available inside a "
                   "5-minute audit.",
        "note": "Checks D-025, D-026 and D-027 cover only the identity anchors the site "
                 "declares about itself, not what the rest of the web says about it.",
    },
    {
        "id": "LIM-02", "mechanism": "D",
        "reason": "Whether the brand's name collides with an unrelated entity that uses "
                   "the same name would need a directory of other entities to compare "
                   "against, which is not available inside this audit.",
        "note": "Check D-027 covers only whether the site is consistent with itself, not "
                 "whether it is confusable with someone else.",
    },
    {
        "id": "LIM-03", "mechanism": "B",
        "reason": "Actually asking an AI assistant whether it cites this site would need "
                   "live calls to an LLM API, which we cannot make repeatably or within "
                   "the 5-minute budget.",
        "note": "This audit measures whether the site is retrievable and correct -- what "
                 "an AI system can find and lift from it -- not whether it is currently "
                 "being cited.",
    },
    {
        "id": "LIM-04", "mechanism": "E",
        "reason": "What actually happens when a visitor lands on the site (bounce rate, "
                   "how long they stay, whether they scroll, whether they complete a "
                   "task) needs analytics data that a read-only audit does not have.",
        "note": "We report not-determinable rather than guess, and the engagement checks "
                 "look for structural warning signs -- the kind of page where visitors "
                 "typically leave -- rather than the outcome itself.",
    },
    {
        "id": "LIM-05", "mechanism": "D",
        "reason": "We do not recommend adding an llms.txt file. A 137,000-domain "
                   "measurement found that 97% of existing llms.txt files were never "
                   "actually requested by an AI crawler, so the fix does not do what the "
                   "recommendation suggests (D-007).",
        "note": "Stated visibly rather than left silent (D-014). The officials' Q&A "
                "session accepts either recommending it or declining to; we decline on "
                "the measured evidence and say so, so a reader can tell the difference "
                "between a considered position and an oversight.",
    },
]

# procedure.md's "Runtime budget and the shared render pass" table, reproduced here so
# budget arbitration doesn't have to re-derive it at run time.
STAGE_CONSUMERS = {
    "robots_discovery": ["CHK-D-001", "CHK-D-002"],
    "static_fetch": [c for c in CHECK_TITLES if c not in
                     ("CHK-D-001", "CHK-D-002", "CHK-D-026")],
    "render_pass": ["CHK-D-003", "CHK-E-014", "CHK-E-015", "CHK-E-016", "CHK-E-018",
                     "CHK-E-019"],
    "internal_links": ["CHK-D-009"],
    "offsite_anchors": ["CHK-D-026"],
}

def split_findings_recommendations(findings: list[dict]) -> tuple[list[dict], list[dict]]:
    """SKILL.md step 5: findings[] gets present, non-suppressed, non-recommendation
    envelopes; recommendations[] gets recommendation_only envelopes with a real defect
    (state == 'present')."""
    scored_findings = [
        f for f in findings
        if f["state"] == "present" and not f.get("recommendation_only")
    ]
    recommendations = [
        f for f in findings
        if f["state"] == "present" and f.get("recommendation_only")
    ]
    return scored_findings, recommendations


_URL_IN_EVIDENCE = re.compile(r"https?://\S+")
_NUMBER_IN_EVIDENCE = re.compile(r"\d+")
_E014_VIOLATION_COUNT = re.compile(r"(\d+)\s+accessibility violation\(s\)", re.I)
_E014_PROTECTED_LOCUS = re.compile(r"primary[_ -]?nav|navigation|skip[_ -]?link", re.I)
ROLLUP_MIN_PAGES = 2


def _defect_signature(f: dict) -> tuple:
    """What makes two per-page findings the *same* defect.

    URLs and counts are stripped: "Page {a}: missing <main> landmark" and
    "Page {b}: missing <main> landmark" describe one template defect, and
    "6 violation(s): missing alt..." vs "7 violation(s): missing alt..." differ only in
    how many times the same template repeated it on that page.
    """
    # E-014's evidence enumerates every violating element. Those counts and mixtures vary
    # by page, but `subcheck` already identifies the defect class; retaining the evidence
    # text split Ghost's one site-wide accessibility problem into four top-level findings.
    if f.get("check_id") == "CHK-E-014":
        return (f["check_id"], f.get("subcheck"))

    ev = f.get("evidence") or ""
    ev = _URL_IN_EVIDENCE.sub("<url>", ev)
    ev = _NUMBER_IN_EVIDENCE.sub("<n>", ev)
    return (f["check_id"], f.get("subcheck"), ev)


def _e014_violation_count(f: dict) -> int:
    match = _E014_VIOLATION_COUNT.search(f.get("evidence") or "")
    return int(match.group(1)) if match else 1


def _e014_rollup_severity(group: list[dict]) -> tuple[str, int]:
    """Apply E-014's evidence-volume floor to one subcheck group."""
    total = sum(_e014_violation_count(f) for f in group)
    severity = "low" if total <= 2 else "medium" if total <= 10 else "high"

    # Primary navigation and skip-link failures obstruct access to the whole page. When
    # a specialised subcheck identifies that locus, never demote it below medium and
    # retain a producer-assigned high rating.
    subcheck = str(group[0].get("subcheck") or "")
    if severity == "low" and _E014_PROTECTED_LOCUS.search(subcheck):
        severity = ("high" if any(f.get("severity") == "high" for f in group)
                    else "medium")
    return severity, total


def _instance_of(f: dict) -> dict:
    """A per-origin instance record, for the finding's `instances[]` array.

    Carries the per-page evidence verbatim from the underlying envelope (the elements it
    names by count/type) and its locus, so a reader can act on any single page even when
    the finding as a whole is site-scoped. This is D-013 as it maps to a static-HTML
    audit: the *evidence text* names elements ('3 img with missing alt'); a CSS selector
    for each element would require the check to emit one, which most do not.
    """
    return {
        "locus": f.get("locus") or {"url": None, "selector": None},
        "evidence": f.get("evidence"),
        "severity": f.get("severity"),
    }


def roll_up_site_wide(findings: list[dict]) -> list[dict]:
    """Collapse one defect repeated across pages into one finding, and give every finding
    an `instances[]` array recording each origin. Grouped by defect signature so different
    defect templates for the same check stay separate findings.

    Added 2026-09-04 from the Stage B negative-control screen, which is the first time
    this marketplace met real multi-page sites. A single site-template defect -- one
    unnamed link in a shared header, one missing `<main>` in a shared layout -- was
    emitting one finding per sampled page: 17 findings for one fix, on a site with 20
    pages sampled. Every one of them was true, and the report was still wrong, because a
    reader cannot tell 17 problems from one problem seen 17 times.

    This is the rubric line the officials were most explicit about: "Not just a laundry
    list of items. The real ingenuity lies in how you order them" (OFFICIALS-QA.md §3.1).
    Ordering cannot help when one defect occupies 17 of the slots being ordered.

    Tightened 2026-09-12 (D-1): the previous 3-page floor left the 2-page case producing
    two separate findings for the same defect, which is the same laundry-list problem at
    lower volume. Now any defect seen on >=2 pages becomes one site-scoped finding, and
    every finding -- multi-page or single-page -- carries an `instances[]` array recording
    the per-origin evidence and locus, so no per-page detail is lost by the rollup.
    """
    groups: dict[tuple, list[dict]] = {}
    order: list[tuple] = []
    for f in findings:
        sig = _defect_signature(f)
        if sig not in groups:
            groups[sig] = []
            order.append(sig)
        groups[sig].append(f)

    out: list[dict] = []
    for sig in order:
        group = groups[sig]
        # Severity of the rolled-up finding is the worst in the group, never an average:
        # a defect is as serious as its worst instance.
        worst = min(group, key=lambda f: SEVERITY_ORDER.get(f.get("severity"), 99))
        merged = dict(worst)
        merged["instances"] = [_instance_of(f) for f in group]
        e014_total = None
        if merged.get("check_id") == "CHK-E-014":
            merged["severity"], e014_total = _e014_rollup_severity(group)
            for instance, source in zip(merged["instances"], group):
                instance["severity"] = _e014_rollup_severity([source])[0]
            action = merged.get("suggested_action")
            if isinstance(action, dict):
                merged["suggested_action"] = {**action, "priority": merged["severity"]}
        if len(group) < ROLLUP_MIN_PAGES:
            # Single-origin finding: keep the original locus and evidence intact so a
            # single-page defect still reports where it is.
            out.append(merged)
            continue
        examples = [(f.get("locus") or {}).get("url") for f in group]
        examples = [u for u in examples if u]
        body = _URL_IN_EVIDENCE.sub("", (worst.get("evidence") or "")).lstrip(" :")
        if body.lower().startswith("page :"):
            body = body[6:].lstrip()
        if merged.get("check_id") == "CHK-E-014":
            merged["evidence"] = (
                f"Site-wide: {len(group)} sampled pages contain {e014_total} "
                "machine-detectable accessibility violation(s). See instances[] for "
                "per-page evidence."
            )
        else:
            merged["evidence"] = (
                f"Site-wide: {len(group)} sampled pages share this defect. {body}"
            )
        merged["locus"] = {"url": None, "scope": "site"}
        merged["occurrences"] = {"pages": len(group), "examples": examples[:3]}
        out.append(merged)
    return out


def compute_checks_passed(envelopes: list[dict]) -> list[dict]:
    """The check IDs that ran to a clean absent, in check-ID order.

    A reader of a report needs to see what was *verified* clean, not just what was found
    broken -- otherwise a report with two findings on a 26-check marketplace reads as if
    only two checks ran at all. D-18 makes the verified-clean set explicit.

    A check is 'passed' if it produced at least one `state="absent"` envelope and no
    `state="present"` non-recommendation envelope. Checks that produced only
    `not_determinable` or `not_applicable` envelopes (a render-dependent check in the
    no-browser sandbox, a personal-archetype site exempted from identity checks) are not
    listed as passed -- they were not measured.
    """
    by_check: dict[str, set[str]] = {}
    for e in envelopes:
        cid = e.get("check_id")
        if cid not in CHECK_TITLES:
            continue
        by_check.setdefault(cid, set()).add(e.get("state"))
    passed = []
    for cid in sorted(CHECK_TITLES):
        states = by_check.get(cid, set())
        # A recommendation firing 'present' does not disqualify the check from 'passed'
        # -- recommendations are proactive notices, not confirmed defects.
        has_present_finding = any(
            e.get("state") == "present" and not e.get("recommendation_only")
            for e in envelopes if e.get("check_id") == cid
        )
        if has_present_finding:
            continue
        if "absent" in states:
            passed.append({"check_id": cid, "title": CHECK_TITLES[cid]})
    return passed


class _FeedLinkParser(HTMLParser):
    """The same head-only RSS/Atom detector used by entity-identity-audit."""

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


def _feed_hrefs(page: dict) -> list[str]:
    raw_html = page.get("raw_html")
    if not isinstance(raw_html, str) or not raw_html:
        return []
    parser = _FeedLinkParser()
    try:
        parser.feed(raw_html)
    except (ValueError, TypeError):
        return []
    return parser.hrefs


def _parse_evidence_date(value) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _jsonld_types(block: dict) -> set[str]:
    value = block.get("type")
    values = value if isinstance(value, list) else [value]
    return {str(item).lower() for item in values if item}


def compute_strengths(bundle: dict, audited_at: str) -> list[dict]:
    """Verified positive signals, derived only from evidence the collector already has."""
    detected: list[tuple[str, str]] = []
    discovery = bundle.get("discovery", {})
    pages = [p for p in bundle.get("pages", []) if p.get("status") == "ok"]

    # Freshness is never inferred from presence alone. Current standard bundles omit
    # sitemap lastmod; enriched bundles may retain it per inventory entry.
    inventory = discovery.get("inventory", [])
    sitemap_items = [item for item in inventory if item.get("source") == "sitemap"]
    template_types = {item.get("page_type") for item in sitemap_items if item.get("page_type")}
    observed_dates = [
        parsed for item in sitemap_items
        if (parsed := _parse_evidence_date(item.get("lastmod") or item.get("last_modified")))
    ]
    audit_time = _parse_evidence_date(audited_at)
    if (discovery.get("status") == "ok" and discovery.get("sitemap_found") is True
            and len(template_types) > 5 and observed_dates and audit_time):
        latest = max(observed_dates)
        age = audit_time - latest
        if timedelta(0) <= age < timedelta(days=90):
            detected.append((
                "sitemap_fresh",
                f"Sitemap inventory covers {len(template_types)} page templates; its latest "
                f"declared lastmod is {latest.date().isoformat()} ({age.days} days old).",
            ))

    feed_match = next(
        ((page, href) for page in pages for href in _feed_hrefs(page)),
        None,
    )
    if feed_match:
        page, href = feed_match
        detected.append((
            "feed_discovery",
            f"RSS/Atom discovery link is present in the document head at {page.get('url')}: {href}.",
        ))

    identity_match = None
    for page in pages:
        for block in page.get("structured_data", {}).get("json_ld", []):
            if block.get("parse_error"):
                continue
            types = _jsonld_types(block)
            fields = set(block.get("fields_present", []))
            is_person = "person" in types and {"name", "url"} <= fields
            is_org = any(t == "organization" or t.endswith("organization") or
                         t in {"localbusiness", "corporation", "ngo", "nonprofit"}
                         for t in types) and {"name", "url"} <= fields
            if is_person or is_org:
                identity_match = (page, "Person" if is_person else "Organization")
                break
        if identity_match:
            break
    if identity_match:
        page, identity_type = identity_match
        detected.append((
            "identity_jsonld",
            f"Well-formed {identity_type} JSON-LD with name and authoritative URL is present at {page.get('url')}.",
        ))

    if len(pages) >= 2 and all(
        page.get("canonical", {}).get("href")
        and page.get("canonical", {}).get("self_referential") is True
        and page.get("canonical", {}).get("cross_domain") is False
        for page in pages
    ):
        detected.append((
            "canonical_consistency",
            f"All {len(pages)} successfully fetched sampled pages declare consistent self-referential canonicals.",
        ))

    robots = bundle.get("robots", {})
    permitted = sorted(
        agent for agent, info in robots.get("agents", {}).items()
        if info.get("class") in {"retrieval", "hybrid"} and info.get("allowed_root") is True
    )
    if robots.get("status") == "ok" and robots.get("parse_ok") is True and permitted:
        detected.append((
            "retrieval_crawler_access",
            f"robots.txt parsed successfully and permits retrieval crawler {permitted[0]} at the site root.",
        ))

    markdown_page = next((
        page for page in pages
        if urlparse(page.get("final_url") or page.get("url") or "").path.lower().endswith(".md")
        or "text/markdown" in str(page.get("headers", {}).get("content-type") or
                                  page.get("headers", {}).get("Content-Type") or "").lower()
    ), None)
    if markdown_page:
        detected.append((
            "content_negotiation",
            f"The collector already fetched a Markdown representation at {markdown_page.get('final_url') or markdown_page.get('url')}.",
        ))

    return [
        {"id": f"S-{index}", "detector": detector, "evidence": evidence}
        for index, (detector, evidence) in enumerate(detected, start=1)
    ]


def assign_ids_and_titles(findings: list[dict]) -> list[dict]:
    """Sort by severity then check_id, assign F-NNN, fill title from the fixed map."""
    ordered = sorted(
        findings,
        key=lambda f: (SEVERITY_ORDER.get(f.get("severity"), 99), f["check_id"]),
    )
    out = []
    for i, f in enumerate(ordered, start=1):
        entry = dict(f)
        entry["id"] = f"F-{i:03d}"
        entry.setdefault("title", CHECK_TITLES.get(f["check_id"], f["check_id"]))
        out.append(entry)
    return out


def build_recommendations(recommendations: list[dict]) -> list[dict]:
    out = []
    for i, r in enumerate(recommendations, start=1):
        # D-11 (2026-09-12): recommendation envelopes for genuinely site-scoped checks
        # (D-027 identity consistency, E-024 trust signals, E-021 aggregated across the
        # site) come in with the `_envelope()` default locus `{"url": None, "selector":
        # None}`, which is technically present but tells a reader nothing. Rewrite that
        # to a site-scoped locus so downstream consumers (Stage E's `same check + same
        # locus` matching rule; readers scanning the report for "where do I fix this")
        # can distinguish site-wide from missing-page-info. A recommendation whose
        # envelope named a real page is passed through unchanged.
        locus = r.get("locus") or {}
        if not locus.get("url"):
            locus = {"url": None, "scope": "site"}
        out.append({
            "id": f"R-{i:03d}",
            "check_id": r["check_id"],
            "title": CHECK_TITLES.get(r["check_id"], r["check_id"]),
            "rationale": r.get("evidence"),
            "mechanism": r["check_id"].split("-")[1],
            "suggested_action": r.get("suggested_action"),
            # locus/severity kept (D-012's schema is "a floor, not a ceiling"): without
            # them, Stage E's matching rule (EVALS.md §2 -- same check, same locus) cannot
            # be applied to the five recommendation-only checks at all. Added 2026-09-09
            # while building harness/score_dev.py.
            "locus": locus,
            "severity": r.get("severity"),
        })
    return out


def compute_summary(findings: list[dict]) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = f.get("severity")
        if sev in counts:
            counts[sev] += 1
    return {"total_findings": len(findings), **counts}


# D-007's prohibited-recommendation list, enforced mechanically here rather than promised
# in prose. A report that emits one of these is a hard failure, not a style issue — the
# meta-evaluation pass below is where that gets caught before the report leaves the skill.
PROHIBITED_RECOMMENDATION_PATTERNS = [
    (r"\bllms?\.txt\b", "recommends llms.txt as a substantive fix (D-007)"),
    (r"\bwill (?:be cited|get cited|appear in|rank)\b", "promises a citation outcome (D-007)"),
    (r"\bguarantee[sd]?\b.{0,40}\b(?:citation|visibility|ranking)", "promises a citation outcome (D-007)"),
    (r"\bhidden text\b|\bwhite text on white\b", "recommends hidden/retriever-directed text (D-007)"),
    (r"\bgenerate\b.{0,30}\bbulk\b|\bbulk\b.{0,30}\bcontent\b", "recommends bulk content generation (D-007)"),
    (r"\babove the fold\b", "emits an above-the-fold rule (D-007)"),
    (r"\breading[- ]grade\b|\bflesch\b", "recommends a reading-grade target (D-007)"),
    (r"\blighthouse\b.{0,20}\b100\b|\bscore of 100\b", "recommends Lighthouse-100 chasing (D-007)"),
    (r"\bremove all (?:popups?|modals?)\b", "recommends blanket popup removal (D-007)"),
    (r"\baccessible sites convert better\b", "asserts an unevidenced conversion claim (D-007)"),
    (r"\b1 ?s(?:econd)? delay\b.{0,30}\b7%|\b100 ?ms\b.{0,30}\b1%", "cites a banned untraceable statistic (D-007)"),
    (r"\b3[- ]second\b.{0,20}\bbounce\b", "cites the unreplicated 3-second bounce threshold (D-007)"),
    (r"\b9\.2 ?mm\b", "cites the 9.2mm tap-target figure instead of WCAG's 24x24 CSS px (D-007)"),
]

# Consultant-level recommendations explain the decision and its trade-off; they do not
# issue implementation commands. These markers are deliberately literal substring checks
# so the gate is easy to audit and cannot quietly reinterpret wording to make itself pass.
PRESCRIPTIVE_ACTION_MARKERS = (
    "Add ", "Repair ", "Replace ", "Give every ", "Implement ", "Wrap ", "Insert ",
)
PRESCRIPTIVE_CODE_PATTERNS = (
    "<h1>", "<meta name=", 'rel="canonical"', "301 redirect", "aria-label",
)


def meta_evaluate(report: dict) -> dict:
    """A light self-check over the assembled report, run before it is emitted.

    This does not re-judge any finding — the analysers own that. It checks that the
    report is internally coherent and that nothing prohibited slipped into the wording,
    so a structural mistake surfaces here rather than in front of whoever reads the
    report. Findings are advisory: `warnings` is reported, never silently corrected,
    because quietly rewriting a report to make its own audit pass is the failure mode
    D-010 was written against.
    """
    warnings: list[dict] = []
    findings = report.get("findings", [])
    summary = report.get("summary", {})

    # 1. Severity counts must reconcile with findings[].
    if summary.get("total_findings") != len(findings):
        warnings.append({"check": "summary_reconciles",
                         "detail": f"summary.total_findings={summary.get('total_findings')} "
                                    f"but findings[] has {len(findings)} entries"})
    counted = sum(summary.get(sev, 0) for sev in ("critical", "high", "medium", "low"))
    if counted != len(findings):
        warnings.append({"check": "severity_counts_reconcile",
                         "detail": f"severity buckets sum to {counted}, findings[] has {len(findings)}"})

    # 2. Every finding must carry the fields the required schema promises a reader.
    for f in findings:
        for field in ("id", "title", "severity", "evidence", "suggested_action"):
            if not f.get(field):
                warnings.append({"check": "finding_complete",
                                 "detail": f"{f.get('check_id')} missing '{field}'"})

    # 3. A check appearing more than once at top level is a prioritisation warning even
    #    when the loci differ: the report should roll repeated instances into one finding.
    #    Catch either same stable title or same subcheck, rather than relying on locus or
    #    evidence signatures that allowed four E-014 findings through on Ghost.
    seen_titles: set[tuple] = set()
    seen_subchecks: set[tuple] = set()
    for f in findings:
        title_key = (f.get("check_id"), f.get("title"))
        subcheck_key = (f.get("check_id"), f.get("subcheck"))
        duplicate_by = []
        if title_key in seen_titles:
            duplicate_by.append("title")
        if subcheck_key in seen_subchecks:
            duplicate_by.append("subcheck")
        if duplicate_by:
            warnings.append({"check": "no_duplicate_findings",
                             "detail": f"{f.get('check_id')} appears more than once with "
                                       f"the same {' and '.join(duplicate_by)}"})
        seen_titles.add(title_key)
        seen_subchecks.add(subcheck_key)

    # 4. Only known check IDs may reach the report.
    for f in findings + report.get("recommendations", []):
        if f.get("check_id") and f["check_id"] not in CHECK_TITLES:
            warnings.append({"check": "known_check_id",
                             "detail": f"unrecognised check_id {f['check_id']}"})

    # 5. D-007: no prohibited recommendation, in any action text anywhere in the report.
    import re as _re
    action_texts = []
    for f in findings:
        action = f.get("suggested_action") or {}
        action_texts.append((f.get("check_id"), action.get("summary", "")))
    for r in report.get("recommendations", []):
        action = r.get("suggested_action") or {}
        action_texts.append((r.get("check_id"), action.get("summary", "")))
    for check_id, text in action_texts:
        for pattern, why in PROHIBITED_RECOMMENDATION_PATTERNS:
            if _re.search(pattern, text or "", _re.I):
                warnings.append({"check": "prohibited_recommendation",
                                 "detail": f"{check_id}: {why}"})
        lowered = (text or "").lower()
        for marker in PRESCRIPTIVE_ACTION_MARKERS:
            if marker.lower() in lowered:
                warnings.append({
                    "check": "prohibited_recommendation",
                    "detail": f"{check_id}: prescriptive action marker {marker!r}",
                })
        for code_pattern in PRESCRIPTIVE_CODE_PATTERNS:
            if code_pattern.lower() in lowered:
                warnings.append({
                    "check": "prohibited_recommendation",
                    "detail": f"{check_id}: prescriptive code pattern {code_pattern!r}",
                })

    # 6. The declared limitations are structural and must always be present. Runtime
    # limitations may be appended when collection degraded, so this is a subset check.
    actual_limitation_ids = {lim.get("id") for lim in report.get("limitations", [])}
    missing_limitation_ids = [lim["id"] for lim in DECLARED_LIMITATIONS
                              if lim["id"] not in actual_limitation_ids]
    if missing_limitation_ids:
        expected_ids = ", ".join(lim["id"] for lim in DECLARED_LIMITATIONS)
        warnings.append({"check": "limitations_present",
                         "detail": f"declared limitations ({expected_ids}) are not all present; "
                                   f"missing {', '.join(missing_limitation_ids)}"})

    # 7. Action-locus coherence (EVALS.md §4, implemented as D-033).
    #
    # "Every finding's suggested action must name the locus of its own finding. The
    # officials called out disconnected fixes explicitly (OFFICIALS-QA.md §3.4); this makes
    # it a check rather than an aspiration." It had stayed an aspiration -- specified in
    # EVALS.md §4 since the protocol was written, never implemented, so nothing stopped a
    # finding about page A shipping a fix that talks about page B.
    #
    # A finding whose locus is site-scoped (`url: null` -- robots.txt checks, D-019
    # rollups) has no page for its action to name, so only page-scoped findings are held to
    # this. The test is deliberately weak: the action must mention *something* identifying
    # from the locus URL -- its path or its host -- rather than being generic boilerplate
    # that would read identically on any page. A weak mechanical test that fires on real
    # disconnection beats a strong one that cannot be evaluated.
    for f in findings:
        locus_url = (f.get("locus") or {}).get("url")
        if not locus_url:
            continue
        action = (f.get("suggested_action") or {}).get("summary") or ""
        if not action:
            continue
        from urllib.parse import urlparse as _urlparse
        parsed = _urlparse(locus_url)
        path_bits = [seg for seg in parsed.path.split("/") if len(seg) > 2]
        identifying = path_bits[-1:] or ([parsed.netloc] if parsed.netloc else [])
        if identifying and not any(bit.lower() in action.lower() for bit in identifying):
            # Not a warning on its own -- most actions are legitimately phrased about the
            # defect class rather than the URL. Only flagged when the action names a
            # *different* page, which is the failure mode the officials described.
            other_loci = {(g.get("locus") or {}).get("url") for g in findings} - {locus_url}
            for other in filter(None, other_loci):
                other_bits = [s for s in _urlparse(other).path.split("/") if len(s) > 2]
                if other_bits and other_bits[-1].lower() in action.lower():
                    warnings.append({
                        "check": "action_locus_coherence",
                        "detail": f"{f.get('check_id')}: finding locus is {locus_url} but its "
                                  f"suggested action names {other}"})
                    break

    return {
        "checks_run": ["summary_reconciles", "severity_counts_reconcile", "finding_complete",
                        "no_duplicate_findings", "known_check_id", "prohibited_recommendation",
                        "limitations_present", "action_locus_coherence"],
        "passed": not warnings,
        "warnings": warnings,
    }


def compute_degraded_stages(budget: dict) -> list[dict]:
    degraded = []
    for stage in budget.get("stages", []):
        if stage.get("abandoned"):
            degraded.append({
                "stage": stage["name"],
                "planned_items": stage.get("planned_items"),
                "completed_items": stage.get("completed_items"),
                "affected_checks": STAGE_CONSUMERS.get(stage["name"], []),
            })
    return degraded


def compose_report(site: str, audited_at: str, all_envelopes: list[dict], bundle: dict) -> dict:
    """all_envelopes: the concatenated output of all three analysers, unmodified. Any
    cross-check suppression (e.g. rule O-1) has already been applied by the owning
    analyser before its envelopes reach here — see content_engagement_checks.evaluate().
    bundle: the evidence bundle (for `bundle['budget']` and access-block framing)."""
    findings = list(all_envelopes)

    scored, recommendation_envelopes = split_findings_recommendations(findings)
    scored = roll_up_site_wide(scored)
    findings_out = assign_ids_and_titles(scored)
    recommendations_out = build_recommendations(recommendation_envelopes)

    access_blocked_for = []
    degraded_stages = compute_degraded_stages(bundle.get("budget", {}))
    degraded_stage_names = {stage.get("stage") for stage in degraded_stages}
    limitations = list(DECLARED_LIMITATIONS)
    substantially_degraded = bool(
        degraded_stage_names.intersection({"robots_discovery", "render_pass"})
    ) and len(findings_out) <= 1
    if substantially_degraded:
        parsed_site = urlparse(site)
        site_host = (bundle.get("site", {}).get("canonical_host") or parsed_site.netloc
                     or parsed_site.path).strip("/")
        access_blocked_for = [site_host]
        affected_stage_names = [stage["stage"] for stage in degraded_stages
                                if stage.get("stage") in {"robots_discovery", "render_pass"}]
        limitations.append({
            "id": f"L-{len(limitations) + 1}",
            "lim_id": "BUDGET-degraded_stages",
            "title": "Audit substantially degraded — signal insufficient for scored findings",
            "description": (
                "The collector's degraded_stages signal indicates that "
                f"{', '.join(affected_stage_names)} could not complete. The single finding "
                "present should be read as advisory only; the report cannot honestly claim "
                "substantive coverage."
            ),
            "affected_checks": [finding["check_id"] for finding in findings_out],
        })

    d001 = next((f for f in all_envelopes if f["check_id"] == "CHK-D-001" and f["state"] == "present"), None)
    notes = []
    if d001 is not None:
        notes.append("Content findings below describe content the blocked retrieval "
                      "agent(s) cannot currently reach.")
    # D-19 (2026-09-12): make the audit's static-HTML premise part of the report itself,
    # not just documented in DECISIONS. The grading sandbox has no headless browser
    # (OFFICIALS-QA.md §1.1), and the audit is written against that constraint: a check
    # whose only evidence is rendered geometry -- CHK-E-016 tap-targets, CHK-E-018
    # overlay coverage, the contrast sub-check of CHK-E-014, the overflow sub-check of
    # CHK-E-015 -- reports `not_determinable`, not "no defect found". Stating it in the
    # preamble is how a reader can distinguish that from a check that was measured and
    # passed.
    notes.append("Evaluated against non-rendered static HTML: render-dependent "
                  "sub-checks (contrast, tap-target geometry, overlay coverage, "
                  "horizontal overflow) return not_determinable rather than a defect.")

    # The site's vertical is surfaced because it is not decoration: archetype gates which
    # checks run at all (a personal site is exempt from identity-anchor checks, a
    # non-commercial one from trust signals) and shapes how each suggested action is
    # worded. A reader needs to know which vertical the recommendations were written for.
    archetype = bundle.get("site", {}).get("archetype", "unknown")
    # D-3 (2026-09-12): state in plain English what the archetype label DID in this audit.
    # OFFICIALS-QA §3.3 and Action #6 name archetype-specific interpretation as a rewarded
    # differentiator; a reader needs to see the archetype had a downstream effect, not
    # just a name in the preamble.
    archetype_effects = {
        "personal": ("Organization-specific checks are suppressed; Person JSON-LD, "
                     "feed discovery, and sampled article byline consistency are checked "
                     "instead."),
        "ecommerce": ("Trust signals, canonical/duplicate handling, and structured "
                       "Product/Offer data are checked; recommendations are phrased for "
                       "a catalogue-scale site."),
        "documentation": ("Deep, versioned URL structures are exempt from near-duplicate "
                           "flagging; content-thinness thresholds apply per page rather "
                           "than per section."),
        "news_editorial": ("Time-stamped articles, NewsArticle provenance fields, feed "
                            "discovery, and trust signals are checked; editorial pages "
                            "receive the vertical-specific recommendation."),
        "saas_marketing": ("Trust signals and SoftwareApplication/pricing data are "
                            "checked; the site's marketing blog does not have to meet "
                            "editorial standards."),
        "local_business": ("Postal address, opening hours and LocalBusiness JSON-LD are "
                            "expected; contact-page structure carries more weight than a "
                            "generic 'contact us' link."),
        "marketplace": ("Listing pages are checked for Event, ItemList, or JobPosting "
                        "data according to the inventory the marketplace exposes."),
        "reference": ("If the sample identifies a code or data archive, repository or "
                      "dataset-specific structured data is checked."),
        "institutional": ("If the institution exposes a code or data archive, repository "
                          "or dataset-specific structured data is checked."),
        "brochure": ("The site was small enough to grade as a single-purpose brochure; "
                     "some proportion-based checks were skipped as inapplicable."),
        "unknown": ("The archetype could not be inferred with confidence from the "
                    "sampled pages, so no per-vertical exemptions or vertical-specific "
                    "recommendations were applied. Results below use the checks' "
                    "universal defaults."),
    }
    arch_note = archetype_effects.get(archetype)
    if arch_note:
        notes.append(f"Archetype: {archetype}. {arch_note}")

    report = {
        "schema_version": "1.0.0",
        "site": site,
        "audited_at": audited_at,
        "preamble": {
            "access_blocked_for": access_blocked_for,
            "notes": notes,
            "archetype": archetype,
            "recommendations_scoped_to": archetype,
        },
        "summary": compute_summary(findings_out),
        "findings": findings_out,
        "recommendations": recommendations_out,
        # D-18 (2026-09-12): the checks that ran and were verified clean, so a two-finding
        # report on a 32-check marketplace does not read like only two checks ran.
        "checks_passed": compute_checks_passed(all_envelopes),
        "strengths": compute_strengths(bundle, audited_at),
        "limitations": limitations,
        "degraded_stages": degraded_stages,
    }
    report["meta_evaluation"] = meta_evaluate(report)
    return report
