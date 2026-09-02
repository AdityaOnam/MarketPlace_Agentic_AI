---
name: site-evidence-collector
description: Collect a complete, read-only observational record of a website — robots.txt and per-agent crawler rules, a sampled page inventory with extracted main text and structured data, one shared headless render pass per sampled page, bounded internal-link and off-site identity-anchor reachability checks — and emit it as a single evidence bundle. Use when an audit needs the site's observable state gathered once, politely and within a fixed time budget, before any analysis happens. This skill observes and never judges: it emits no findings, no severities, and no recommendations.
license: Apache-2.0
allowed-tools:
  - http_fetch      # GET/HEAD only; no other method is ever issued
  - headless_browser # navigate, resize, read DOM/computed styles/geometry; no interaction
---

# Site Evidence Collector

The only skill in this marketplace permitted to make a network request. Every other skill
is a pure function from the bundle this produces to its findings. That boundary is what
makes the runtime budget and the read-only guarantee enforceable rather than promised.

## When to use

Invoked by `audit-orchestrator` as the first stage of an audit, given a URL or domain. Also
usable standalone to capture a reproducible site snapshot for evaluation fixtures — the
bundle format is identical either way, so analysers cannot tell live collection from replay.

## Inputs

| Input | Required | Default |
| --- | --- | --- |
| `target` | yes | — a URL or bare domain |
| `budget_s` | no | `300` — hard ceiling for the whole collection |
| `max_static_pages` | no | `20` |
| `max_rendered_pages` | no | `3` |

## Output

One evidence bundle conforming to `references/bundle-schema.md` (sections: `site`,
`robots`, `discovery`, `pages`, `rendered`, `links`, `anchors`, `budget`). No findings.

## Procedure

Deterministic. Given the same target and the same site state, the same bundle — including
the same page selection, which is seeded from a hash of the sorted inventory, never from
wall-clock or random state.

1. **Resolve the target.** Normalize to an origin, follow up to 3 redirects, record the
   chain, TLS validity, and final canonical host into `site`.
2. **Fetch and parse `robots.txt` before anything else.** Classify every declared agent as
   `retrieval`, `training`, `hybrid`, or `generic` using
   `references/ai-crawler-agents.md`. Record per-agent rules, the matched line number, and
   any `crawl-delay`. **Every subsequent request in this procedure obeys these rules.**
3. **Discover pages.** Read declared sitemaps; otherwise follow same-origin links from the
   homepage, breadth-first. Label each URL's `page_type` and the site's `archetype`.
4. **Sample and fetch statically** (≤ `max_static_pages`, ≤ 20). Stratify the sample across
   `page_type` so per-page-type scoring is possible downstream. For each page extract main
   text with boilerplate removed, headings, landmarks, structured data, links, images,
   iframes, media elements, form controls, dates, contact signals, and a trigram hash.
5. **Run the shared render pass** (≤ `max_rendered_pages`, ≤ 3). **One navigation per page.**
   Measure the mobile 375 px viewport on every rendered page and the desktop 1280 px
   viewport on the homepage only, by resizing the already-loaded page — never by
   re-navigating. Capture rendered DOM, main text, tap-target and overlay geometry,
   ad-region candidates with the detector that fired, and contrast pairs.
6. **Check internal links** — HEAD, ≤ 20, skipping fragments, `mailto:`, and anything
   `robots.txt` disallows. Record skips with their reason.
7. **Check off-site identity anchors** — HEAD, ≤ 8, one request per host, on URLs the site
   itself declares via `sameAs` or footer profile links. **401, 403 and 429 mean
   bot-blocked, not broken:** record `resolved: null`, never `false`.
8. **Emit the bundle** with per-stage timings in `budget`.

Full step detail, extraction rules, and classification tables:
[`references/procedure.md`](references/procedure.md).

## Time budget

| Stage | Budget |
| --- | --- |
| robots + discovery | 15 s |
| static fetches | 45 s |
| shared render pass | 75 s |
| internal links | 25 s |
| off-site anchors | 20 s |
| reserve | 80 s |

**Degradation rule.** When a stage exhausts its budget it is abandoned, its bundle section
is marked `partial` or `unavailable` with a reason, and collection continues. Never extend a
stage by borrowing from another. A bundle that says what it could not collect is worth more
than one that guessed — analysers are required to emit `not_determinable` for any evidence
that is not `ok`.

## Safety rules

These are not advisory. A collection that violates any of them is a failed collection.

- **Read-only.** `GET` and `HEAD` only. Never `POST`, `PUT`, `PATCH` or `DELETE`.
- **Never submit a form, click a control, or execute a user interaction** in the headless
  browser. Navigate, resize, and read — nothing else.
- **Never authenticate.** No credentials, no cookies carried from anywhere, no login pages
  followed, no paywall circumvention.
- **Obey `robots.txt`**, including `crawl-delay`. A disallowed path is not fetched, and is
  recorded as skipped with that reason.
- **Rate limit** to at most 2 concurrent requests per host with a minimum 250 ms gap, or the
  declared `crawl-delay` if longer.
- **Never evade bot detection.** Do not spoof a browser to defeat a challenge, do not retry
  around a 403, do not rotate identity. A blocked resource is evidence, not an obstacle.
- **Identify honestly** via a descriptive User-Agent naming the audit and a contact URL.
- **Off-site requests are HEAD-only, capped at 8, one per host**, and only to URLs the site
  itself declared.

## Failure modes this skill must handle without crashing

Robots-blocked root, JS-only single-page app, single-page site, very large site, non-Latin
script, paywall, parked domain, cloaking or differential serving, bot-challenge pages, slow
origin, and redirect loops. Each produces a valid bundle with the affected sections marked
`partial` or `unavailable` — never an exception, and never an inferred value.
