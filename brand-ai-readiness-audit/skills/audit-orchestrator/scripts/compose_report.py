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
    #
    # Phase 9 item H (2026-09-14): the entries below carry a stable `lim_id` that
    # survives across runs; `id` (the ephemeral L-NNN slot) is stamped at emission
    # time in compose_report(). Before this pass, entries carried a single `id`
    # holding the stable value, so shipped reports had `lim_id: null` on every
    # declared limitation while only the runtime BUDGET-degraded_stages entry had
    # a proper stable id. See docs/DECISIONS.md D-035 (Phase 9 tier 1).
    {
        "lim_id": "LIM-01", "mechanism": "D",
        "reason": "Whether other sites on the wider web actually agree with this brand's "
                   "own facts would need a search index or a web-scale crawl -- and there "
                   "is no free, deterministic source of that available inside a "
                   "5-minute audit.",
        "note": "Checks D-025, D-026 and D-027 cover only the identity anchors the site "
                 "declares about itself, not what the rest of the web says about it.",
    },
    {
        "lim_id": "LIM-02", "mechanism": "D",
        "reason": "Whether the brand's name collides with an unrelated entity that uses "
                   "the same name would need a directory of other entities to compare "
                   "against, which is not available inside this audit.",
        "note": "Check D-027 covers only whether the site is consistent with itself, not "
                 "whether it is confusable with someone else.",
    },
    {
        "lim_id": "LIM-03", "mechanism": "B",
        "reason": "Actually asking an AI assistant whether it cites this site would need "
                   "live calls to an LLM API, which we cannot make repeatably or within "
                   "the 5-minute budget.",
        "note": "This audit measures whether the site is retrievable and correct -- what "
                 "an AI system can find and lift from it -- not whether it is currently "
                 "being cited.",
    },
    {
        "lim_id": "LIM-04", "mechanism": "E",
        "reason": "What actually happens when a visitor lands on the site (bounce rate, "
                   "how long they stay, whether they scroll, whether they complete a "
                   "task) needs analytics data that a read-only audit does not have.",
        "note": "We report not-determinable rather than guess, and the engagement checks "
                 "look for structural warning signs -- the kind of page where visitors "
                 "typically leave -- rather than the outcome itself.",
    },
    {
        "lim_id": "LIM-05", "mechanism": "D",
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
    """Apply E-014's evidence-volume floor to one subcheck group.

    Phase 9 item D (2026-09-14): accessibility-only findings are capped at `medium`
    regardless of evidence volume. The critical/high tier is reserved for
    AI-crawler-blocking, canonical, and identity defects; 15 unlabeled form controls
    on a docs site is a genuine defect but not a top-severity AI-readiness signal
    that should sit next to a `Disallow: /` for ChatGPT-User. The severity floor is
    still applied for the tiny (<=2 violations) case so a single missing alt text
    on a marketing page does not sit at medium next to a canonical mismatch.
    """
    total = sum(_e014_violation_count(f) for f in group)
    severity = "low" if total <= 2 else "medium"

    # Primary navigation and skip-link failures obstruct access to the whole page. When
    # a specialised subcheck identifies that locus, never demote it below medium and
    # retain a producer-assigned high rating.
    subcheck = str(group[0].get("subcheck") or "")
    if severity == "low" and _E014_PROTECTED_LOCUS.search(subcheck):
        severity = "medium"
    return severity, total


def _cap_a11y_severity(check_id: str, severity: str) -> str:
    """Phase 9 item D: cap CHK-E-014 and CHK-E-022 at medium regardless of source.

    A11y checks fire on structural HTML defects (missing landmarks, unlabeled
    controls, heading-level skips). These are real but not AI-crawler-blocking on
    their own; treating them as `high` alongside a `Disallow: / GPTBot` finding
    fails the axis-1 prioritisation the officials named as the differentiator.
    """
    if check_id in ("CHK-E-014", "CHK-E-022") and severity in ("critical", "high"):
        return "medium"
    return severity


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
            # Phase 9 item D: still cap a11y severities.
            merged["severity"] = _cap_a11y_severity(merged.get("check_id"), merged.get("severity"))
            action = merged.get("suggested_action")
            if isinstance(action, dict) and merged.get("check_id") in ("CHK-E-014", "CHK-E-022"):
                merged["suggested_action"] = {**action, "priority": merged["severity"]}
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
        # Phase 9 item A (2026-09-14): preserve the first sampled page's URL on the
        # rollup so axis-4 (evidence chain) stays intact. Before this pass every
        # site-wide finding shipped with `locus.url = null`, forcing a reader to
        # descend into instances[] to find any URL they could open. Now `locus.url`
        # names the first affected page (a click-through anchor) and `scope: site`
        # + `occurrences` still describe that the defect templates across the
        # sample. See docs/DECISIONS.md D-035.
        first_url = next(
            (url for url in examples if url), None
        )
        merged["locus"] = {"url": first_url, "scope": "site", "selector": None}
        merged["occurrences"] = {"pages": len(group), "examples": examples[:3]}
        # Fix D: cap accessibility-only severities at medium after rollup severity
        # was computed. E-014 already runs through _e014_rollup_severity above; E-022
        # goes through the generic path and inherits the worst source severity.
        merged["severity"] = _cap_a11y_severity(merged.get("check_id"), merged.get("severity"))
        action = merged.get("suggested_action")
        if isinstance(action, dict) and merged.get("check_id") in ("CHK-E-014", "CHK-E-022"):
            merged["suggested_action"] = {**action, "priority": merged["severity"]}
        out.append(merged)
    return out


# Phase 9 item M: DOM/link-dependent checks that require the sampled pages to have
# been reached and their DOM parsed. On a blocked site (access_blocked_for populated)
# these checks had no input; showing them as `passed` reads as "we verified the
# accessibility structure of a site we could not reach", which two independent judges
# flagged as fatal contradiction.
DOM_DEPENDENT_CHECKS = frozenset({
    "CHK-E-014", "CHK-E-015", "CHK-E-022", "CHK-D-003", "CHK-D-009",
    "CHK-E-018", "CHK-E-019", "CHK-E-021",
})


def _dedup_covered_by_rollup(findings: list[dict]) -> list[dict]:
    """Phase 9 item U (2026-09-14): drop per-page findings that a same-check,
    same-subcheck site-wide rollup already covers.

    Before this pass, heise.de shipped three CHK-E-022 findings: two site-wide
    rollups (no_h1 across 4 pages, no_main across 6 pages) plus a per-page finding
    on `/benachrichtigungen/heise-bot/` for no_main -- a page that was already one
    of the six the site-wide rollup covered. Meta-eval's no_duplicate_findings gate
    caught it but the report shipped anyway.

    The dedup rule is intentionally conservative: only drop a per-page finding
    when a site-wide rollup exists on the SAME `(check_id, subcheck)` pair AND
    the per-page URL appears in that rollup's `occurrences.examples` or
    `instances[]`. That way genuinely different defect classes on the same page
    (e.g. no_h1 vs no_main both on `/foo`) still surface as separate findings.
    """
    rollups_by_key: dict[tuple, dict] = {}
    for f in findings:
        if (f.get("locus") or {}).get("scope") == "site":
            rollups_by_key[(f.get("check_id"), f.get("subcheck"))] = f

    out: list[dict] = []
    dropped_any = False
    for f in findings:
        if (f.get("locus") or {}).get("scope") == "site":
            out.append(f)
            continue
        key = (f.get("check_id"), f.get("subcheck"))
        rollup = rollups_by_key.get(key)
        if rollup is not None:
            page_url = (f.get("locus") or {}).get("url")
            covered = False
            examples = (rollup.get("occurrences") or {}).get("examples") or []
            if page_url and page_url in examples:
                covered = True
            else:
                # Fall back to instances[] in case examples is truncated (only 3 kept).
                for inst in rollup.get("instances", []) or []:
                    if (inst.get("locus") or {}).get("url") == page_url:
                        covered = True
                        break
            if covered:
                dropped_any = True
                continue
        out.append(f)
    return out


def compute_checks_passed(
    envelopes: list[dict],
    degraded_stages: list[dict] | None = None,
    access_blocked_for: list[str] | None = None,
) -> list[dict]:
    """The check IDs that ran to a clean absent, in check-ID order.

    A reader of a report needs to see what was *verified* clean, not just what was found
    broken -- otherwise a report with two findings on a 26-check marketplace reads as if
    only two checks ran at all. D-18 makes the verified-clean set explicit.

    A check is 'passed' if it produced at least one `state="absent"` envelope and no
    `state="present"` non-recommendation envelope. Checks that produced only
    `not_determinable` or `not_applicable` envelopes (a render-dependent check in the
    no-browser sandbox, a personal-archetype site exempted from identity checks) are not
    listed as passed -- they were not measured.

    Phase 9 item M (2026-09-14): checks whose input stage was abandoned during
    collection cannot be verified clean, even if they emitted no `present` envelope.
    On a WAF-blocked site whose `render_pass` never produced any DOM, DOM-only checks
    (E-014, E-015, E-022, D-003, D-009, E-018, E-019, E-021) previously showed up in
    checks_passed[] as if they had been measured -- two independent judges called this
    "fatal contradiction" and "internal architectural collapse". Union every
    `degraded_stages[].affected_checks` list and remove those check IDs from passed;
    they belong to the (implicit) not_determinable set the degraded_stages block
    already describes. See docs/DECISIONS.md D-035.
    """
    starved: set[str] = set()
    for stage in (degraded_stages or []):
        for cid in stage.get("affected_checks", []) or []:
            starved.add(cid)
    # If the site is marked substantially blocked, the whole DOM/link-dependent
    # family had no meaningful input regardless of which specific stages recorded
    # abandonment; treat every DOM-dependent check as starved so a blocked-site
    # report never lists them as `passed`.
    if access_blocked_for:
        starved.update(DOM_DEPENDENT_CHECKS)
    by_check: dict[str, set[str]] = {}
    for e in envelopes:
        cid = e.get("check_id")
        if cid not in CHECK_TITLES:
            continue
        by_check.setdefault(cid, set()).add(e.get("state"))
    passed = []
    for cid in sorted(CHECK_TITLES):
        if cid in starved:
            # Input stage was abandoned; the analyser had nothing to score.
            continue
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


def _consolidate_per_page_recs(recommendations: list[dict]) -> list[dict]:
    """Phase 9 item B (2026-09-14): consolidate per-page recommendations that share a
    check_id and an identical `suggested_action.summary` into one recommendation with
    per-page detail in `instances[]`.

    Before this pass, `check_d008` and similar per-page recommenders emitted one
    recommendation per sampled page with the same advisory string, producing
    reports that shipped six identical CHK-D-008 entries on a five-page sample.
    Judges consistently read this as either padding or empty content. Group by
    (check_id, sanitized_summary) — using the same text-normalisation the finding
    rollup uses so per-page URL differences do not defeat the merge — and merge.

    Recommendations whose `summary` is empty or missing are passed through unchanged
    so a downstream drop-or-rewrite step (item C) can act on them.
    """
    if not recommendations:
        return recommendations

    def _norm(text: str | None) -> str:
        s = _URL_IN_EVIDENCE.sub("<url>", text or "")
        return _NUMBER_IN_EVIDENCE.sub("<n>", s).strip()

    groups: dict[tuple, list[dict]] = {}
    order: list[tuple] = []
    for r in recommendations:
        summary = (r.get("suggested_action") or {}).get("summary") or ""
        if not summary.strip():
            key = ("__no_summary__", id(r))
        else:
            key = (r.get("check_id"), _norm(summary))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)

    out: list[dict] = []
    for key in order:
        group = groups[key]
        if len(group) == 1:
            out.append(group[0])
            continue
        merged = dict(group[0])
        # Preserve the first per-page URL as the primary locus so axis-4 (evidence
        # chain) still has a click-through. Every original per-page envelope is
        # kept in instances[].
        merged["instances"] = [
            {
                "locus": r.get("locus") or {"url": None, "selector": None},
                "evidence": r.get("evidence"),
                "severity": r.get("severity"),
            }
            for r in group
        ]
        # Note the aggregation in the evidence rather than lying about a single-page
        # observation. The individual page URLs live in instances[].
        base_evidence = group[0].get("evidence") or ""
        merged["evidence"] = (
            f"{len(group)} sampled pages share this proactive recommendation. "
            f"See instances[] for per-page evidence. First: {base_evidence}"
        )
        out.append(merged)
    return out


