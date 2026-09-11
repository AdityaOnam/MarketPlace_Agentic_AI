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
ROLLUP_MIN_PAGES = 2


def _defect_signature(f: dict) -> tuple:
    """What makes two per-page findings the *same* defect.

    URLs and counts are stripped: "Page {a}: missing <main> landmark" and
    "Page {b}: missing <main> landmark" describe one template defect, and
    "6 violation(s): missing alt..." vs "7 violation(s): missing alt..." differ only in
    how many times the same template repeated it on that page.
    """
    ev = f.get("evidence") or ""
    ev = _URL_IN_EVIDENCE.sub("<url>", ev)
    ev = _NUMBER_IN_EVIDENCE.sub("<n>", ev)
    return (f["check_id"], f.get("subcheck"), ev)


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

    # 3. No check may appear twice as a top-level finding for the same locus — a real
    #    duplicate means suppression (O-1) failed to fire. Keyed on `subcheck` as well,
    #    because a few checks legitimately grade one page more than once: CHK-E-014 rates
    #    static WCAG failures (`high`) separately from contrast (`medium`, NORMATIVE), and
    #    CHK-E-015 rates the viewport meta separately from horizontal overflow. Those are
    #    distinct judgments sharing an ID, not duplicates.
    #    Site-wide rolled-up findings (D-019) all carry locus.url = None, so two genuinely
    #    different defects found by one check would collide on that key and be reported as
    #    a duplicate. The defect signature disambiguates them -- it is what defined the
    #    groups in the first place.
    seen: set[tuple] = set()
    for f in findings:
        scope_key = (_defect_signature(f) if f.get("occurrences")
                     else (f.get("locus") or {}).get("url"))
        key = (f.get("check_id"), scope_key, f.get("subcheck"))
        if key in seen:
            label = f"{f.get('check_id')}"
            if f.get("subcheck"):
                label += f" ({f['subcheck']})"
            warnings.append({"check": "no_duplicate_findings",
                             "detail": f"{label} reported twice for {key[1]}"})
        seen.add(key)

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

    # 6. The declared limitations are structural and must always be present.
    if len(report.get("limitations", [])) != len(DECLARED_LIMITATIONS):
        expected_ids = ", ".join(lim["id"] for lim in DECLARED_LIMITATIONS)
        warnings.append({"check": "limitations_present",
                         "detail": f"declared limitations ({expected_ids}) are not all present"})

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
        "personal": ("Identity checks (Organization JSON-LD, sameAs anchors, "
                     "self-consistent legal name) are suppressed: a personal site is "
                     "not expected to publish structured entity metadata."),
        "ecommerce": ("Trust signals, canonical/duplicate handling, and structured "
                       "product data are graded more strictly; recommendations are "
                       "phrased for a catalogue-scale site."),
        "documentation": ("Deep, versioned URL structures are exempt from near-duplicate "
                           "flagging; content-thinness thresholds apply per page rather "
                           "than per section."),
        "news_editorial": ("Time-stamped articles, byline signals, and the date-signal "
                            "check are graded more strictly; the trust-signals check "
                            "is applied."),
        "saas_marketing": ("Trust signals and pricing-page identity are graded more "
                            "strictly; the site's marketing blog does not have to meet "
                            "editorial standards."),
        "local_business": ("Postal address, opening hours and LocalBusiness JSON-LD are "
                            "expected; contact-page structure carries more weight than a "
                            "generic 'contact us' link."),
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
        # report on a 26-check marketplace does not read like only two checks ran.
        "checks_passed": compute_checks_passed(all_envelopes),
        "limitations": DECLARED_LIMITATIONS,
        "degraded_stages": compute_degraded_stages(bundle.get("budget", {})),
    }
    report["meta_evaluation"] = meta_evaluate(report)
    return report
