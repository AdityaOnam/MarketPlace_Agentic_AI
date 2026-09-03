"""Build the `links` bundle section from raw HEAD-check results. Reference: procedure.md §6."""
from __future__ import annotations

MAX_INTERNAL_LINKS = 20


def build_links_section(head_results: list[dict], skipped: list[dict]) -> dict:
    """head_results: [{'url', 'http_status', 'from_page', 'anchor_text'}], already capped
    at MAX_INTERNAL_LINKS and already HEAD-only by the caller (the agent's http_fetch tool
    invocation, per SKILL.md step 6). skipped: [{'url', 'reason'}] — fragments, mailto:,
    tel:, javascript:, and robots.txt-disallowed paths, recorded so CHK-D-009's FP guard
    can exclude them rather than counting them as untested."""
    return {
        "status": "ok",
        "reason": None,
        "checked_count": len(head_results),
        "results": head_results[:MAX_INTERNAL_LINKS],
        "skipped": skipped,
    }


def build_links_section_unavailable(reason: str) -> dict:
    return {"status": "unavailable", "reason": reason, "checked_count": 0, "results": [], "skipped": []}
