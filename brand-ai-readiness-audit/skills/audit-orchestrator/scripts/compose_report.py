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
    "CHK-E-015": "Mobile viewport blocks zoom or overflows horizontally",
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
    {
        "id": "LIM-01", "mechanism": "D",
        "reason": "Actual agreement across the wider web about the brand's facts requires "
                   "a search or web-scale index API. No free, deterministic, rate-safe "
                   "source exists.",
        "note": "CHK-D-025/026/027 audit only the anchoring the site itself provides for "
                 "that corroboration, not corroboration itself.",
    },
    {
        "id": "LIM-02", "mechanism": "D",
        "reason": "Detecting a same-name collision with an unrelated entity requires a "
                   "corpus of other entities.",
        "note": "CHK-D-027 covers only self-consistency, the site-side half.",
    },
    {
        "id": "LIM-03", "mechanism": "B",
        "reason": "Live-querying a generative engine would break determinism, the "
                   "5-minute budget, and reproducibility.",
        "note": "This audit measures retrievability and correctness of what the site "
                 "exposes, never observed citation outcomes.",
    },
    {
        "id": "LIM-04", "mechanism": "E",
        "reason": "Field engagement outcomes (bounce, dwell, scroll, conversion, task "
                   "success) are not observable read-only.",
        "note": "Reported not_determinable where the gap is itself actionable.",
    },
    {
        "id": "LIM-05", "mechanism": "D",
        "reason": "llms.txt is not recommended as a substantive fix: a 137k-domain "
                   "measurement found 97% of existing llms.txt files were never requested. "
                   "This audit declines to recommend adding one on that evidence (D-007).",
        "note": "Stated here rather than omitted (D-014) — the officials' Q&A confirms "
                "recommending it is an acceptable position, so silence about it would look "
                "indistinguishable from having missed it.",
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
ROLLUP_MIN_PAGES = 3


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


def roll_up_site_wide(findings: list[dict]) -> list[dict]:
    """Collapse one defect repeated across pages into one finding with a page count.

    Added 2026-09-04 from the Stage B negative-control screen, which is the first time
    this marketplace met real multi-page sites. A single site-template defect -- one
    unnamed link in a shared header, one missing `<main>` in a shared layout -- was
    emitting one finding per sampled page: 17 findings for one fix, on a site with 20
    pages sampled. Every one of them was true, and the report was still wrong, because a
    reader cannot tell 17 problems from one problem seen 17 times.

    This is the rubric line the officials were most explicit about: "Not just a laundry
    list of items. The real ingenuity lies in how you order them" (OFFICIALS-QA.md §3.1).
    Ordering cannot help when one defect occupies 17 of the slots being ordered.

    A defect seen on fewer than `ROLLUP_MIN_PAGES` pages is left alone -- at one or two
    pages it is plausibly specific to those pages, and collapsing it would hide the locus
    a reader needs.
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
        if len(group) < ROLLUP_MIN_PAGES:
            out.extend(group)
            continue
        # Severity of the rolled-up finding is the worst in the group, never an average:
        # a defect is as serious as its worst instance.
        worst = min(group, key=lambda f: SEVERITY_ORDER.get(f.get("severity"), 99))
        merged = dict(worst)
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
            "locus": r.get("locus"),
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

    # The site's vertical is surfaced because it is not decoration: archetype gates which
    # checks run at all (a personal site is exempt from identity-anchor checks, a
    # non-commercial one from trust signals) and shapes how each suggested action is
    # worded. A reader needs to know which vertical the recommendations were written for.
    archetype = bundle.get("site", {}).get("archetype", "unknown")

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
        "limitations": DECLARED_LIMITATIONS,
        "degraded_stages": compute_degraded_stages(bundle.get("budget", {})),
    }
    report["meta_evaluation"] = meta_evaluate(report)
    return report
