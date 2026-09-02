#!/usr/bin/env python3
"""
Entrypoint runner: invokes every specialist check script, merges their
findings, applies the severity/priority rubric, and emits ONE audit report.

Read-only. stdlib only. Deterministic: same input -> same output ordering.

Usage:
    python run_audit.py --url example.com [--max-pages 8] [--out audit-report.json]
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "..")           # <marketplace>/skills
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "lib"))
import fetch_lib as F  # noqa: E402

# Ordered: layer 0/1 gates the rest.
CHECK_SCRIPTS = [
    ("crawl-access-audit",      "check_crawl_access.py"),
    ("engagement-onsite-audit", "check_engagement.py"),
    # add further skills here; the orchestrator needs no other change
]

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
CONF_ORDER = {"high": 0, "medium": 1, "low": 2}


def run_skill(skill_id, script, url, max_pages, timeout=90):
    """Run one check script as a subprocess. Never raises."""
    path = os.path.join(SKILLS, skill_id, "scripts", script)
    if not os.path.exists(path):
        return None, f"{skill_id}: script not found"
    try:
        proc = subprocess.run(
            [sys.executable, path, "--url", url, "--max-pages", str(max_pages)],
            capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            return None, f"{skill_id}: exited {proc.returncode}"
        return json.loads(proc.stdout).get("findings", []), None
    except subprocess.TimeoutExpired:
        return None, f"{skill_id}: timed out after {timeout}s"
    except Exception as e:
        return None, f"{skill_id}: {e}"


def dedupe(findings):
    """Collapse duplicates by (check_id, sorted affected urls); keep worst severity."""
    merged = {}
    for f in findings:
        key = (f.get("check_id"), tuple(sorted(f.get("affected_urls", []))))
        if key in merged:
            keep = merged[key]
            if SEV_ORDER[f["severity"]] < SEV_ORDER[keep["severity"]]:
                merged[key] = f
        else:
            merged[key] = f
    return list(merged.values())


def rank(findings):
    """Deterministic ordering: severity, then confidence, then title."""
    return sorted(findings, key=lambda f: (
        SEV_ORDER.get(f.get("severity"), 9),
        CONF_ORDER.get(f.get("confidence", "medium"), 1),
        f.get("check_id", ""),
        f.get("title", ""),
    ))


def proactive(findings):
    """Beyond-defect recommendations, skipped where a real defect already covers it."""
    fired = {f.get("check_id") for f in findings}
    pool = [
        ("P-01", "Publish a canonical, quotable facts page",
         "Add an /about or /facts page stating the brand's atomic facts (legal name, "
         "founding year, HQ, what it sells, who it serves, pricing model, contact) in "
         "short declarative sentences.",
         "Assistants build answers from spans they can quote verbatim. A fact spread "
         "across a hero video and a PDF has no quotable span; the same fact in one clean "
         "sentence does - and gives every other site one consistent source to copy.", None),
        ("P-03", "Build the sameAs identity graph",
         "Link official profiles (LinkedIn, Crunchbase, Wikidata, GitHub, app stores) "
         "from Organization.sameAs, and make each of those profiles link back.",
         "Disambiguation is a graph problem. Mutual links between independent sources are "
         "what let a system decide which similarly named entity you are.", None),
        ("P-04", "Seed independent corroboration off-site",
         "Get the same phrasing of the core facts onto sources you do not control - "
         "industry directories, press, partner pages, conference bios.",
         "Single-source claims are treated as fragile. Repetition across unrelated "
         "domains is the strongest trust signal a machine has.", None),
        ("P-05", "Show and maintain a visible last-updated date",
         "Display a last-updated date on pricing, docs and policy pages and mirror it in "
         "schema dateModified - and actually revise the content when you bump it.",
         "Freshness is a tiebreaker between competing sources; an undated page loses to a "
         "dated rival even when its content is newer.", None),
        ("P-06", "Answer real questions in the visitor's own words",
         "Add an FAQ using real query phrasing, answer-first, marked up as FAQPage.",
         "Question-shaped headings match question-shaped queries, and an answer-first "
         "paragraph is directly liftable as a citation.", "EN-03"),
    ]
    out = []
    for cid, title, action, mech, skip_if in pool:
        if skip_if and skip_if in fired:
            continue
        out.append({
            "check_id": cid, "category": "discoverability", "proactive": True,
            "title": title, "severity": "info", "confidence": "medium",
            "evidence": "No defect detected for this; recommended as a proactive "
                        "improvement based on how retrieval and citation work.",
            "affected_urls": [],
            "suggested_action": {"summary": action, "priority": "medium",
                                 "mechanism": mech, "steps": [], "effort": "medium"},
        })
    return out[:5]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--max-pages", type=int, default=8)
    ap.add_argument("--out", default="audit-report.json")
    args = ap.parse_args()

    started = time.time()
    base, host = F.normalise(args.url)

    all_findings, not_assessed, ran = [], [], []
    for skill_id, script in CHECK_SCRIPTS:
        result, err = run_skill(skill_id, script, base, args.max_pages)
        if err:
            not_assessed.append(err)
        else:
            ran.append(skill_id)
            all_findings.extend(result)

    findings = rank(dedupe(all_findings)) + proactive(all_findings)
    for i, f in enumerate(findings, 1):
        f["id"] = f"F-{i:03d}"

    counts = {s: 0 for s in SEV_ORDER}
    for f in findings:
        counts[f["severity"]] += 1

    report = {
        "site": host,
        "audited_at": datetime.datetime.now(datetime.timezone.utc)
                              .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": {
            "pages_crawled": args.max_pages,
            "robots_respected": True,
            "checks_run": ran,
            "checks_not_assessed": not_assessed,
            "duration_seconds": round(time.time() - started, 1),
        },
        "summary": {"total_findings": len(findings), **counts},
        "findings": findings,
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n--- {host}: {len(findings)} findings "
          f"({counts['critical']} critical, {counts['high']} high, "
          f"{counts['medium']} medium) -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
