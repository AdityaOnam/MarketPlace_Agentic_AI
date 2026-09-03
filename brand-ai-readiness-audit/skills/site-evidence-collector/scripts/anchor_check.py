"""Build the `anchors` bundle section — the only off-origin evidence in the audit.

Reference: procedure.md §7. Pure function over already-executed HEAD results; the actual
off-site requests (max 8, one per registrable domain, 3s timeout, <=3 redirects) are made
by the agent's http_fetch tool per SKILL.md step 7, not by this module.
"""
from __future__ import annotations

MAX_ANCHORS = 8
BOT_BLOCKED_STATUSES = {401, 403, 429}


def build_anchors_section(declared: list[dict], raw_results: list[dict]) -> dict:
    """declared: [{'url', 'source', 'host'}] from sameAs / outbound_profile_links.
    raw_results: [{'url', 'http_status'}] for up to MAX_ANCHORS of `declared`, one per
    registrable domain, already executed.

    Encodes the load-bearing rule structurally: 401/403/429 -> resolved: null with
    `bot_blocked_not_broken`, never `false`. This is deliberately not left for the
    analyser to remember (docs/BUNDLE-SCHEMA.md `anchors` section)."""
    if not declared:
        return {"status": "ok", "reason": None, "declared": [], "checked_count": 0, "results": []}

    results = []
    for r in raw_results[:MAX_ANCHORS]:
        status = r.get("http_status")
        if status in BOT_BLOCKED_STATUSES:
            results.append({"url": r["url"], "http_status": status, "resolved": None,
                             "note": "bot_blocked_not_broken"})
        elif status is None:
            results.append({"url": r["url"], "http_status": None, "resolved": None,
                             "note": "timeout"})
        elif 200 <= status < 400:
            results.append({"url": r["url"], "http_status": status, "resolved": True})
        else:
            results.append({"url": r["url"], "http_status": status, "resolved": False})

    return {
        "status": "ok",
        "reason": None,
        "declared": declared,
        "checked_count": len(results),
        "results": results,
    }


def build_anchors_section_unavailable(declared: list[dict], reason: str) -> dict:
    return {"status": "unavailable", "reason": reason, "declared": declared, "checked_count": 0,
            "results": []}
