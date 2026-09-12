# Evidence bundle schema

The interface between `site-evidence-collector` and the four analysers. Pinned to exact
field names so the six skills compose. Authoritative over `ARCHITECTURE.md §4.1`, which
describes it only at section level.

**Contract.** The collector emits exactly one bundle. Analysers read it, never extend it,
and never fetch. Every section carries a status; an analyser whose required evidence is not
`ok` emits `not_determinable` with the section's reason — it never infers.

```
status: "ok" | "partial" | "unavailable"
reason: string | null      # required whenever status != "ok"
```

---

## Top level

```json
{
  "schema_version": "1.0.0",
  "site": { ... },
  "robots": { ... },
  "discovery": { ... },
  "pages": [ ... ],
  "rendered": [ ... ],
  "links": { ... },
  "anchors": { ... },
  "budget": { ... }
}
```

## `site`

```json
{
  "status": "ok",
  "reason": null,
  "input": "example.com",
  "canonical_host": "www.example.com",
  "origin": "https://www.example.com",
  "scheme": "https",
  "redirect_chain": ["http://example.com", "https://example.com", "https://www.example.com"],
  "tls_valid": true,
  "archetype": "ecommerce | documentation | saas_marketing | news_editorial | local_business | brochure | reference | institutional | marketplace | personal | unknown",
  "archetype_confidence": 0.0
}
```

`archetype` drives the per-archetype suppression rules in the ledger (D-009). `reference`, `institutional`, `marketplace` and `personal` were added by D-035; `archetype_confidence` (0.55–0.90, or 0.0 with `unknown`) is derived from evidence strength and margin, see procedure.md §3. It is a
collector-side label because it depends on the whole page inventory, not on one page.

## `robots`

```json
{
  "status": "ok",
  "reason": null,
  "fetch_status": 200,
  "body": "<verbatim text>",
  "parse_ok": true,
  "agents": {
    "GPTBot":        { "class": "retrieval", "allowed_root": false, "disallow_rules": ["/"], "matched_line": 12, "crawl_delay": null },
    "PerplexityBot": { "class": "retrieval", "allowed_root": true,  "disallow_rules": [],    "matched_line": null, "crawl_delay": null },
    "CCBot":         { "class": "training",  "allowed_root": false, "disallow_rules": ["/"], "matched_line": 20, "crawl_delay": null },
    "*":             { "class": "generic",   "allowed_root": true,  "disallow_rules": ["/admin"], "matched_line": 3, "crawl_delay": 10 }
  },
  "sitemap_declarations": ["https://www.example.com/sitemap.xml"]
}
```

`class` is `retrieval` | `training` | `hybrid` | `generic` | `unknown`. **This field is what
separates CHK-D-001 from CHK-D-002** — the ledger requires the distinction, and the agent
list with its classification lives in the collector's `references/ai-crawler-agents.md` so
it is updatable without touching logic.

`matched_line` supplies the `robots.txt line {N}` fragment CHK-D-001's evidence string
requires.

## `discovery`

```json
{
  "status": "ok",
  "reason": null,
  "sitemap_found": true,
  "sitemap_urls_count": 240,
  "inventory": [
    { "url": "https://www.example.com/", "page_type": "home", "source": "seed" },
    { "url": "https://www.example.com/about", "page_type": "about", "source": "sitemap" }
  ],
  "sampled_static": ["https://www.example.com/", "..."],
  "sampled_rendered": ["https://www.example.com/", "...", "..."],
  "sampling_seed": "sha256:..."
}
```

`page_type` ∈ `home | about | contact | product | category | article | documentation |
legal | pricing | faq | login | other`. Required by D-009: scoring is per page type, never
pooled. `sampling_seed` makes page selection deterministic, which D-010's `pass^k` needs.

## `pages[]`

One entry per statically fetched page (≤20).

```json
{
  "url": "https://www.example.com/",
  "final_url": "https://www.example.com/",
  "status": "ok",
  "reason": null,
  "http_status": 200,
  "page_type": "home",
  "headers": { "last-modified": "...", "content-type": "...", "etag": "..." },
  "raw_html": "<verbatim>",
  "raw_html_bytes": 48210,

  "main_text": "<boilerplate-stripped extraction>",
  "main_text_words": 812,
  "main_content_source": "main",
  "extraction_ok": true,
  "js_render_suspected": false,
  "js_payload_heavy": false,

  "title": "...",
  "meta": { "viewport": "width=device-width, initial-scale=1", "description": "...", "robots": null },
  "lang": "en",
  "canonical": { "href": "https://www.example.com/", "self_referential": true, "cross_domain": false },

  "headings": [ { "level": 1, "text": "...", "order": 0 } ],
  "landmarks": { "main": 1, "nav": 1, "header": 1, "footer": 1 },

  "structured_data": {
    "json_ld": [ { "type": "Organization", "raw": {}, "fields_present": ["name", "url", "sameAs"] } ],
    "microdata_types": [],
    "rdfa_types": []
  },

  "links": [ { "href": "...", "text": "read more", "rel": null, "internal": true, "aria_label": null } ],
  "outbound_profile_links": [ "https://<profile-host>/<handle>" ],

  "images": [ { "src": "...", "alt": null, "decorative_hint": false, "width_attr": null, "height_attr": null, "css_aspect_ratio": null, "in_picture": false } ],
  "iframes": [ { "src": "...", "width_attr": null, "height_attr": null, "title": null } ],
  "media": [ { "tag": "video", "autoplay": true, "muted": false, "controls": false, "loop": true } ],

  "form_controls": [ { "type": "text", "id": "q", "has_label": false, "aria_label": null } ],
  "interactive_empty": { "links_no_text": 2, "buttons_no_text": 1 },

  "noscript": { "present": true, "words": 12 },
  "dates": { "meta_published": null, "meta_modified": null, "visible_dates": [], "header_last_modified": "..." },

  "contact_signals": { "email": true, "phone": "+1 555 0100", "postal_address": "...", "org_name_footer": "Example Ltd" },
  "trigram_hash": "sha256:..."
}
```

