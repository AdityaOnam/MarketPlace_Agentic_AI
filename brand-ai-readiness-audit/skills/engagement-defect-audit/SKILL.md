---
name: engagement-defect-audit
description: Detect on-site defects known to obstruct user access or content comprehension — accessibility violations, mobile layout failures, content-blocking overlays, blank first paint, autoplaying media with sound, structural layout instability, heading/landmark integrity failures, excessive ad density, and missing trust signals. Covers mechanisms E (personalization and prior context — detecting the engagement barriers that vary a user's experience) and F (why machines drop content — detecting when substantive content is not available as readable text). Use as the engagement analysis stage of a brand AI-readiness audit, after the evidence bundle has been collected. This skill detects defects, never predicts engagement outcomes.
license: Apache-2.0
allowed-tools: []
---

# Engagement Defect Audit

Mechanisms E and F of the brief: *engagement barriers that obstruct how visitors experience
the site, and how machines lose content.* Per **D-008**, this skill detects defects known
to obstruct access and comprehension. It never predicts bounce rate, dwell time, scroll
depth, or conversion — those are field engagement outcomes not observable read-only (LIM-04).

**This skill declares no tools and makes no network requests.** It is a pure function from
an evidence bundle to findings. All fetching and rendering happened in `site-evidence-collector`.

## When to use

Invoked by `audit-orchestrator` with an evidence bundle. This is the largest analyser:
eleven checks across accessibility, mobile layout, overlay behaviour, JavaScript rendering
gaps, media controls, structural layout stability, heading integrity, advertising density,
and trust signals (CHK-E-014 through CHK-E-024).

## Inputs

Two sections of the evidence bundle:

| Section | Fields used |
| --- | --- |
| `pages[]` | `lang`, `images[]`, `form_controls[]`, `interactive_empty`, `links[]`, `media[]`, `headings`, `landmarks`, `noscript`, `main_text_words`, `meta.viewport`, `contact_signals`, `dates`, `page_type`, `url`, `status` |
| `rendered[]` | `computed_styles.contrast_pairs`, `viewports.mobile_375.horizontal_overflow`, `viewports.mobile_375.tap_targets`, `viewports.mobile_375.overlays`, `viewports.mobile_375.body_scroll_locked`, `viewports.mobile_375.ad_regions`, `viewports.mobile_375.ad_area_pct_total`, `main_text_words` |

Reads `pages` and `rendered`. Reads nothing else.

## Output

Up to eleven finding envelopes in the standard format defined in
`docs/ARCHITECTURE.md §4.2`. Every check emits an envelope even when clean (`state:
"absent"`). **CHK-E-024 is the one exception:** per the single-source rule (D-004/ledger),
it must never appear in `findings[]`; it ships as a `recommendation` envelope so the
orchestrator routes it to `recommendations[]` rather than `findings[]`. Mark it
`"route": "recommendations"` in the envelope.

## Procedure

1. **Gate on evidence.** Before evaluating any check:
   - Checks that need only static HTML (`pages`): gate on `pages.status`. If `pages.status
     != "ok"` for a given page, exclude it from that check's page sample. If the whole
     section is unavailable, emit all static checks as `not_determinable`.
   - Checks that need rendered data (`rendered`): gate on both the section status and the
     specific `rendered[url].status`. If the render pass was abandoned (`budget.stages`
     shows `abandoned: true` for `render_pass`), emit all render-dependent checks as
     `not_determinable` with reason "render stage abandoned (budget exhausted)".
   - Never infer from absent evidence.

2. **Evaluate the eleven checks** (full detail in `references/checks.md`):
   - CHK-E-014 — Machine-detectable WCAG failures (lang, alt, labels, empty controls, contrast)
   - CHK-E-015 — Viewport meta missing or zoom-blocking
   - CHK-E-016 — Standalone tap targets below WCAG 2.2 minimum (24×24 CSS px)
   - CHK-E-017 — Non-descriptive anchor text
   - CHK-E-018 — Content-blocking overlay at load
   - CHK-E-019 — Blank first paint without JS (JS-render gap + no fallback)
   - CHK-E-020 — Autoplaying media with sound and no pause/stop control
   - CHK-E-021 — Images/iframes without explicit dimensions (structural reflow)
   - CHK-E-022 — Missing landmark or heading integrity violation
   - CHK-E-023 — Ad/promo density exceeds 30% of mobile viewport
   - CHK-E-024 — Missing trust signals *(recommendation-only — see note below)*

3. **Apply false-positive guards** before emitting any finding. See check-level guards in
   `references/checks.md`. Do not emit a finding you cannot suppress correctly.

4. **Emit** all eleven envelopes. `absent` and `not_applicable` are emitted, not dropped.
   CHK-E-024 carries `"route": "recommendations"` in its envelope; the orchestrator is
   responsible for placing it in `recommendations[]` rather than `findings[]`.

## Note on CHK-E-019 and the render comparison

CHK-E-019 (blank first paint) independently recomputes the raw-vs-rendered word-count gap
that `render-extractability-audit`'s CHK-D-003 also computes. **This duplication is
deliberate:** analysers are blind to each other by design. Both checks independently arrive
at the same raw comparison; the orchestrator deduplicates the reported root cause when
both fire on a JS-only site. See ARCHITECTURE.md §4.3 and the orchestrator skill for the
dedup logic. Do not try to avoid this duplication inside this skill — the architectural
boundary is the point.

## Note on CHK-E-023 and the two-detector rule

CHK-E-023 (ad density) is explicitly flagged in `docs/BUNDLE-SCHEMA.md` (Caveat 1) as
the weakest check in the entire ledger. The `ad_regions[]` entries each carry a `detector`
field recording which heuristic fired (`iframe_thirdparty`, `slot_attr`, or `filterlist`).

**Require ≥2 independent detectors to agree before emitting a finding.** If only one
detector type fires across all ad regions, emit `not_determinable` with reason "only one
detection method agrees — insufficient confidence." A single detector's verdict is not
enough to avoid a false positive.

## Note on CHK-E-024 and the single-source rule

CHK-E-024 (trust signals) is demoted from `findings[]` under the single-source rule
(D-004/ledger): its support reduces to one unreplicated study. It must never appear in a
`findings[]` array at any severity. It ships exclusively as a recommendation, clearly
marked in its envelope so the orchestrator routes it correctly. If the sources supporting
CHK-E-024 are later hand-verified and a second independent source confirmed, the ledger
must be updated first; only then may this check be promoted to a finding.

## Checks at a glance

| Check | Renders? | Evidence strength | Severity | FP guard |
| --- | --- | --- | --- | --- |
| CHK-E-014 | partial (contrast) | HARD-MECHANICAL / NORMATIVE | high (a–e), medium (contrast) | `alt=""` is correct for decorative images |
| CHK-E-015 | yes (overflow) | HARD-MECHANICAL / NORMATIVE | high (zoom block), medium (missing meta/overflow) | Exclude desktop-only sites; exclude minimum-scale=1 |
| CHK-E-016 | yes | NORMATIVE | medium | Exclude inline text links; exclude spaced targets |
| CHK-E-017 | no | NORMATIVE / THEORETICAL | medium | Exclude aria-labeled links |
| CHK-E-018 | yes | HARD-MECHANICAL / NORMATIVE | high | Suppress cookie-consent and age-gate overlays |
| CHK-E-019 | yes | HARD-MECHANICAL / CAUSAL | high | Suppress if noscript >50 words or skeleton UI present |
| CHK-E-020 | no | NORMATIVE (WCAG 2.2 SC 1.4.2) | medium | `video autoplay muted` is fine |
| CHK-E-021 | no | THEORETICAL | medium (≥10 elements, ≥2 pages), low otherwise | Require N≥3; exclude responsive `<picture>` tags |
| CHK-E-022 | no | NORMATIVE / PRACTITIONER | high (no h1), medium (skips/missing main) | Exclude heading skips on user-generated content pages |
| CHK-E-023 | yes | CORRELATIONAL / NORMATIVE | medium | Suppress if no ads detected site-wide; require ≥2 detectors |
| CHK-E-024 | no | CORRELATIONAL (single-study) | **recommendation-only** | Only apply to commercial/service/news sites |

Full per-check evidence strings, severity rules, FP guards, not-determinable paths, and
suggested actions: [`references/checks.md`](references/checks.md).

## False-positive discipline

The four highest false-positive risks in this skill:

1. **CHK-E-014: flagging `alt=""` as missing alt text.** Empty alt on decorative images
   is correct per WCAG. The check must distinguish `alt` attribute absent (a violation)
   from `alt=""` (correct and intentional). Test `image.alt === null`, not `!image.alt`.

2. **CHK-E-023: single detector triggering a finding.** Ad detection is heuristic-based.
   Requiring ≥2 independent detector types to agree is not optional — the schema's
   `detector` field exists precisely for this guard. A filter-list match alone, or a single
   `iframe_thirdparty` detection, is not sufficient.

3. **CHK-E-018: flagging cookie banners and age-verification gates.** These overlays are
   a legal compliance requirement, not a defect. The `dismissible_hint` field in the
   bundle encodes `"cookie"` and `"age"` for this purpose — suppress when this field
   matches either value.

4. **CHK-E-019: firing without checking noscript fallback.** A JS-only site that provides
   a `<noscript>` fallback with >50 words is not blank — the fallback is the content.
   Check `noscript.present` and `noscript.words` before emitting.
