"""CHK-D-001 and CHK-D-002 — evaluated purely from bundle['robots'].

Pure function, no network access, no tools declared (matches this skill's frontmatter).
Reference: crawl-access-audit/SKILL.md.
"""
from __future__ import annotations

RETRIEVAL_CLASSES = {"retrieval", "hybrid"}  # ai-crawler-agents.md rule 2: hybrid-at-root
TRAINING_CLASSES = {"training"}


def _envelope(check_id: str, state: str, evidence: str, severity: str | None,
              evidence_strength: str, suggested_action: dict | None,
              locus: dict | None = None, suppressed_by: list[str] | None = None) -> dict:
    return {
        "check_id": check_id,
        "state": state,
        "locus": locus or {"url": None, "selector": None},
        "evidence": evidence,
        "severity": severity,
        "evidence_strength": evidence_strength,
        "suggested_action": suggested_action,
        "suppressed_by": suppressed_by or [],
    }


def evaluate(bundle: dict) -> list[dict]:
    robots = bundle.get("robots", {})

    # Phase 10 P10-2: locus points at the actual robots.txt URL when we have one, so
    # readers can trace the finding back to the specific file whose contents supplied
    # the evidence. Line numbers travel in the evidence string; the locus URL is the
    # file, not `null`.
    origin = (bundle.get("site", {}) or {}).get("origin") or ""
    robots_url = f"{origin.rstrip('/')}/robots.txt" if origin else None

    if robots.get("status") != "ok":
        reason = robots.get("reason") or "robots.txt unavailable"
        loc = {"url": robots_url, "selector": None} if robots_url else None
        return [
            _envelope("CHK-D-001", "not_determinable", reason, None, "HARD-MECHANICAL", None, locus=loc),
            _envelope("CHK-D-002", "not_determinable", reason, None, "CORRELATIONAL", None, locus=loc),
        ]

    agents: dict = robots.get("agents", {})

    blocked_retrieval = [
        (name, info) for name, info in agents.items()
        if info.get("class") in RETRIEVAL_CLASSES and info.get("allowed_root") is False
    ]
    blocked_training = [
        (name, info) for name, info in agents.items()
        if info.get("class") in TRAINING_CLASSES and info.get("allowed_root") is False
    ]

    findings: list[dict] = []

    # Phase 10 P10-2: robots-based findings carry a real locus URL when we have the
    # site origin. The alphabetically-first matched line supplies the selector so a
    # reader can jump straight to the offending Disallow line without scanning.
    def _locus_from_line(line: int | None) -> dict | None:
        if not robots_url:
            return None
        sel = f"L{line}" if isinstance(line, int) else None
        return {"url": robots_url, "selector": sel}

    if blocked_retrieval:
        # Deterministic: report the alphabetically-first blocked retrieval agent as the
        # primary locus, but the evidence string enumerates all of them.
        blocked_retrieval.sort(key=lambda pair: pair[0].lower())
        parts = [
            f"robots.txt line {info['matched_line']}: Disallow: {info['disallow_rules'][0] if info['disallow_rules'] else '/'} "
            f"applies to {name} (retrieval-time AI crawler)."
            for name, info in blocked_retrieval
        ]
        # D-16 (2026-09-12): action now names the intent question first. A newsroom that
        # blocks AI crawlers as a licensing position is not misconfigured, and telling
        # them to "narrow the Disallow" reads as "unblock the scrapers" -- a fix worse
        # than the finding. The finding itself is still critical: this IS the direct
        # cause of retrieval-time invisibility. The action asks whether the block was
        # deliberate; if it wasn't, the mechanical fix comes next.
        agent_names = ", ".join(name for name, _ in blocked_retrieval)
        findings.append(_envelope(
            "CHK-D-001", "present", " ".join(parts), "critical", "HARD-MECHANICAL",
            {
                "summary": f"This block is the direct reason retrieval-time AI "
                           f"assistants cannot cite pages on this site. If it is a "
                           f"deliberate licensing decision for {agent_names}, no change "
                           f"is required -- but note the visibility trade-off. "
                           f"Otherwise, narrow the Disallow rule to the specific paths "
                           f"that need protection rather than the site root.",
                "priority": "critical",
            },
            locus=_locus_from_line(blocked_retrieval[0][1].get("matched_line")),
        ))
    else:
        findings.append(_envelope("CHK-D-001", "absent", "No retrieval-time AI crawler is "
                                   "blocked at root.", None, "HARD-MECHANICAL", None,
                                   locus=_locus_from_line(None)))

    if not blocked_retrieval and blocked_training:
        blocked_training.sort(key=lambda pair: pair[0].lower())
        names = ", ".join(name for name, _ in blocked_training)
        findings.append(_envelope(
            "CHK-D-002", "present",
            f"robots.txt blocks {names} (a training-corpus crawler) but permits "
            f"retrieval-time AI crawlers.",
            "low", "CORRELATIONAL",
            {
                # D-2 (2026-09-12): "parametric-memory coverage" is jargon a site owner
                # cannot act on. Rephrased as what the block actually costs and doesn't
                # cost, in the reader's terms.
                "summary": "Blocking a training-corpus crawler while leaving retrieval "
                           "crawlers open is usually deliberate: the site can still be "
                           "cited by AI assistants at answer time, and only future "
                           "training runs are opted out. If that trade-off matches the "
                           "site's position, no change is needed.",
                "priority": "low",
            },
            suppressed_by=[],
            locus=_locus_from_line(blocked_training[0][1].get("matched_line")),
        ))
    elif blocked_retrieval and blocked_training:
        findings.append(_envelope("CHK-D-002", "not_applicable",
                                   "Suppressed: CHK-D-001 already fired.", None,
                                   "CORRELATIONAL", None, suppressed_by=["CHK-D-001"],
                                   locus=_locus_from_line(None)))
    else:
        findings.append(_envelope("CHK-D-002", "absent", "No training-corpus crawler is "
                                   "blocked while retrieval access remains open.", None,
                                   "CORRELATIONAL", None, locus=_locus_from_line(None)))

    return findings
