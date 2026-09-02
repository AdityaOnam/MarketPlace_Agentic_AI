#!/usr/bin/env python3
"""
Crawl & access checks (CR-01 .. CR-10).

Read-only. Respects robots.txt. stdlib only.
Prints {"findings": [...]} on stdout.

Usage:
    python check_crawl_access.py --url example.com [--max-pages 8]
"""
import argparse
import os
import re
import sys

# Resolve the shared library from the marketplace root (../../../lib).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import fetch_lib as F  # noqa: E402

AI_CRAWLERS = [
    "gptbot", "oai-searchbot", "chatgpt-user", "claudebot", "claude-web",
    "anthropic-ai", "perplexitybot", "google-extended", "ccbot",
    "applebot-extended", "bytespider", "amazonbot", "meta-externalagent",
]

# Disallow paths that are legitimate to block - never flag these.
BENIGN_DISALLOW = re.compile(
    r"^/(admin|wp-admin|cart|checkout|account|login|signin|api|search|"
    r"cgi-bin|tmp|private|internal|\?|\*)", re.I)

SPA_ROOTS = re.compile(r'<div[^>]+id=["\'](root|__next|app|__nuxt)["\']', re.I)


def finding(check_id, title, severity, evidence, action, priority,
            mechanism="", steps=None, effort="medium", confidence="high", urls=None):
    return {
        "check_id": check_id,
        "category": "discoverability",
        "title": title,
        "severity": severity,
        "confidence": confidence,
        "evidence": evidence,
        "affected_urls": (urls or [])[:5],
        "suggested_action": {
            "summary": action,
            "priority": priority,
            "mechanism": mechanism,
            "steps": steps or [],
            "effort": effort,
        },
    }


def parse_robots_groups(text):
    """-> {user_agent_lower: [disallow paths]} ; tolerant of messy files."""
    groups, current = {}, []
    for raw in text.splitlines():
        line = raw.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "user-agent":
            current = [val.lower()]
            groups.setdefault(val.lower(), [])
        elif key == "disallow" and current:
            for ua in current:
                groups.setdefault(ua, []).append(val)
    return groups


def check_robots(robots, findings):
    text, status = robots["text"], robots["status"]
    if status != 200 or not text.strip():
        return  # absent robots.txt means "allow all" - not a defect
    groups = parse_robots_groups(text)

    # CR-01: blanket block for everyone
    if any(d == "/" for d in groups.get("*", [])):
        findings.append(finding(
            "CR-01", "robots.txt blocks all crawlers from the entire site", "critical",
            f'{robots["url"]} (HTTP 200) contains "User-agent: *" with "Disallow: /". '
            "Every content path is disallowed for general crawlers.",
            "Replace the site-wide Disallow: / with targeted rules that block only "
            "private routes.",
            "critical",
            mechanism="Reach is the first of three steps (reach -> read -> extract). "
                      "A blanket disallow fails step one, so no retrieval system can "
                      "index or cite any page.",
            steps=[
                'Remove "Disallow: /" from the User-agent: * group.',
                'Disallow only private routes: /admin, /cart, /checkout, /api, /search.',
                'Add a "Sitemap:" line pointing at the full sitemap.',
                "Re-fetch robots.txt and confirm a content URL is now allowed.",
            ],
            effort="low", urls=[robots["url"]]))

    # CR-02: AI fetchers specifically excluded
    blocked = [ua for ua in groups
               if ua in AI_CRAWLERS and any(d == "/" for d in groups[ua])]
    if blocked:
        findings.append(finding(
            "CR-02", "AI assistant crawlers are blocked from the site", "high",
            f"robots.txt blocks {len(blocked)} AI crawler(s) with Disallow: / — "
            + ", ".join(sorted(blocked)) + ".",
            "Decide the AI-crawler policy deliberately: allow retrieval agents if the "
            "brand should be citable; block only training crawlers if not.",
            "high",
            mechanism="Retrieval agents are the fetchers that build cited answers. "
                      "Blocking them removes the brand from AI answers while classic "
                      "search keeps working, so the loss is invisible in analytics.",
            steps=[
                "To be citable: allow OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot.",
                "To opt out of training only: keep GPTBot, CCBot, Google-Extended, "
                "Applebot-Extended disallowed.",
                "Document the chosen policy so it is not reverted by a template update.",
            ],
            effort="low", urls=[robots["url"]]))

    # Report over-broad content blocks (excluding benign admin paths)
    broad = [d for d in groups.get("*", [])
             if d and d != "/" and not BENIGN_DISALLOW.match(d) and d.count("/") <= 2]
    if broad:
        findings.append(finding(
            "CR-01b", "robots.txt disallows content sections", "medium",
            "User-agent: * disallows content paths: " + ", ".join(broad[:6]) + ".",
            "Review these disallows and re-open any that contain public content.",
            "medium",
            mechanism="Disallowed sections are never fetched, so their facts cannot "
                      "enter an index no matter how good the content is.",
            effort="low", confidence="medium", urls=[robots["url"]]))