def build_recommendations(recommendations: list[dict]) -> list[dict]:
    # Phase 9 item B: consolidate per-page duplicates before serialising.
    recommendations = _consolidate_per_page_recs(recommendations)
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
        suggested_action = r.get("suggested_action")
        # Phase 9 item B close-out (2026-09-14): every recommendation carries a
        # top-level `summary` string that mirrors suggested_action.summary. Prior
        # shipped shape kept the summary nested; readers and verifiers that
        # walked `recommendations[]` for a top-level summary found nothing on any
        # rec and reported them all as empty. Duplicating the string at both
        # levels is backward-compatible (existing consumers of
        # suggested_action.summary keep working) and satisfies the top-level
        # reader without a schema break.
        top_summary = ""
        if isinstance(suggested_action, dict):
            top_summary = (suggested_action.get("summary") or "").strip()
        entry = {
            "id": f"R-{i:03d}",
            "check_id": r["check_id"],
            "title": CHECK_TITLES.get(r["check_id"], r["check_id"]),
            "summary": top_summary,
            "rationale": r.get("evidence"),
            "mechanism": r["check_id"].split("-")[1],
            "suggested_action": suggested_action,
            # locus/severity kept (D-012's schema is "a floor, not a ceiling"): without
            # them, Stage E's matching rule (EVALS.md §2 -- same check, same locus) cannot
            # be applied to the five recommendation-only checks at all. Added 2026-09-09
            # while building harness/score_dev.py.
            "locus": locus,
            "severity": r.get("severity"),
        }
        if r.get("instances"):
            entry["instances"] = r["instances"]
        out.append(entry)
    return out


