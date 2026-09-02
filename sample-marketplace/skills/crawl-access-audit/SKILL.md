---
name: crawl-access-audit
description: >-
  Checks whether an automated reader can reach a website and read its content
  at all - robots.txt policy and AI-crawler blocks, HTTP status and redirect
  health, sitemap presence and accuracy, canonical correctness, and whether the
  page's substance exists in the raw HTML response or only appears after
  JavaScript runs. Use as the first layer of an AI-discoverability audit, since
  every deeper check is meaningless when the crawler is blocked or sees an
  empty shell.
license: MIT
allowed-tools:
  - Bash
  - Read
---

# Crawl & Access Audit (Layer 0-1)

Answers one question: **can a machine reach this page, and does it see what a
human sees?** Everything else in the marketplace depends on this passing.

## When to use

Called by `audit-orchestrator` as check 1. Can also be run alone to triage
"our site vanished from AI answers".

## Inputs

- `url` — target site (required)
- `max_pages` — page budget, default `8`

## Safety

`GET` only. Honours `robots.txt` — a disallowed path is *never fetched*, only
reported. 0.4 s minimum between requests. No auth, no forms, no writes.

## Procedure

1. Fetch `robots.txt`. Record status and full text.
2. Crawl the homepage plus up to `max_pages - 1` same-domain internal links
   (robots-filtered, rate-limited).
3. Probe `sitemap.xml` and any `Sitemap:` directives in `robots.txt`.
4. Run each check in `references/checks.md` against the fetched set.
5. Emit findings as JSON on stdout: `{"findings": [...]}`.

Run: `python scripts/check_crawl_access.py --url <url> --max-pages <n>`

## Checks (summary — full logic in `references/checks.md`)

| ID | Fires when | Base severity |
|---|---|---|
| `CR-01` | `robots.txt` disallows `/` for `*` | critical |
| `CR-02` | Named AI crawlers (GPTBot, ClaudeBot, PerplexityBot, …) disallowed | high |
| `CR-03` | Homepage or sampled pages return non-200 | critical / high |
| `CR-04` | Raw HTML has < 150 words while the page is script-heavy — JS-render dependency | high |
| `CR-05` | No `sitemap.xml` and none declared in `robots.txt` | medium |
| `CR-06` | Missing or cross-host `rel=canonical` | medium |
| `CR-07` | Missing `<title>` or `<meta name="description">` | medium |
| `CR-08` | Chains of ≥ 2 redirects, or http→https not enforced | low |
| `CR-09` | `noindex` on content pages | critical |
| `CR-10` | Missing `<html lang>` | low |

## False-positive guards

- `Disallow: /admin`, `/cart`, `/search`, `/api` is **correct** — not a finding.
  Only flag disallows covering content routes.
- Do not fire `CR-04` on a page that is genuinely short by design (a contact
  page). Require the script-heavy signal *and* a low word count *and* at least
  3 pages showing the pattern before claiming it is sitewide.
- `CR-09` on a staging/preview host is expected — note it rather than escalate.

## Output

`{"findings": [...]}` — each finding carries `check_id`, `category:
"discoverability"`, `title`, `severity`, `confidence`, `evidence`,
`affected_urls`, `suggested_action`. The orchestrator merges, renumbers and
ranks; this skill does not assign final IDs.

## References

- `references/checks.md` — exact thresholds, evidence templates, and the
  remediation text for every check.
