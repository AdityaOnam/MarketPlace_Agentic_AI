#!/usr/bin/env python3
"""
On-site engagement checks (EN-01 .. EN-10).
Read-only, robots-respecting, stdlib only. Prints {"findings": [...]}.

Usage: python check_engagement.py --url example.com [--max-pages 8]
"""
import argparse
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import fetch_lib as F  # noqa: E402

CTA = re.compile(r"\b(get started|start|try|buy|book|contact|demo|sign ?up|"
                 r"subscribe|download|request|talk to|learn more|pricing)\b", re.I)
LEAF_ROUTES = re.compile(r"/(contact|privacy|terms|legal|thank-?you|cookies)", re.I)
DEIXIS_OPEN = re.compile(r"^(we|our|this|it|they)\b", re.I)


def finding(cid, title, sev, evidence, action, prio, mechanism="", steps=None,
            effort="low", conf="high", urls=None):
    return {"check_id": cid, "category": "engagement", "title": title,
            "severity": sev, "confidence": conf, "evidence": evidence,
            "affected_urls": (urls or [])[:5],
            "suggested_action": {"summary": action, "priority": prio,
                                 "mechanism": mechanism, "steps": steps or [],
                                 "effort": effort}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--max-pages", type=int, default=F.MAX_PAGES)
    args = ap.parse_args()

    base, host = F.normalise(args.url)
    pages, _robots = F.crawl(base, args.max_pages)
    ok = [(u, r) for u, r in pages if r.get("ok")]
    if not ok:
        F.emit([])
        return

    n = len(ok)
    no_h1, no_cta, dead_end, no_crumb, deixis = [], [], [], [], []
    img_total = img_no_alt = 0
    internal = set()

    for url, r in ok:
        p = F.parse_html(r["html"])
        body = " ".join(p.text_chunks)
        opening = " ".join(body.split()[:100])

        if not p.h1s or not any(len(h.split()) >= 3 for h in p.h1s):
            no_h1.append(url)

        if not CTA.search(body[:4000]):
            no_cta.append(url)

        # in-content internal links (crude proxy: same-host, non-nav-duplicated)
        outbound = set()
        for href in p.links:
            full = urllib.parse.urljoin(url, href).split("#")[0]
            pu = urllib.parse.urlparse(full)
            if pu.netloc == host and full.rstrip("/") != url.rstrip("/"):
                outbound.add(full)
                internal.add(full)
        if len(outbound) < 3 and not LEAF_ROUTES.search(url):
            dead_end.append(url)

        depth = len([s for s in urllib.parse.urlparse(url).path.split("/") if s])
        if depth >= 2 and not p.has_breadcrumb and "breadcrumb" not in r["html"].lower():
            no_crumb.append(url)

        # brand name absent from opening + headings -> chunk is unattributable
        brand = host.split(".")[0].lower()
        heading_text = " ".join(h for _, h in p.headings).lower()
        if DEIXIS_OPEN.match(opening.strip()) and brand not in opening.lower() \
                and brand not in heading_text:
            deixis.append(url)

        img_total += p.img_total
        img_no_alt += p.img_no_alt

    out = []
    if len(no_h1) >= n * 0.5:
        out.append(finding(
            "EN-01", "Pages lack a descriptive main heading", "high",
            f"{len(no_h1)}/{n} sampled pages have no <h1> or only a generic one "
            f"(e.g. {no_h1[0]}).",
            "Give every page one descriptive H1 naming the page subject and the brand.",
            "high",
            mechanism="The H1 is the first orientation cue for a reader and the title a "
                      "retrieval chunk attaches to. Without it, a deep-landing visitor "
                      "cannot tell where they are and an extracted chunk is untitled.",
            steps=['Use "<Subject> - <Brand>" rather than "Welcome".',
                   "Exactly one H1 per page; nest sections under H2/H3."],
            urls=no_h1))

    if len(no_cta) >= n * 0.5:
        out.append(finding(
            "EN-03", "Most pages offer no next step", "medium",
            f"{len(no_cta)}/{n} sampled pages contain no action link or button in the "
            "main content.",
            "Add one primary call to action per page, matched to that page's intent.",
            "medium",
            mechanism="Visitors referred by an AI answer land mid-funnel with no journey "
                      "behind them. A page with no next step ends the session.",
            steps=["One primary action visible without scrolling.",
                   "Add a lower-commitment secondary option (docs, pricing)."],
            urls=no_cta))

    if len(dead_end) >= max(2, n * 0.4):
        out.append(finding(
            "EN-04", "Pages are dead ends with almost no internal links", "medium",
            f"{len(dead_end)}/{n} sampled pages link to fewer than 3 other pages on the "
            f"site (e.g. {dead_end[0]}).",
            "Add 2-4 contextual in-content links per page with descriptive anchor text.",
            "medium",
            mechanism="Deep arrivals explore laterally, not through a nav they never saw. "
                      "In-content links are also how topical relevance flows between pages.",
            urls=dead_end))

    if no_crumb:
        out.append(finding(
            "EN-05", "Deep pages give no sense of where the visitor is", "medium",
            f"{len(no_crumb)}/{n} sampled pages sit 2+ levels deep with no breadcrumb "
            f"element or BreadcrumbList markup (e.g. {no_crumb[0]}).",
            "Render breadcrumbs on every page below the top level and mark them up as "
            "BreadcrumbList.",
            "medium",
            mechanism="Breadcrumbs answer 'where am I and what is this part of' - the "
                      "exact question a context-free arrival has.",
            urls=no_crumb))

    if deixis:
        out.append(finding(
            "EN-08", "Pages assume the visitor already knows who you are", "medium",
            f"{len(deixis)}/{n} sampled pages open with 'we/our/this' and never name the "
            f"brand or product in the first 100 words or in any heading (e.g. {deixis[0]}).",
            "Name the entity explicitly at least once per page and per major section.",
            "medium",
            mechanism="Retrieval returns chunks, not sites. A chunk lifted from mid-page "
                      "loses the header, so if the subject only lives in the nav the "
                      "chunk is unattributable and gets dropped.",
            steps=["Write \"Acme's deployment pipeline\", not \"our pipeline\".",
                   "Repeat the entity name in section headings."],
            conf="medium", urls=deixis))

    if img_total >= 5 and img_no_alt > img_total * 0.5:
        out.append(finding(
            "EN-10", "Most images have no alt text", "low",
            f"{img_no_alt}/{img_total} images across {n} sampled pages have empty or "
            "missing alt attributes.",
            "Add descriptive alt text conveying each image's information.",
            "low",
            mechanism="Alt text is the only textual representation of an image for "
                      "assistive technology and for extraction; missing alt is content "
                      "that effectively does not exist.",
            urls=[u for u, _ in ok]))

    if len(internal) > 30 and not any(F.parse_html(r["html"]).has_search_input
                                      for _, r in ok):
        out.append(finding(
            "EN-09", "No site search on a large site", "low",
            f"{len(internal)} internal URLs discovered; no search input found on any of "
            f"the {n} sampled pages.",
            "Add site search reachable from every page.",
            "low",
            mechanism="Past roughly 30 pages, browsing stops scaling; a visitor who "
                      "cannot find the one page they need leaves.",
            conf="medium"))

    F.emit(out)


if __name__ == "__main__":
    main()