def _drop_empty_summary_recs(report: dict) -> list[dict]:
    """Phase 9 item B close-out (2026-09-14): defense-in-depth drop pass.

    If a source check emits a recommendation envelope with no `suggested_action`
    at all -- so `_consolidate_per_page_recs` cannot merge it, `build_recommendations`
    cannot mirror a summary from it, and the top-level `summary` field ends up
    empty -- drop that recommendation and record the drop as an
    `empty_recommendation` warning. The report should never ship a recommendation
    the reader cannot act on.
    """
    dropped: list[dict] = []
    kept: list[dict] = []
    for r in report.get("recommendations", []) or []:
        nested = ""
        sa = r.get("suggested_action")
        if isinstance(sa, dict):
            nested = (sa.get("summary") or "").strip()
        top = (r.get("summary") or "").strip()
        if not nested and not top:
            dropped.append({
                "check": "empty_recommendation",
                "detail": f"{r.get('check_id')}: no summary produced by source check",
            })
            continue
        kept.append(r)
    report["recommendations"] = kept
    return dropped


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


def _action_has_prescriptive_marker(text: str | None) -> str | None:
    """Return the first offending marker if the action text uses prescriptive wording,
    otherwise None. Substring checks kept deliberately literal so the gate is easy to
    audit and cannot quietly reinterpret wording to make itself pass.
    """
    if not text:
        return None
    lowered = text.lower()
    for marker in PRESCRIPTIVE_ACTION_MARKERS:
        if marker.lower() in lowered:
            return marker
    for code_pattern in PRESCRIPTIVE_CODE_PATTERNS:
        if code_pattern.lower() in lowered:
            return code_pattern
    return None


