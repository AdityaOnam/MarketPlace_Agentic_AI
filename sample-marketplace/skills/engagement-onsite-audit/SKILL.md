---
name: engagement-onsite-audit
description: >-
  Checks why visitors who arrive on a website fail to understand it, keep
  exploring, or act - weak above-the-fold orientation, unclear value
  proposition, missing or duplicated calls to action, shallow internal linking,
  broken breadcrumbs, filter and search state lost on navigation, and pages
  that assume prior context. Use as the on-site engagement half of a brand
  AI-readiness audit, especially for traffic arriving deep from AI answers.
license: MIT
allowed-tools:
  - Bash
  - Read
---

# On-Site Engagement Audit (Layer 4)

Machines finding you is half the job. This skill asks: **once a human lands,
can they orient, continue, and act?**

The framing that matters: visitors arriving from an AI answer land *deep and
context-free*. They did not pass the homepage, did not read the nav, and do not
know who you are. A page that assumes the journey strands them.

## When to use

Called by `audit-orchestrator` as check 4. Runs independently of the
discoverability checks — a perfectly crawlable site can still bounce everyone.

## Inputs

- `url` — target site (required)
- `max_pages` — page budget, default `8`

## Safety

`GET` only, robots-respecting, rate-limited. No form submission, no clicks that
change state, no auth.

## Procedure

1. Reuse the shared crawl from the orchestrator (or crawl if run standalone).
2. For each page, extract: heading tree, first 200 words, link graph, CTA
   candidates, breadcrumb markers, search affordance, media-vs-text balance.
3. Apply the checks below.
4. Emit `{"findings": [...]}` on stdout.

Run: `python scripts/check_engagement.py --url <url> --max-pages <n>`

## Checks

| ID | Fires when | Base severity |
|---|---|---|
| `EN-01` | No `<h1>`, or an `<h1>` that does not say what the page/brand is | high |
| `EN-02` | First 200 words never state what the organisation does or who it serves | high |
| `EN-03` | No clear primary call to action on content pages | medium |
| `EN-04` | Orphan / dead-end pages: < 3 outbound internal links | medium |
| `EN-05` | No breadcrumbs or hierarchy signal on pages ≥ 2 levels deep | medium |
| `EN-06` | Filter/search/tab state not reflected in the URL — not shareable, lost on reload | medium |
| `EN-07` | Key content carried only by images/video with no text equivalent | high |
| `EN-08` | Page depends on pronouns/deixis with no self-contained subject | medium |
| `EN-09` | No search affordance on a site with > 30 internal links | low |
| `EN-10` | Images missing alt text at > 50% | low |

## False-positive guards

- A landing page with one deliberate CTA is *good* — `EN-03` fires on absence,
  never on singularity.
- Do not fire `EN-04` on a genuine leaf page (contact, legal) — exempt routes
  matching `/(contact|privacy|terms|legal)`.
- `EN-06` only applies where a listing/filter UI actually exists.
- Never flag design taste. Every finding must cite a structural observation.

## Output

`{"findings": [...]}` with `category: "engagement"`. IDs and final ranking are
assigned by the orchestrator.

## References

- `references/checks.md` — thresholds, evidence templates, and fixes.
