#!/usr/bin/env python3
"""
Off-site discoverability: can a crawler even get in and read the page?
Usage: python3 check_crawlability.py <https://example.com>
Prints JSON: {"findings": [...]} — each finding lacks "id" (orchestrator assigns it).
"""
import sys
import urllib.parse
from fetch_lib import fetch, get_robots, parse_html, emit, discover_pages

AI_BOTS = [
    "GPTBot", "ChatGPT-User", "OAI-SearchBot",  # OpenAI
    "ClaudeBot", "anthropic-ai", "Claude-Web",  # Anthropic
    "PerplexityBot", "Perplexity-User",
    "Google-Extended",
    "CCBot",  # Common Crawl (feeds many LLM training/RAG pipelines)
    "Bytespider",
    "Amazonbot",
]


def normalize(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")


def main():
    if len(sys.argv) < 2:
        print(json_error("usage: check_crawlability.py <url>"))
        sys.exit(1)
    base_url = normalize(sys.argv[1])
    findings = []

    # 1. robots.txt
    rp, robots_txt, robots_url, robots_status = get_robots(base_url)
    if not robots_txt.strip():
        findings.append({
            "title": "No robots.txt found",
            "category": "discoverability",
            "severity": "low",
            "evidence": f"GET {robots_url} returned status {robots_status} with an empty/missing body.",
            "suggested_action": {
                "summary": "Publish a robots.txt at the domain root that explicitly allows crawling of public "
                            "content and points to the sitemap (Sitemap: https://.../sitemap.xml). Without one, "
                            "crawlers fall back to default behavior, which is inconsistent across bots.",
                "priority": "low",
            },
        })
    else:
        parsed_base = urllib.parse.urlparse(base_url)
        home_disallowed = not rp.can_fetch("*", base_url)
        if home_disallowed:
            findings.append({
                "title": "robots.txt blocks the homepage for general crawlers",
                "category": "discoverability",
                "severity": "critical",
                "evidence": f"robots.txt at {robots_url} disallows '*' from fetching {base_url}. "
                             f"A page blocked at the root cannot be discovered by any crawler-based system, "
                             f"regardless of content quality.",
                "suggested_action": {
                    "summary": "Remove the Disallow rule blocking the homepage (and any other public marketing/"
                                "content paths) for User-agent: *.",
                    "priority": "critical",
                },
            })
        blocked_ai_bots = [ua for ua in AI_BOTS if not rp.can_fetch(ua, base_url)]
        # only meaningful if general '*' access IS allowed but specific AI bots are singled out
        if blocked_ai_bots and not home_disallowed:
            findings.append({
                "title": "robots.txt specifically blocks known AI-assistant crawlers",
                "category": "discoverability",
                "severity": "high",
                "evidence": f"robots.txt at {robots_url} allows general crawling but explicitly disallows: "
                             f"{', '.join(blocked_ai_bots)}. These user-agents are used by AI assistants/answer "
                             f"engines (OpenAI, Anthropic, Perplexity, Common Crawl-derived corpora, etc.) to "
                             f"fetch and cite pages at answer time.",
                "suggested_action": {
                    "summary": "If the intent is to be discoverable and cited by AI assistants, remove the "
                                "Disallow rules for these user-agents on public content paths. If the block is "
                                "intentional (e.g. paywall/IP policy), treat this as an accepted trade-off rather "
                                "than a bug — but document the decision, since it directly suppresses AI citation.",
                    "priority": "high",
                },
            })
        if "sitemap:" not in robots_txt.lower():
            findings.append({
                "title": "robots.txt does not reference a sitemap",
                "category": "discoverability",
                "severity": "low",
                "evidence": f"No 'Sitemap:' directive found in {robots_url}.",
                "suggested_action": {
                    "summary": "Add 'Sitemap: https://<domain>/sitemap.xml' to robots.txt so crawlers can find "
                                "the full set of indexable URLs without relying on discovering internal links.",
                    "priority": "low",
                },
            })

    # 2. sitemap.xml reachability (direct check regardless of robots.txt mention)
    sitemap_url = f"{urllib.parse.urlparse(base_url).scheme}://{urllib.parse.urlparse(base_url).netloc}/sitemap.xml"
    sm = fetch(sitemap_url)
    if not sm.get("ok") or "<urlset" not in sm.get("html", "") and "<sitemapindex" not in sm.get("html", ""):
        findings.append({
            "title": "sitemap.xml missing or not valid XML sitemap",
            "category": "discoverability",
            "severity": "medium",
            "evidence": f"GET {sitemap_url} -> status {sm.get('status')}; body did not contain a <urlset> or "
                         f"<sitemapindex> root element.",
            "suggested_action": {
                "summary": "Publish a valid XML sitemap listing canonical URLs for all indexable pages, and keep "
                            "it current as pages are added/removed.",
                "priority": "medium",
            },
        })

    # 3. homepage fetch: status, https, redirects
    home = fetch(base_url)
    if not home.get("ok"):
        findings.append({
            "title": "Homepage did not return a successful response",
            "category": "discoverability",
            "severity": "critical",
            "evidence": f"GET {base_url} -> status {home.get('status')}, error: {home.get('error')}.",
            "suggested_action": {
                "summary": "Fix the underlying server/DNS/TLS issue so the homepage reliably returns HTTP 200. "
                            "A page that errors for a plain GET request errors for crawlers too.",
                "priority": "critical",
            },
        })
        emit(findings)
        return

    if home["url"].startswith("http://") and base_url.startswith("http://"):
        findings.append({
            "title": "Site is served over HTTP, not HTTPS",
            "category": "discoverability",
            "severity": "medium",
            "evidence": f"Final resolved URL {home['url']} uses http://, not https://.",
            "suggested_action": {
                "summary": "Serve the site over HTTPS with a valid certificate and redirect all HTTP traffic to "
                            "HTTPS. Lack of HTTPS is a trust signal search/AI ranking systems weigh negatively.",
                "priority": "medium",
            },
        })

    if home["url"].rstrip("/") != base_url.rstrip("/"):
        findings.append({
            "title": "Homepage redirects before serving content",
            "category": "discoverability",
            "severity": "low",
            "evidence": f"Requested {base_url}, final URL after redirects was {home['url']}.",
            "suggested_action": {
                "summary": "Confirm the redirect chain is a single, fast, permanent (301) hop to the canonical "
                            "URL. Long or looping redirect chains waste crawl budget and can cause a page to be "
                            "skipped.",
                "priority": "low",
            },
        })

    page = parse_html(home["html"])

    # 4. meta robots noindex on homepage
    robots_meta = page.meta.get("robots", "")
    if "noindex" in robots_meta.lower():
        findings.append({
            "title": "Homepage has a noindex meta directive",
            "category": "discoverability",
            "severity": "critical",
            "evidence": f"<meta name=\"robots\" content=\"{robots_meta}\"> found on the homepage.",
            "suggested_action": {
                "summary": "Remove the noindex directive from any public page that should be discoverable.",
                "priority": "critical",
            },
        })

    # 5. canonical sanity
    if not page.canonical:
        findings.append({
            "title": "Homepage has no canonical tag",
            "category": "discoverability",
            "severity": "low",
            "evidence": "No <link rel=\"canonical\"> found in the homepage <head>.",
            "suggested_action": {
                "summary": "Add a self-referencing canonical tag to every indexable page to avoid duplicate-"
                            "content ambiguity across URL variants (tracking params, trailing slash, http/https).",
                "priority": "low",
            },
        })
    else:
        canon_host = urllib.parse.urlparse(urllib.parse.urljoin(base_url, page.canonical)).netloc
        base_host = urllib.parse.urlparse(base_url).netloc
        if canon_host and canon_host != base_host:
            findings.append({
                "title": "Homepage canonical tag points to a different domain",
                "category": "discoverability",
                "severity": "high",
                "evidence": f"canonical={page.canonical!r} resolves to host {canon_host}, but the page was "
                             f"fetched from {base_host}.",
                "suggested_action": {
                    "summary": "Point the canonical tag at the correct self URL unless this domain is "
                                "intentionally a mirror/staging copy of another canonical domain.",
                    "priority": "high",
                },
            })

    # 6. lang attribute
    if not page.lang:
        findings.append({
            "title": "Missing html lang attribute",
            "category": "discoverability",
            "severity": "low",
            "evidence": "<html> tag has no lang attribute.",
            "suggested_action": {
                "summary": "Add lang=\"en\" (or the correct language code) to the <html> tag so language-aware "
                            "systems classify and route the content correctly.",
                "priority": "low",
            },
        })

    # 7. JS-render gap heuristic
    words = page.word_count()
    scripts = page.script_count
    body_len = len(home["html"])
    if words < 150 and scripts >= 3:
        findings.append({
            "title": "Homepage looks like a client-rendered shell with little content in the raw HTML",
            "category": "discoverability",
            "severity": "high",
            "evidence": f"Raw HTML fetched without executing JavaScript contains only ~{words} words of visible "
                         f"text alongside {scripts} <script> tags ({body_len} bytes total). Crawlers/answer "
                         f"engines that don't execute JavaScript (or use a lightweight fetch rather than a full "
                         f"headless browser) will see substantially less content than a human visitor does.",
            "suggested_action": {
                "summary": "Server-side render (SSR) or statically pre-render the primary content of key pages "
                            "(home, product/service, about, pricing) so the core facts are present in the initial "
                            "HTML response, not only assembled client-side after JS execution.",
                "priority": "high",
            },
        })

    emit(findings)


def json_error(msg):
    import json
    return json.dumps({"error": msg})


if __name__ == "__main__":
    main()