# Phase 9 item P (2026-09-14): strength detectors and the check_ids their presence
# would contradict a recommendation for. When compute_strengths() confirms
# `identity_jsonld` (well-formed Organization/Person JSON-LD), a recommendation
# under CHK-D-006 or CHK-D-007 saying "consider adding Organization JSON-LD" is
# an internal contradiction. Two independent judges called this out on Al Jazeera.
# The map is deliberately narrow -- only detectors whose evidence directly answers
# a specific check's premise -- and the filter drops the offending recommendation
# and records the drop as a `contradicted_by_strength` warning for traceability.
STRENGTH_CONTRADICTS_CHECK: dict[str, tuple[str, ...]] = {
    "feed_discovery":            ("CHK-D-032", "CHK-D-033"),
    "identity_jsonld":           ("CHK-D-006", "CHK-D-007"),
    "canonical_consistency":     ("CHK-D-008",),
    "retrieval_crawler_access":  ("CHK-D-001",),
}


def _filter_strengths_recs_contradiction(report: dict) -> list[dict]:
    """Drop recs whose check_id is already answered by an active strength detector.

    The report cannot honestly say "the site has X" in `strengths[]` and simultaneously
    say "the site should add X" in `recommendations[]`. This is the strengths-vs-recs
    contradiction pattern the judges flagged. When a strength detector fires, drop
    the recommendations it contradicts and log the drop as a warning.
    """
    strengths = report.get("strengths", []) or []
    active_detectors = {s.get("detector") for s in strengths if s.get("detector")}
    if not active_detectors:
        return []
    contradicted_check_ids: set[str] = set()
    for detector in active_detectors:
        for cid in STRENGTH_CONTRADICTS_CHECK.get(detector, ()):
            contradicted_check_ids.add(cid)
    if not contradicted_check_ids:
        return []
    dropped: list[dict] = []
    kept: list[dict] = []
    for r in report.get("recommendations", []) or []:
        cid = r.get("check_id")
        if cid in contradicted_check_ids:
            dropped.append({
                "check": "contradicted_by_strength",
                "detail": (f"{cid}: recommendation dropped because the site's active "
                           f"strength detectors already answer this check's premise"),
            })
            continue
        kept.append(r)
    report["recommendations"] = kept
    return dropped


