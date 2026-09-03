"""Assemble the final evidence bundle from already-built sections.

The actual network calls (robots.txt fetch, page fetches, the rendered-page pass, link
and anchor HEAD checks) are made by the agent's declared tools per SKILL.md's numbered
procedure — this module's job is purely to combine their results, in the shape
docs/BUNDLE-SCHEMA.md fixes, and to compute `budget` from stage timings. It never fetches
anything itself.
"""
from __future__ import annotations

REQUIRED_SECTIONS = ("site", "robots", "discovery", "pages", "rendered", "links", "anchors", "budget")


def build_site_section(input_target: str, canonical_host: str, origin: str, scheme: str,
                        redirect_chain: list[str], tls_valid: bool,
                        archetype: str, archetype_confidence: float,
                        status: str = "ok", reason: str | None = None) -> dict:
    return {
        "status": status,
        "reason": reason,
        "input": input_target,
        "canonical_host": canonical_host,
        "origin": origin,
        "scheme": scheme,
        "redirect_chain": redirect_chain,
        "tls_valid": tls_valid,
        "archetype": archetype,
        "archetype_confidence": archetype_confidence,
    }


def build_discovery_section(sitemap_found: bool, sitemap_urls_count: int,
                             inventory: list[dict], sampled_static: list[str],
                             sampled_rendered: list[str], sampling_seed: str) -> dict:
    return {
        "status": "ok",
        "reason": None,
        "sitemap_found": sitemap_found,
        "sitemap_urls_count": sitemap_urls_count,
        "inventory": inventory,
        "sampled_static": sampled_static,
        "sampled_rendered": sampled_rendered,
        "sampling_seed": sampling_seed,
    }


def build_budget_section(stages: list[dict], cap_s: int = 300) -> dict:
    """stages: [{'name', 'budget_s', 'actual_s', 'abandoned', ...}]."""
    total_s = sum(s.get("actual_s") or 0 for s in stages)
    return {"status": "ok", "reason": None, "stages": stages, "total_s": round(total_s, 1), "cap_s": cap_s}


def build_bundle(
    site: dict,
    robots: dict,
    discovery: dict,
    pages: list[dict],
    rendered: list[dict],
    links: dict,
    anchors: dict,
    budget: dict,
    schema_version: str = "1.0.0",
) -> dict:
    bundle = {
        "schema_version": schema_version,
        "site": site,
        "robots": robots,
        "discovery": discovery,
        "pages": pages,
        "rendered": rendered,
        "links": links,
        "anchors": anchors,
        "budget": budget,
    }
    missing = [k for k in REQUIRED_SECTIONS if k not in bundle]
    if missing:
        raise ValueError(f"bundle missing required sections: {missing}")
    return bundle


def empty_bundle_for_robots_unavailable(site: dict, robots: dict, budget: dict) -> dict:
    """procedure.md §2: if robots.txt itself is unavailable, collection stops there and
    the bundle is emitted with only `site` and `robots` populated. Every other section is
    'unavailable' with a shared reason so analysers reading them fail closed correctly."""
    reason = "robots_unavailable_collection_stopped"
    empty_pages: list[dict] = []
    empty_rendered: list[dict] = []
    return build_bundle(
        site=site,
        robots=robots,
        discovery={"status": "unavailable", "reason": reason, "sitemap_found": False,
                   "sitemap_urls_count": 0, "inventory": [], "sampled_static": [],
                   "sampled_rendered": [], "sampling_seed": None},
        pages=empty_pages,
        rendered=empty_rendered,
        links={"status": "unavailable", "reason": reason, "checked_count": 0, "results": [], "skipped": []},
        anchors={"status": "unavailable", "reason": reason, "declared": [], "checked_count": 0, "results": []},
        budget=budget,
    )
