"""Parse and classify robots.txt into the bundle's `robots` section.

Pure function over already-fetched text — this module makes no network request. The
caller (following SKILL.md step 2) fetches `{origin}/robots.txt` with the agent's
http_fetch tool and passes the response here.

Reference: site-evidence-collector/references/procedure.md §2,
site-evidence-collector/references/ai-crawler-agents.md, docs/BUNDLE-SCHEMA.md `robots`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Sourced from references/ai-crawler-agents.md. Keep the two in sync by hand; this table
# is intentionally data, not derived, so it can be extended without touching any check.
AGENT_CLASS = {
    "gptbot": "training",
    "oai-searchbot": "retrieval",
    "chatgpt-user": "retrieval",
    "claudebot": "training",
    "claude-web": "retrieval",
    "claude-user": "retrieval",
    "claude-searchbot": "retrieval",
    "perplexitybot": "retrieval",
    "perplexity-user": "retrieval",
    "google-extended": "training",
    "googlebot": "hybrid",
    "bingbot": "hybrid",
    "applebot-extended": "training",
    "applebot": "hybrid",
    "ccbot": "training",
    "bytespider": "training",
    "amazonbot": "training",
    "meta-externalagent": "training",
    "meta-externalfetcher": "retrieval",
    "cohere-ai": "unknown",
    "diffbot": "unknown",
    "omgilibot": "unknown",
    "anthropic-ai": "unknown",
}


# Phase 10 P10-8: role description per named agent, sourced from vendor docs (see
# references/ai-crawler-agents.md). The class taxonomy above stays: it drives the
# existing CHK-D-001/D-002 routing. This map adds a human-readable role phrase for
# the D-001 evidence string so a reader sees "search-indexing crawler", not just
# "retrieval-time AI crawler" — the plan explicitly asks for retrieval/training/
# hybrid distinctions and role semantics rather than a flat "retrieval-time" claim.
# Agents not in this map fall back to a generic phrase derived from AGENT_CLASS.
AGENT_ROLE = {
    "gptbot":                "training-corpus crawler",
    "oai-searchbot":         "search-indexing crawler",
    "chatgpt-user":          "user-triggered fetch on behalf of ChatGPT",
    "claudebot":             "training-corpus crawler",
    "claude-web":            "retrieval-time crawler",
    "claude-user":           "user-triggered fetch on behalf of Claude",
    "claude-searchbot":      "search-indexing crawler",
    "perplexitybot":         "retrieval-time crawler",
    "perplexity-user":       "user-triggered fetch on behalf of Perplexity",
    "google-extended":       "training-corpus crawler",
    "googlebot":             "general search-indexing crawler (also used for AI Overviews)",
    "bingbot":               "general search-indexing crawler (also used for Copilot)",
    "applebot-extended":     "training-corpus crawler",
    "applebot":              "general search-indexing crawler",
    "ccbot":                 "training-corpus crawler (Common Crawl)",
    "bytespider":            "training-corpus crawler (ByteDance)",
    "amazonbot":             "training-corpus crawler (Amazon)",
    "meta-externalagent":    "training-corpus crawler (Meta)",
    "meta-externalfetcher":  "user-triggered fetch on behalf of Meta AI",
    "cohere-ai":             "AI crawler (role not confirmed in public docs)",
    "diffbot":               "structured-data extraction crawler",
    "omgilibot":             "AI crawler (role not confirmed in public docs)",
    "anthropic-ai":          "AI crawler (role not confirmed in public docs)",
}


def classify_agent(token: str) -> str:
    """Classify a User-agent token. Unknown tokens (including '*') are 'unknown'/'generic'."""
    if token.strip() == "*":
        return "generic"
    return AGENT_CLASS.get(token.strip().lower(), "unknown")


def agent_role(token: str) -> str:
    """Human-readable role for a named agent's D-001 evidence string. Phase 10 P10-8:
    a reader sees the specific role (search indexing / training corpus / user-
    triggered fetch / retrieval-time), not a flat 'retrieval-time' claim across
    every class. Unknown-agent tokens fall back to a class-derived phrase."""
    key = token.strip().lower()
    if key == "*":
        return "any user-agent not explicitly named elsewhere in the file"
    if key in AGENT_ROLE:
        return AGENT_ROLE[key]
    cls = AGENT_CLASS.get(key, "unknown")
    if cls == "training":
        return "training-corpus crawler"
    if cls == "retrieval":
        return "retrieval-time crawler"
    if cls == "hybrid":
        return "general search-indexing crawler used both live and for training"
    return "role not confirmed in public docs"


@dataclass
class _Block:
    agents: list[str] = field(default_factory=list)
    disallow: list[tuple[str, int]] = field(default_factory=list)  # (rule, line_no)
    allow: list[tuple[str, int]] = field(default_factory=list)
    crawl_delay: float | None = None


def _parse_blocks(text: str) -> list[_Block]:
    """Group User-agent lines that share a rule block, per the robots exclusion standard.

    A block starts at one or more consecutive `User-agent:` lines and ends at the next
    `User-agent:` line that follows a non-User-agent directive (i.e. once rules have
    started, a new User-agent line starts a new block).
    """
    blocks: list[_Block] = []
    current: _Block | None = None
    seen_rule_in_current = False

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()

        if key == "user-agent":
            if current is None or seen_rule_in_current:
                current = _Block()
                blocks.append(current)
                seen_rule_in_current = False
            current.agents.append(value)
        elif current is None:
            # Directive before any User-agent line: malformed: ignore per "be liberal in
            # what you accept" — never fabricate a block that was never declared.
            continue
        elif key == "disallow":
            seen_rule_in_current = True
            if value != "":
                current.disallow.append((value, line_no))
            else:
                # Empty Disallow means "allow everything" for this agent — record no rule.
                pass
        elif key == "allow":
            seen_rule_in_current = True
            current.allow.append((value, line_no))
        elif key == "crawl-delay":
            seen_rule_in_current = True
            try:
                current.crawl_delay = float(value)
            except ValueError:
                pass
        # Other directives (Sitemap handled by caller; Host, etc.) are ignored here.

    return blocks


def _rule_matches_root(rule: str) -> bool:
    """Does this robots.txt path rule match the root URL path `/`?

    RFC 9309 §2.2.2 gives path patterns two metacharacters: `*` matches any run of
    characters, and `$` at the end anchors the match to the end of the path. Everything
    else is a literal prefix match.

    Added by D-031 (2026-09-10). The previous test was `"/".startswith(rule)`, pure prefix
    matching with no metacharacter handling, which got `Allow: /$` exactly backwards:
    `"/".startswith("/$")` is False, so the rule that *explicitly permits the root URL and
    nothing else* was not even collected as a candidate. bookshop.org uses precisely that
    construct to open its root to seven named AI-retrieval agents before falling back to
    `Disallow: /` for everything deeper -- and CHK-D-001, a `critical`-severity check,
    reported the site as blocking retrieval crawlers at root.
    """
    if rule == "":
        return True
    anchored = rule.endswith("$")
    pattern = rule[:-1] if anchored else rule
    if "*" in pattern:
        regex = "".join(".*" if ch == "*" else re.escape(ch) for ch in pattern)
        regex = f"^{regex}$" if anchored else f"^{regex}"
        return re.match(regex, "/") is not None
    return pattern == "/" if anchored else "/".startswith(pattern)


def _root_allowed(block: _Block) -> tuple[bool, list[str], int | None]:
    """Is `/` allowed for this block? Longest-matching-rule wins per the de-facto standard;
    ties prefer Allow. Returns (allowed, disallow_rules_matching_root, matched_line)."""
    candidates: list[tuple[int, bool, str, int]] = []  # (rule_len, is_allow, rule, line_no)
    for rule, line_no in block.disallow:
        if _rule_matches_root(rule):
            candidates.append((len(rule), False, rule, line_no))
    for rule, line_no in block.allow:
        if _rule_matches_root(rule):
            candidates.append((len(rule), True, rule, line_no))

    if not candidates:
        return True, [], None

    candidates.sort(key=lambda c: c[0])
    best_len = candidates[-1][0]
    best = [c for c in candidates if c[0] == best_len]
    # Tie at the same specificity: Allow wins (more permissive reading).
    winner = max(best, key=lambda c: c[1])
    _, is_allow, rule, line_no = winner
    disallow_rules = [c[2] for c in candidates if not c[1]]
    # matched_line exists only to supply CHK-D-001's "Disallow: {rule}" evidence quote
    # (docs/BUNDLE-SCHEMA.md's own example leaves it null for an Allow-decided outcome) —
    # it is never populated when an Allow rule, or no rule at all, decided the result.
    matched_line = line_no if not is_allow else None
    return is_allow, disallow_rules, matched_line


def parse_robots_txt(text: str) -> dict:
    """Parse robots.txt body into the bundle's `robots.agents` + `sitemap_declarations`.

    Does not set `status`/`fetch_status`/`reason` — the caller (build_bundle) sets those
    from the actual HTTP response, since a 404/410 is a valid "everything permitted"
    reading that never calls this parser at all (see procedure.md §2).
    """
    blocks = _parse_blocks(text)

    # Specific agents override '*' for that agent (procedure.md / ai-crawler-agents.md
    # rule 1). Build the merged per-agent view: every named agent across all blocks, plus
    # the wildcard block if present, each resolved independently.
    agents: dict[str, dict] = {}
    wildcard_block: _Block | None = None

    for block in blocks:
        for agent in block.agents:
            if agent.strip() == "*":
                wildcard_block = block
            else:
                allowed_root, disallow_rules, matched_line = _root_allowed(block)
                agents[agent] = {
                    "class": classify_agent(agent),
                    "role": agent_role(agent),
                    "allowed_root": allowed_root,
                    "disallow_rules": disallow_rules,
                    "matched_line": matched_line,
                    "crawl_delay": block.crawl_delay,
                }

    if wildcard_block is not None:
        allowed_root, disallow_rules, matched_line = _root_allowed(wildcard_block)
        agents["*"] = {
            "class": "generic",
            "role": agent_role("*"),
            "allowed_root": allowed_root,
            "disallow_rules": disallow_rules,
            "matched_line": matched_line,
            "crawl_delay": wildcard_block.crawl_delay,
        }

    sitemap_declarations = []
    for line in text.splitlines():
        clean = line.split("#", 1)[0].strip()
        if clean.lower().startswith("sitemap:"):
            sitemap_declarations.append(clean.split(":", 1)[1].strip())

    return {
        "agents": agents,
        "sitemap_declarations": sitemap_declarations,
    }


def build_robots_section(fetch_status: int | None, body: str | None) -> dict:
    """Build the full `robots` bundle section from a raw fetch result.

    `fetch_status=None` means the request itself failed (timeout, connection error,
    challenge page) — collection stops per procedure.md §2.
    """
    if fetch_status is None:
        return {"status": "unavailable", "reason": "robots_fetch_failed", "fetch_status": None,
                "body": None, "parse_ok": False, "agents": {}, "sitemap_declarations": []}

    if fetch_status in (404, 410):
        return {"status": "ok", "reason": None, "fetch_status": fetch_status, "body": "",
                "parse_ok": True, "agents": {}, "sitemap_declarations": []}

    if fetch_status >= 500 or fetch_status == 429:
        return {"status": "unavailable", "reason": f"robots_fetch_status_{fetch_status}",
                "fetch_status": fetch_status, "body": body, "parse_ok": False, "agents": {},
                "sitemap_declarations": []}

    if fetch_status != 200:
        # Any other non-200 (e.g. a redirect the fetcher didn't follow, an auth wall):
        # cannot establish rules safely.
        return {"status": "unavailable", "reason": f"robots_fetch_status_{fetch_status}",
                "fetch_status": fetch_status, "body": body, "parse_ok": False, "agents": {},
                "sitemap_declarations": []}

    parsed = parse_robots_txt(body or "")
    return {
        "status": "ok",
        "reason": None,
        "fetch_status": fetch_status,
        "body": body,
        "parse_ok": True,
        "agents": parsed["agents"],
        "sitemap_declarations": parsed["sitemap_declarations"],
    }