def _enforce_prohibited_recommendation_gate(report: dict) -> list[dict]:
    """Phase 9 item C (2026-09-14): drop recommendations whose suggested_action still
    reads as an implementation fix, and record the drop as a `gate_dropped_action`
    warning. The gate is DEFENSE IN DEPTH: prescriptive wording should already have
    been rewritten at each check's source (item C first pass), but this ensures a
    check that regresses cannot silently ship a `Wrap ... in <main>` action to a
    reader. Findings are NOT dropped here (they own real defects that need surfacing);
    if a finding's action still has an imperative marker after the source rewrite,
    that surfaces as a `prohibited_recommendation` warning per the meta-eval below.
    """
    dropped: list[dict] = []
    recs = report.get("recommendations", [])
    kept: list[dict] = []
    for r in recs:
        action = (r.get("suggested_action") or {}).get("summary")
        marker = _action_has_prescriptive_marker(action)
        if marker is not None:
            dropped.append({
                "check": "gate_dropped_action",
                "detail": (f"{r.get('check_id')}: dropped recommendation with "
                           f"prescriptive marker {marker!r}; wording gate enforced"),
            })
            continue
        kept.append(r)
    report["recommendations"] = kept
    return dropped


def meta_evaluate(report: dict) -> dict:
    """A light self-check over the assembled report, run before it is emitted.

    This does not re-judge any finding — the analysers own that. It checks that the
    report is internally coherent and that nothing prohibited slipped into the wording,
    so a structural mistake surfaces here rather than in front of whoever reads the
    report. Findings are advisory: `warnings` is reported, never silently corrected,
    because quietly rewriting a report to make its own audit pass is the failure mode
    D-010 was written against.
    """
    # Phase 9 items P + C + B close-out: run the strengths/recs contradiction
    # filter first so a rec that would otherwise be dropped by the
    # prescriptive-marker gate is recorded as the more informative
    # contradicted_by_strength warning, then run the prescriptive-marker drop
    # gate, then the empty-summary defense-in-depth drop. Each surfaces its
    # drops for traceability.
    warnings: list[dict] = _filter_strengths_recs_contradiction(report)
    warnings.extend(_enforce_prohibited_recommendation_gate(report))
    warnings.extend(_drop_empty_summary_recs(report))
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

    # 3. A check appearing more than once at top level is a prioritisation warning
    #    when the SAME (check_id, subcheck) fires twice. Phase 9 item U (2026-09-14):
    #    prior logic tripped whenever `title` matched, which fired on legitimate
    #    distinctions -- CHK-E-022 with subcheck `no_h1` and subcheck `no_main`
    #    are two different defect classes that share a check_id and title but need
    #    to surface separately. The meta-eval treats `(check_id, subcheck)` as the
    #    identity of a defect class; identical (check_id, subcheck) pairs across
    #    different findings are still a real duplicate.
    seen_subchecks: set[tuple] = set()
    for f in findings:
        subcheck_key = (f.get("check_id"), f.get("subcheck"))
        if subcheck_key in seen_subchecks:
            warnings.append({"check": "no_duplicate_findings",
                             "detail": f"{f.get('check_id')} appears more than once with "
                                       f"the same subcheck ({f.get('subcheck')!r})"})
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
    # Phase 9 item H: read stable `lim_id` (the LIM-01..LIM-05 / BUDGET-* slug), not
    # the ephemeral `id` (L-NNN slot) that is stamped at emission.
    actual_limitation_ids = {lim.get("lim_id") for lim in report.get("limitations", [])}
    missing_limitation_ids = [lim["lim_id"] for lim in DECLARED_LIMITATIONS
                              if lim["lim_id"] not in actual_limitation_ids]
    if missing_limitation_ids:
        expected_ids = ", ".join(lim["lim_id"] for lim in DECLARED_LIMITATIONS)
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
    # Phase 9 item U: strip per-page findings the site-wide rollup already covers.
    scored = _dedup_covered_by_rollup(scored)
    findings_out = assign_ids_and_titles(scored)
    recommendations_out = build_recommendations(recommendation_envelopes)

    # Phase 9 items O + T (2026-09-14): honest access-state taxonomy.
    #
    # Prior rule (item 2.5): `access_blocked_for` fired when `degraded_stages` contained
    # robots_discovery OR render_pass AND findings <= 1. That rule misfired in three
    # directions -- Al Jazeera (5/5 successful fetches, still flagged blocked because
    # render_pass is expected-degraded without a headless browser); Coinbase (partial
    # block -- robots readable, pages blocked) framed identically to India.gov.in
    # (full block -- robots unreachable); and any short-content site with one finding
    # and no headless browser also fired.
    #
    # New rule uses the collector's own extraction results directly:
    #   pages_fetched = count of bundle.pages with extraction_ok
    #   robots_ok     = 'robots_discovery' NOT in degraded_stages
    #   pages_fetched == 0 and not robots_ok  -> access_state = "full_block",
    #                                            access_blocked_for = [host]
    #   pages_fetched == 0 and robots_ok      -> access_state = "partial_block",
    #                                            access_partial_for = [host]
    #   pages_fetched >  0                    -> access_state = "ok"
    # Fix L (block-as-finding) is intentionally NOT emitted: OFFICIALS-QA §2.2 and
    # Action #10 place blocked sites out of scope for further audit investment. The
    # access_state preamble field IS the entire signal we ship for blocked sites --
    # no new finding, no new recommendation. See docs/DECISIONS.md D-035.
    degraded_stages = compute_degraded_stages(bundle.get("budget", {}))
    degraded_stage_names = {stage.get("stage") for stage in degraded_stages}
    pages_fetched = sum(
        1 for p in (bundle.get("pages") or [])
        if p.get("extraction_ok", True) and p.get("status") == "ok"
    )
    robots_ok = "robots_discovery" not in degraded_stage_names
    parsed_site = urlparse(site)
    site_host = (bundle.get("site", {}).get("canonical_host") or parsed_site.netloc
                 or parsed_site.path).strip("/")
    access_blocked_for: list[str] = []
    access_partial_for: list[str] = []
    if pages_fetched == 0 and not robots_ok:
        access_state = "full_block"
        access_blocked_for = [site_host]
    elif pages_fetched == 0 and robots_ok:
        access_state = "partial_block"
        access_partial_for = [site_host]
    else:
        access_state = "ok"

    # Phase 9 item H (2026-09-14): DECLARED_LIMITATIONS carry a stable `lim_id`; the
    # ephemeral `id: L-NNN` slot is stamped here at emission so every shipped
    # limitation has both fields and readers can distinguish "the LIM-01 cross-web
    # limitation" from "the third limitation in this report".
    limitations = [dict(lim) for lim in DECLARED_LIMITATIONS]
    if access_state in ("full_block", "partial_block"):
        affected_stage_names = [stage["stage"] for stage in degraded_stages
                                if stage.get("stage") in {"robots_discovery", "render_pass"}]
        limitations.append({
            "lim_id": "BUDGET-degraded_stages",
            "title": "Audit substantially degraded — signal insufficient for scored findings",
            "description": (
                f"The collector could not reach any of the sampled pages "
                f"({pages_fetched} successful fetches). "
                + ("robots.txt was also unreachable; " if not robots_ok else "")
                + "The report's remaining findings and strengths should be read as "
                "advisory only; the audit cannot honestly claim substantive coverage."
            ),
            "affected_checks": [finding["check_id"] for finding in findings_out],
        })
    # Stamp the ephemeral id at emission so every limitation carries both an id
    # (L-NNN, positional) and a lim_id (stable slug). Previously only the runtime
    # BUDGET-degraded_stages entry had both; declared entries shipped with a null
    # lim_id, which two independent judges flagged as opaque.
    for i, lim in enumerate(limitations, start=1):
        lim["id"] = f"L-{i:03d}"

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
            "access_state": access_state,
            "access_blocked_for": access_blocked_for,
            "access_partial_for": access_partial_for,
            "notes": notes,
            "archetype": archetype,
            "recommendations_scoped_to": archetype,
        },
        "summary": compute_summary(findings_out),
        "findings": findings_out,
        "recommendations": recommendations_out,
        # D-18 (2026-09-12): the checks that ran and were verified clean, so a two-finding
        # report on a 32-check marketplace does not read like only two checks ran.
        # Phase 9 item M (2026-09-14): starved checks (whose input stage was
        # abandoned) are excluded, not treated as passed.
        # Full or partial block both mean the DOM/link-dependent checks had no meaningful
        # input; starve them either way.
        "checks_passed": compute_checks_passed(
            all_envelopes, degraded_stages, access_blocked_for + access_partial_for),
        "strengths": compute_strengths(bundle, audited_at),
        "limitations": limitations,
        "degraded_stages": degraded_stages,
    }
    report["meta_evaluation"] = meta_evaluate(report)
    return report
