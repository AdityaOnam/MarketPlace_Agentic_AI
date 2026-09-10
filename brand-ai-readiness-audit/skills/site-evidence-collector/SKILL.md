---
name: site-evidence-collector
description: Collect a complete, read-only observational record of a website — robots.txt and per-agent crawler rules, a sampled page inventory with extracted main text and structured data, one shared rendered-page pass per sampled page, bounded internal-link and off-site identity-anchor reachability checks — and emit it as a single in-memory evidence bundle. Use when an audit needs the site's observable state gathered once, politely and within a fixed time budget, before any analysis happens. This skill observes and never judges: it emits no findings, no severities, and no recommendations.
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
usable standalone to capture a reproducible site record for evaluation fixtures — the
bundle format is identical either way, so analysers cannot tell live collection from replay.

**The bundle is in-memory only.** It is built during a single audit, passed to the
analysers within that same run, and discarded when the run ends. This skill writes nothing
to disk, keeps no cache, and carries nothing between runs — there is no persistent store
anywhere in this marketplace, and no run can be influenced by a previous one. (An
evaluation harness may choose to serialise a bundle to disk as a fixture, but that is a
choice made outside the marketplace at evaluation time, not behaviour of this skill.)

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

## Executable checks

`scripts/` holds the deterministic parsing/extraction logic that turns already-fetched
raw content into bundle sections — it does not fetch or render anything itself; that is
the agent's `http_fetch`/`headless_browser` tool calls per the procedure below.
`robots_parser.py` (robots.txt parsing + classification), `html_tree.py` +
`extract_page.py` (the full `pages[]` extraction, on a stdlib-only HTML tree — no bundled
dependency), `page_classifier.py` (`page_type`/`archetype` labelling), `sampling.py`
(deterministic seeded page selection), `render_geometry.py` (WCAG contrast-ratio math,
overlay/tap-target/ad-region classification from already-measured geometry),
`link_check.py` / `anchor_check.py` (the two link-inventory sections, encoding the
401/403/429-is-not-broken rule structurally), and `build_bundle.py` (final assembly).

## Procedure

Given the same target and the same site state, this procedure is built to produce the same
bundle — including the same page selection, which is seeded from a hash of the sorted
inventory rather than from wall-clock or random state. **That is a design goal serving
reproducibility, not a requirement the audit imposes:** a live site can change between
runs, an origin can vary its responses, and a stage can be abandoned on one run and
complete on the next. Where that happens the bundle records it (`status`, `reason`,
`budget.stages[].abandoned`) instead of presenting one run's luck as a stable result.

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
5. **Run the shared rendered-page pass** (≤ `max_rendered_pages`, ≤ 3), **only if
   `headless_browser` is available this run.** If it is not — this marketplace's grading
   sandbox has none — skip the pass, emit `rendered: []`, and still record a `render_pass`
   entry in `budget.stages` marked `abandoned: true` with the reason. Recording the stage
   even at zero elapsed time is what lets `degraded_stages[]` in the final report name
   which checks lost evidence, instead of those checks silently vanishing. When the tool is
   available: **one navigation per page.** Measure the mobile 375 px viewport on every
   rendered page and the desktop 1280 px viewport on the homepage only, by resizing the
   already-loaded page — never by re-navigating. Capture rendered DOM, main text,
   tap-target and overlay geometry, ad-region candidates with the detector that fired, and
   contrast pairs.
6. **Check internal links** — HEAD, ≤ 20, skipping fragments, `mailto:`, and anything
   `robots.txt` disallows. Record skips with their reason.
7. **Check off-site identity anchors** — HEAD, ≤ 8, one request per host, on URLs the site
   itself declares via `sameAs` or footer profile links. **401, 403 and 429 mean
   bot-blocked, not broken:** record `resolved: null`, never `false`. **A 404, 405, 410 or
   501 from HEAD alone is not a failure either** — many servers mishandle HEAD, and one
   major social platform answers HEAD with 404 and GET with 200 for the same profile URL.
   Confirm with a single GET before recording `resolved: false`; without that confirmation
   the result is `resolved: null`. This is not retrying around a block: a 401/403/429 is
   never re-requested.
8. **Emit the bundle** with per-stage timings in `budget`.

Full step detail, extraction rules, and classification tables:
[`references/procedure.md`](references/procedure.md).

## Time budget

| Stage | Budget |
| --- | --- |
| robots + discovery | 15 s |
| static fetches | 45 s |
| shared rendered-page pass | 75 s |
| internal links | 25 s |
| off-site anchors | 20 s |
| reserve | 80 s |

**What the budget does and does not cover.** These are wall-clock ceilings on each stage,
and they bound how long this skill will *wait* — they are not a claim about how fast the
audited site responds. **Time spent waiting on an external origin is outside our control
and is not excluded from the clock; it is capped by it.** A slow origin, a long redirect
chain, or a rate-limited host does not make the audit overrun — it makes the affected
stage hit its ceiling and be abandoned, producing a partial bundle rather than a late one.
The `<5 minute` figure is therefore a guarantee about the audit's own behaviour, not a
prediction about any particular site's latency, and `budget.stages[].actual_s` records
where the time actually went so a slow run is attributable rather than mysterious.

**Degradation rule.** When a stage exhausts its budget it is abandoned, its bundle section
is marked `partial` or `unavailable` with a reason, and collection continues. Never extend a
stage by borrowing from another. A bundle that says what it could not collect is worth more
than one that guessed — analysers are required to emit `not_determinable` for any evidence
that is not `ok`. The render pass can also be abandoned *before it starts* — no
`headless_browser` tool this run, not a mid-run timeout — and that case is recorded in
`budget.stages` exactly the same way (see step 5), because a check that quietly returns
`not_determinable` is invisible in the final report unless its stage is declared abandoned.

## Safety rules

These are not advisory. A collection that violates any of them is a failed collection.

- **Read-only.** `GET` and `HEAD` only. Never `POST`, `PUT`, `PATCH` or `DELETE`.
- **Never submit a form, click a control, or execute a user interaction** while rendering
  a page. Navigate, resize, and read — nothing else.
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
