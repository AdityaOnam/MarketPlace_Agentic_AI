"""Compose the final audit report from the four analysers' raw finding envelopes.

Implements audit-orchestrator/SKILL.md steps 3-6: cross-skill suppression (rule O-1),
JS-only root-cause dedup (rule O-2), findings/recommendations/limitations separation,
and report assembly. Pure function — this module never invokes a skill or the network;
the agent following SKILL.md calls the collector and the four analysers and passes their
combined envelope list here.
"""
from __future__ import annotations

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
    "CHK-E-023": "Mobile ad density exceeds Better Ads threshold",
    "CHK-E-024": "Missing trust signals",
}

JS_ONLY_DEDUP_TITLE = ("JavaScript-only site — primary content invisible to non-rendering "
                        "AI retrievers")

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
]

# procedure.md's "Runtime budget and the shared render pass" table, reproduced here so
# budget arbitration doesn't have to re-derive it at run time.
STAGE_CONSUMERS = {
    "robots_discovery": ["CHK-D-001", "CHK-D-002"],
    "static_fetch": [c for c in CHECK_TITLES if c not in
                     ("CHK-D-001", "CHK-D-002", "CHK-D-026")],
    "render_pass": ["CHK-D-003", "CHK-E-014", "CHK-E-015", "CHK-E-016", "CHK-E-018",
                     "CHK-E-019", "CHK-E-023"],
    "internal_links": ["CHK-D-009"],
    "offsite_anchors": ["CHK-D-026"],
}

JS_ONLY_CLUSTER = ["CHK-D-003", "CHK-D-004", "CHK-D-005", "CHK-E-019"]


def _by_check_and_locus(findings: list[dict]) -> dict[tuple[str, str | None], dict]:
    return {(f["check_id"], (f.get("locus") or {}).get("url")): f for f in findings}


def apply_suppression(findings: list[dict]) -> list[dict]:
    """Rule O-1: CHK-E-019 yields to CHK-D-003 when both are present for the homepage.

    This is the one genuinely cross-skill suppression this function needs to apply.
    CHK-D-002/CHK-D-001 and CHK-D-010/CHK-D-004 are already resolved inside their owning
    analysers (crawl-access-audit, render-extractability-audit respectively) before their
    envelopes ever reach here — re-applying that logic at this layer would be redundant
    and is deliberately not done.
    """
    d003 = next((f for f in findings if f["check_id"] == "CHK-D-003" and f["state"] == "present"), None)
    e019 = next((f for f in findings if f["check_id"] == "CHK-E-019" and f["state"] == "present"), None)

    if d003 is not None and e019 is not None:
        e019["state"] = "suppressed"
        e019["suppressed_by"] = list(set(e019.get("suppressed_by", []) + ["CHK-D-003"]))

    return findings


def dedup_js_only_cluster(findings: list[dict]) -> tuple[list[dict], list[dict]]:
    """Rule O-2: collapse CHK-D-003/004/005/E-019 into one finding when ALL FOUR fire on
    the homepage. Requires the full pattern — collapsing on a partial match risks hiding
    a genuinely independent defect, which SKILL.md's false-positive discipline explicitly
    warns against ("when in doubt, report separately").

    Returns (remaining_findings, consequences_of_root) — remaining_findings has the
    cluster members removed (root finding kept, marked with `consequences`); the caller
    assembles the merged evidence/title from the root plus the returned consequences.
    """
    home_url = None
    d003 = next((f for f in findings if f["check_id"] == "CHK-D-003" and f["state"] == "present"), None)
    if d003 is None:
        return findings, []
    home_url = (d003.get("locus") or {}).get("url")

    cluster_members = []
    for check_id in ("CHK-D-004", "CHK-D-005", "CHK-E-019"):
        match = next((f for f in findings
                      if f["check_id"] == check_id
                      and (f.get("locus") or {}).get("url") == home_url
                      and f["state"] in ("present", "suppressed")), None)
        cluster_members.append(match)

    if any(m is None for m in cluster_members):
        return findings, []  # partial pattern: report independently, per SKILL.md rule

    consequences = [{"check_id": m["check_id"], "evidence": m["evidence"]} for m in cluster_members]
    d003["title"] = JS_ONLY_DEDUP_TITLE
    d003["consequences"] = consequences

    consumed_ids = {id(m) for m in cluster_members}
    remaining = [f for f in findings if id(f) not in consumed_ids]
    return remaining, consequences


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
    #    duplicate means suppression or dedup failed to fire. Keyed on `subcheck` as well,
    #    because a few checks legitimately grade one page more than once: CHK-E-014 rates
    #    static WCAG failures (`high`) separately from contrast (`medium`, NORMATIVE), and
    #    CHK-E-015 rates the viewport meta separately from horizontal overflow. Those are
    #    distinct judgments sharing an ID, not duplicates.
    seen: set[tuple] = set()
    for f in findings:
        key = (f.get("check_id"), (f.get("locus") or {}).get("url"), f.get("subcheck"))
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

    # 6. The four declared limitations are structural and must always be present.
    if len(report.get("limitations", [])) != len(DECLARED_LIMITATIONS):
        warnings.append({"check": "limitations_present",
                         "detail": "declared limitations LIM-01..04 are not all present"})

    return {
        "checks_run": ["summary_reconciles", "severity_counts_reconcile", "finding_complete",
                        "no_duplicate_findings", "known_check_id", "prohibited_recommendation",
                        "limitations_present"],
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
    """all_envelopes: the concatenated output of all four analysers, unmodified.
    bundle: the evidence bundle (for `bundle['budget']` and access-block framing)."""
    findings = list(all_envelopes)
    findings = apply_suppression(findings)
    findings, _consequences = dedup_js_only_cluster(findings)

    scored, recommendation_envelopes = split_findings_recommendations(findings)
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