def check_pages(pages, findings):
    ok = [(u, r) for u, r in pages if r.get("ok")]
    bad = [(u, r) for u, r in pages if not r.get("ok")]
    home_url, home = pages[0]

    # CR-03: reachability
    if not home.get("ok"):
        findings.append(finding(
            "CR-03", "Homepage is unreachable to an automated reader", "critical",
            f'{home_url} returned {home.get("status") or "no response"} '
            f'({home.get("error", "")}).'.strip(),
            "Restore the homepage for non-browser user agents and confirm it returns 200.",
            "critical",
            mechanism="If the entry point cannot be fetched, nothing downstream is "
                      "discoverable. Common causes are bot-filtering WAF rules or "
                      "user-agent gating that also blocks legitimate retrieval agents.",
            steps=[
                "Test with a plain GET and a non-browser User-Agent.",
                "Check WAF/CDN bot rules for over-broad blocking of unknown agents.",
                "Allow-list documented retrieval agents by UA and reverse-DNS.",
            ],
            effort="medium", urls=[home_url]))
        return ok
    if len(bad) >= max(2, len(pages) // 4):
        findings.append(finding(
            "CR-03", "Several internal pages return errors", "high",
            f"{len(bad)}/{len(pages)} sampled URLs returned non-200: "
            + ", ".join(f'{u} -> {r.get("status")}' for u, r in bad[:5]) + ".",
            "Fix or 301-redirect the broken routes and update internal links that point at them.",
            "high",
            mechanism="Broken pages waste crawl budget and can drop already-indexed "
                      "URLs; links pointing at them leak authority into dead ends.",
            effort="medium", urls=[u for u, _ in bad]))

    # CR-04: JS-render dependency
    js_only = []
    for url, r in ok:
        p = F.parse_html(r["html"])
        wc = p.word_count()
        html_len = max(len(r["html"]), 1)
        ratio = sum(len(c) for c in p.text_chunks) / html_len
        if wc < 150 and (p.script_count >= 5 or SPA_ROOTS.search(r["html"])) and ratio < 0.05:
            js_only.append((url, wc, p.script_count))
    if len(js_only) >= 3:
        sample = "; ".join(f"{u} -> {w} words, {s} scripts" for u, w, s in js_only[:3])
        findings.append(finding(
            "CR-04", "Page content only exists after JavaScript runs", "high",
            f"{len(js_only)}/{len(ok)} sampled pages return under 150 words of text in "
            f"the raw HTML response while loading 5+ scripts. {sample}.",
            "Server-render or pre-render every indexable route so the main copy, headings "
            "and key facts are present in the initial HTML response.",
            "high",
            mechanism="Many retrieval fetchers do not execute JavaScript. Whatever is in "
                      "the raw response is the entire page as far as they are concerned, "
                      "so content plainly visible in a browser is invisible to them.",
            steps=[
                "Enable SSR or static generation for content routes.",
                "Confirm headings, body copy and key facts appear in view-source.",
                "Keep <title>, meta description and JSON-LD server-rendered too.",
                "Verify with: curl -s <url> | wc -w",
            ],
            effort="high", confidence="high" if len(js_only) >= 3 else "medium",
            urls=[u for u, _, _ in js_only]))

    # CR-09: noindex on content
    noindexed = []
    for url, r in ok:
        p = F.parse_html(r["html"])
        meta_robots = (p.meta.get("robots", "") or "").lower()
        hdr = (r.get("headers", {}).get("x-robots-tag", "") or "").lower()
        if "noindex" in meta_robots or "noindex" in hdr:
            noindexed.append(url)
    if noindexed:
        findings.append(finding(
            "CR-09", "Content pages are marked noindex", "critical",
            f"{len(noindexed)}/{len(ok)} sampled pages carry a noindex directive despite "
            f"returning 200: " + ", ".join(noindexed[:4]) + ".",
            "Remove noindex from public content routes; keep it only on staging, "
            "thank-you and internal-search pages.",
            "critical",
            mechanism="The page fetches and renders normally but is explicitly excluded "
                      "from indexes - the failure mode hardest to spot from the outside.",
            effort="low", urls=noindexed))

    # CR-06 / CR-07 / CR-10: per-page metadata hygiene
    no_canon, no_title, no_desc, no_lang, titles = [], [], [], [], {}
    for url, r in ok:
        p = F.parse_html(r["html"])
        if not p.canonical:
            no_canon.append(url)
        t = (p.title or "").strip()
        if not t:
            no_title.append(url)
        else:
            titles.setdefault(t, []).append(url)
        if not (p.meta.get("description") or "").strip():
            no_desc.append(url)
        if not p.lang:
            no_lang.append(url)

    n = len(ok)
    if n and len(no_canon) >= n * 0.5:
        findings.append(finding(
            "CR-06", "Most pages have no canonical URL", "medium",
            f"{len(no_canon)}/{n} sampled pages have no <link rel=\"canonical\">.",
            "Emit a self-referential absolute canonical on every page.",
            "medium",
            mechanism="Without a canonical, URL variants (tracking params, www vs "
                      "non-www, trailing slash) are treated as separate pages, splitting "
                      "the signals that decide which one gets cited.",
            effort="low", urls=no_canon))

    dupes = {t: u for t, u in titles.items() if len(u) >= 3}
    if len(no_title) or len(no_desc) >= n * 0.3 or dupes:
        bits = []
        if no_title:
            bits.append(f"{len(no_title)}/{n} pages have an empty <title>")
        if dupes:
            t, urls = next(iter(dupes.items()))
            bits.append(f'{len(urls)} pages share the identical title "{t}"')
        if len(no_desc) >= n * 0.3:
            bits.append(f"{len(no_desc)}/{n} pages have no meta description")
        findings.append(finding(
            "CR-07", "Page titles and descriptions are missing or duplicated", "medium",
            "; ".join(bits) + ".",
            "Give every page a unique, specific title containing the brand name, and a "
            "1-2 sentence description stating that page's actual claim.",
            "medium",
            mechanism="Title and description are the highest-confidence one-line summary "
                      "a machine has for what a page is about, and are what gets shown "
                      "when the page is surfaced.",
            steps=[
                "Pattern: <Specific page subject> | <Brand>.",
                "Never reuse one title across templates.",
                "Description states the claim, not a slogan.",
            ],
            effort="low", urls=(no_title or no_desc or list(dupes.values())[0])))

    if n and len(no_lang) == n:
        findings.append(finding(
            "CR-10", "No language declared on the page", "low",
            f"<html> has no lang attribute on {n}/{n} sampled pages.",
            "Add an accurate BCP-47 lang attribute to <html>; add hreflang if locales exist.",
            "low",
            mechanism="Language declaration routes content to the right audience and "
                      "affects locale-scoped retrieval and accessibility tooling.",
            effort="low", urls=no_lang))
    return ok


def check_sitemap(base, robots, findings):
    declared = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots["text"] or "")
    probe = F.fetch(base.rstrip("/") + "/sitemap.xml")
    if not declared and probe.get("status") != 200:
        findings.append(finding(
            "CR-05", "No sitemap is published", "medium",
            f'{base.rstrip("/")}/sitemap.xml returned '
            f'{probe.get("status") or "no response"} and robots.txt declares no '
            "Sitemap: directive.",
            "Publish sitemap.xml with accurate <lastmod> values and declare it in robots.txt.",
            "medium",
            mechanism="Without a sitemap, discovery relies entirely on link-following, so "
                      "pages more than a couple of hops from the homepage may never be "
                      "found. lastmod also supplies the freshness signal used to break "
                      "ties between competing sources.",
            steps=[
                "Generate sitemap.xml during the build, listing every canonical URL.",
                "Set <lastmod> from real content-change timestamps, not build time.",
                'Add "Sitemap: https://<host>/sitemap.xml" to robots.txt.',
            ],
            effort="low"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--max-pages", type=int, default=F.MAX_PAGES)
    args = ap.parse_args()

    base, _host = F.normalise(args.url)
    pages, robots = F.crawl(base, args.max_pages)

    findings = []
    check_robots(robots, findings)
    check_pages(pages, findings)
    check_sitemap(base, robots, findings)
    F.emit(findings)


if __name__ == "__main__":
    main()