`trigram_hash` supports CHK-D-013's Jaccard comparison without shipping full text
comparisons into the analyser.

## `rendered[]`

**In the grading sandbox this is always `[]` — there is no `headless_browser` tool
available (D-015).** That is a structural fact known before collection starts, not a
per-run failure, and it is handled differently from a mid-run timeout: the collector still
records a `render_pass` entry in `budget.stages` marked `abandoned: true` at zero elapsed
time, specifically so `degraded_stages[]` in the assembled report names the six affected
checks rather than them silently disappearing (`not_determinable` findings never reach the
final report otherwise). Two of the six — `CHK-D-003` and `CHK-E-019` — re-derive a
one-sided signal from static HTML alone when this happens; the other four
(`CHK-E-014`'s contrast sub-check, `CHK-E-015`'s overflow sub-check, `CHK-E-016`,
`CHK-E-018`) have no defensible static proxy and stay `not_determinable`, visible only
through `degraded_stages[]`. A seventh, `CHK-E-023`, was in this list until D-018 cut it
outright — unlike the other four it had no reason to exist beyond the renderer, and it was
already the weakest check in the ledger.

One entry per rendered page (≤3). **One navigation per page.** Both viewports are measured
by resizing the same loaded page rather than re-navigating — a second navigation would
roughly double the most expensive stage in the budget for no additional evidence.

```json
{
  "url": "https://www.example.com/",
  "status": "ok",
  "reason": null,
  "render_ms": 4120,
  "dom_html": "<verbatim post-JS>",
  "main_text": "...",
  "main_text_words": 812,
  "h1_count": 1,

  "viewports": {
    "mobile_375": {
      "measured": true,
      "document_scroll_width": 375,
      "horizontal_overflow": false,
      "body_scroll_locked": false,
      "overlays": [ { "selector": "...", "z_index": 1000, "viewport_coverage_pct": 62.0, "dismissible_hint": "cookie|age|none" } ],
      "tap_targets": [ { "selector": "...", "w": 18.0, "h": 18.0, "standalone": true, "spacing_px": 4.0 } ],
      "ad_regions": [ { "selector": "...", "area_pct": 12.0, "detector": "iframe_thirdparty|slot_attr|filterlist" } ],
      "ad_area_pct_total": 12.0
    },
    "desktop_1280": { "measured": true, "...": "same shape; only the homepage is measured at desktop" }
  },

  "computed_styles": {
    "contrast_pairs": [ { "selector": "...", "fg": "#777777", "bg": "#ffffff", "ratio": 4.2, "font_px": 14, "bold": false } ]
  }
}
```

## `links`

```json
{
  "status": "ok",
  "reason": null,
  "checked_count": 20,
  "results": [ { "url": "...", "http_status": 404, "from_page": "...", "anchor_text": "..." } ],
  "skipped": [ { "url": "...", "reason": "robots_disallow | fragment | mailto | budget" } ]
}
```

## `anchors`

The only off-site evidence in the bundle. CHK-D-026.

```json
{
  "status": "ok",
  "reason": null,
  "declared": [ { "url": "...", "source": "json_ld_sameAs | footer_link", "host": "..." } ],
  "checked_count": 6,
  "results": [
    { "url": "...", "http_status": 200, "resolved": true },
    { "url": "...", "http_status": 403, "resolved": null, "note": "bot_blocked_not_broken" }
  ]
}
```

`resolved: null` on 401/403/429 is load-bearing: the ledger requires these be treated as
not-determinable, never as failures. Encoding it as a distinct value rather than `false`
makes the false-positive guard structural rather than a rule the analyser must remember.

## `budget`

```json
{
  "status": "ok",
  "reason": null,
  "stages": [
    { "name": "robots_discovery",  "budget_s": 15, "actual_s": 3.2,  "abandoned": false },
    { "name": "static_fetch",      "budget_s": 45, "actual_s": 28.9, "abandoned": false },
    { "name": "render_pass",       "budget_s": 75, "actual_s": 74.9, "abandoned": true, "completed_items": 2, "planned_items": 3, "reason": "25s per-page timeout hit on the third page." },
    { "name": "internal_links",    "budget_s": 25, "actual_s": 11.0, "abandoned": false },
    { "name": "offsite_anchors",   "budget_s": 20, "actual_s": 8.4,  "abandoned": false },
    { "name": "analysis_reserve",  "budget_s": 40, "actual_s": null, "abandoned": false }
  ],
  "total_s": 126.4,
  "cap_s": 300
}
```

---

## Coverage walk — all 27 checks

Every check's `Observation` column in the ledger, mapped to the fields that satisfy it.

| Check | Satisfied by |
| --- | --- |
| D-001 | `robots.agents[*].class == "retrieval"`, `allowed_root`, `matched_line` |
| D-002 | `robots.agents[*].class == "training"` + D-001 outcome |
| D-003 | `pages[].main_text_words`, `headings` vs `rendered[].main_text_words`, `h1_count` |
| D-004 | `pages[].main_text_words`, `extraction_ok`, `page_type` |
| D-005 | `pages[].headings`, `main_text_words` |
| D-006 | `pages[].main_text` (home/about), `structured_data` |
| D-007 | `pages[].structured_data.json_ld[].fields_present` |
| D-008 | `pages[].canonical` |
| D-009 | `links.results[].http_status`, `links.skipped[]` |
| D-010 | `pages[].main_text`, `page_type` |
| D-011 | `pages[].main_text` |
| D-012 | `pages[].dates`, `page_type` |
| D-013 | `pages[].trigram_hash` |
| D-025 | `pages[].structured_data.json_ld[].fields_present` (sameAs), `outbound_profile_links` |
| D-026 | `anchors.results[]` |
| D-027 | `pages[].structured_data`, `contact_signals` across pages |
| E-014 | `pages[].lang`, `images[].alt`, `form_controls[].has_label`, `interactive_empty`, `rendered[].computed_styles.contrast_pairs` |
| E-015 | `pages[].meta.viewport`, `rendered[].viewports.mobile_375.horizontal_overflow` |
| E-016 | `rendered[].viewports.mobile_375.tap_targets` |
| E-017 | `pages[].links[].text`, `aria_label` |
| E-018 | `rendered[].viewports.mobile_375.overlays`, `body_scroll_locked` |
| E-019 | `pages[].main_text_words`, `noscript` vs `rendered[].main_text_words` |
| E-020 | `pages[].media[]` (`autoplay`, `muted`, `controls`) |
| E-021 | `pages[].images[]`, `iframes[]` (dimension attrs, `in_picture`) |
| E-022 | `pages[].headings`, `landmarks` |
| E-024 | `pages[].contact_signals`, `site.scheme`, `pages[].dates` |

**All 26 are covered.** Two carry caveats worth stating rather than burying.

### Caveat 1 (resolved by removal) — CHK-E-023 ad detection was the weakest link

"Ad region" has no site-agnostic definition, which is why this check carried a
two-detector agreement rule no other check needed and why this caveat named it the most
likely of the 27 to fail its negative-control target. **D-018 cut the check on
2026-09-04** rather than shipping it behind a bespoke guard: it could only read
`rendered[]`, which is empty in every graded run, so it emitted nothing there at all. The
`ad_regions[]` fields and the `detector` classifier remain in `render_geometry.py`, inert,
because removing them would touch the collector for no gain. This caveat is kept rather
than deleted so the reasoning survives the check.

### Caveat 2 — CHK-D-012 needs a time-sensitivity label the bundle doesn't carry

The ledger says "NEVER raise on EVERGREEN", but the bundle supplies `page_type`, not
temporal sensitivity. Deciding whether a page is time-sensitive is judgment, so it belongs
in `entity-identity-audit`, not the collector — the bundle gives it the inputs
(`page_type`, `dates`, URL pattern, tense cues in `main_text`) and the analyser classifies.
Recorded here so it isn't mistaken for a gap.

### Caveat 3 — CHK-E-016 "standalone" is a judgment encoded as data

`tap_targets[].standalone` and `spacing_px` are collector-computed, which puts part of the
false-positive guard (inline text links are exempt under WCAG 2.2 SC 2.5.8) in the
collector. This is deliberate: the exemption depends on layout geometry that only exists
during rendering, and re-deriving it in the analyser would mean shipping geometry the
analyser would otherwise not need.

## Conflicts found

**One.** `ARCHITECTURE.md §4.1` lists "375 px and desktop captures" for each of ≤3 rendered
pages, implying six viewport measurements. The budget table allows 75 s for the whole render
stage. Resolved by measuring both viewports from a single navigation per page (resize, don't
re-navigate), and by measuring desktop **only on the homepage** — desktop adds evidence for
no check that mobile doesn't already cover, since every viewport-dependent check in the
ledger is specified at 375 px. Net: 3 navigations, 4 measurements.
