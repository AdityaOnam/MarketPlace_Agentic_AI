---
name: engagement-defect-audit
description: Detect statically and mechanically detectable defects known to obstruct access or comprehension for visitors who already arrived — WCAG accessibility failures, mobile layout breakage, non-descriptive link text, content-blocking overlays, blank first paint on JS-only pages, autoplaying media, layout-shift-causing markup, missing structural landmarks, and excessive ad density — by reading extracted page text and rendered geometry in an evidence bundle. Use as the on-site-engagement stage of a website audit, covering mechanisms E and F from the brief's appendix. Detects defects only; never predicts bounce, dwell, or conversion.
license: Apache-2.0
allowed-tools: []
---

# Engagement Defect Audit

Mechanisms E and F of the brief. This skill covers eleven checks, all statically or
mechanically detectable, and all framed the same deliberate way per **D-008**: it detects
*defects known to obstruct access and comprehension*, and it never claims to predict bounce,
dwell time, scroll depth, or conversion. The reason is not caution for its own sake — it is
that we cannot observe those outcomes read-only, and most of the literature that quantifies
them is vendor-authored and uncitable (`docs/research/EVIDENCE-LEDGER.md` §"Declared
limitations", `LIM-04`). Read `docs/DECISIONS.md` D-008 before changing this framing.

**This skill declares no tools and makes no network requests.** It is a pure function from
an evidence bundle to findings. All fetching and the shared render pass happened in
`site-evidence-collector`.

## When to use

Invoked by `audit-orchestrator` with an evidence bundle. `CHK-E-019` deliberately
recomputes the same raw-vs-rendered gap that `render-extractability-audit`'s `CHK-D-003`
computes — analysers are blind to each other by design, so both run their own version, and
`audit-orchestrator` collapses a shared JS-only root cause into one reported defect rather
than two. See `docs/ARCHITECTURE.md` §4.3.

## Inputs

The `pages` and `rendered` sections of an evidence bundle
(`site-evidence-collector/references/bundle-schema.md`). Reads nothing else.

## Output

Zero to eleven findings in the standard envelope, plus one special case: `CHK-E-024` never
contributes to `findings[]` (see "The single-source exception" below). Emits `absent`
explicitly wherever a check ran clean.

## Procedure

1. **Gate on evidence, per section.** Checks reading only `pages[]` (`CHK-E-017`,
   `CHK-E-020`, `CHK-E-021`, `CHK-E-022`, `CHK-E-024`) emit `not_determinable` with
   `pages.reason` if `pages.status != "ok"`. Checks reading `rendered[]`
   (`CHK-E-015` overflow, `CHK-E-016`, `CHK-E-018`, `CHK-E-019`, `CHK-E-023`) do the same
   with `rendered.reason` if `rendered.status != "ok"`. `CHK-E-014` reads both.
2. **Evaluate `CHK-E-014`** (WCAG machine-detectable failures) — five subtypes read from
   `pages[]` (missing `lang`, missing `alt`, empty links/buttons via
   `interactive_empty`, unlabelled form controls) plus one from `rendered[]`
   (low-contrast text pairs). Each subtype is graded independently.
3. **Evaluate `CHK-E-015`** (viewport blocking) from `pages[].meta.viewport` (missing meta,
   `user-scalable=no`, `maximum-scale<2`) and `rendered[].viewports.mobile_375.
   horizontal_overflow`.
4. **Evaluate `CHK-E-016`** (small tap targets) from
   `rendered[].viewports.mobile_375.tap_targets[]`, using the collector-computed
   `standalone` and `spacing_px` fields (`docs/BUNDLE-SCHEMA.md` Caveat 3 — the WCAG 2.2
   inline-text-link exemption is already applied there).
5. **Evaluate `CHK-E-017`** (non-descriptive anchor text) from `pages[].links[].text` /
   `aria_label`.
6. **Evaluate `CHK-E-018`** (content-blocking overlay) from
   `rendered[].viewports.mobile_375.overlays[]` and `body_scroll_locked`.
7. **Evaluate `CHK-E-019`** (blank first paint) by independently comparing
   `pages[].main_text_words`/`noscript` against `rendered[].main_text_words` on the
   homepage — the same comparison `CHK-D-003` makes, computed here without reference to
   its result.
8. **Evaluate `CHK-E-020`** (autoplaying media with sound) from `pages[].media[]`.
9. **Evaluate `CHK-E-021`** (missing image/iframe dimensions) from `pages[].images[]`,
   `pages[].iframes[]`.
10. **Evaluate `CHK-E-022`** (landmark/heading integrity) from `pages[].landmarks`,
    `pages[].headings`.
11. **Evaluate `CHK-E-023`** (ad density) from
    `rendered[].viewports.mobile_375.ad_regions[]` and `ad_area_pct_total`, **requiring
    agreement from ≥2 independent detectors before emitting** — see "The weakest check"
    below.
12. **Evaluate `CHK-E-024`** (trust signals) from `pages[].contact_signals`,
    `site.scheme`, `pages[].dates` — commercial/service/news archetypes only. Emit per the
    single-source exception, never as a scored finding.
13. **Emit** the envelope for all eleven checks.

Full per-check detail lives in [`references/checks.md`](references/checks.md).

## Checks at a glance

| Check | Subject | Strength | Ceiling |
| --- | --- | --- | --- |
| CHK-E-014 | WCAG machine-detectable failures (5 subtypes) | HARD-MECHANICAL/NORMATIVE | high (a–e), medium (contrast) |
| CHK-E-015 | Viewport blocking / horizontal overflow | HARD-MECHANICAL/NORMATIVE | high (zoom block), medium (meta/overflow) |
| CHK-E-016 | Small tap targets (&lt;24×24 CSS px) | NORMATIVE | medium |
| CHK-E-017 | Non-descriptive anchor text | NORMATIVE/THEORETICAL | medium |
| CHK-E-018 | Content-blocking overlay at load | HARD-MECHANICAL/NORMATIVE | high |
| CHK-E-019 | Blank first paint, no fallback | HARD-MECHANICAL/CAUSAL | high |
| CHK-E-020 | Autoplaying media with sound | NORMATIVE | medium |
| CHK-E-021 | Missing image/iframe dimensions (CLS cause) | THEORETICAL | medium (≥10 elements/≥2 pages), else low — never higher |
| CHK-E-022 | Landmark/heading integrity | NORMATIVE/PRACTITIONER | high (no h1), medium (skips/missing main) |
| CHK-E-023 | Mobile ad density &gt;30% | CORRELATIONAL/NORMATIVE | medium |
| CHK-E-024 | Missing trust signals | CORRELATIONAL, single-study | **recommendation only — never a finding** |

## The single-source exception — CHK-E-024

`docs/research/EVIDENCE-LEDGER.md` supports this check with a single, unreplicated source.
Under the single-source rule (D-004, formalised in D-012), a check in this position may not
be emitted as a scored finding at any severity — it ships as a proactive recommendation
until a second independent source is verified. Concretely: emit `CHK-E-024`'s envelope with
`severity: null` and `recommendation_only: true` instead of a severity level.
`audit-orchestrator` reads that flag and routes it to the report's `recommendations[]`
array under D-012, never into `findings[]` or the severity summary. This is the only check
in the marketplace that sets `recommendation_only`; every other check's severity is a normal
scored value.

## The weakest check — CHK-E-023

`docs/BUNDLE-SCHEMA.md` Caveat 1 is explicit that "ad region" has no site-agnostic
definition. The bundle's `ad_regions[].detector` field records which heuristic fired
(third-party iframe, ad-slot attribute, filter-list match) precisely so this check can
require **at least two independent detectors to agree** before counting a region as an ad;
a region flagged by only one detector is excluded from `ad_area_pct_total` for this check's
purposes, and if agreement can't be established at all, emit `not_determinable` rather than
a low-confidence finding. This check is the most likely of the eleven to fail its
negative-control target — treat that as a reason for restraint, not a reason to drop it.

## False-positive discipline

Every check here caps at the strength its evidence actually supports (D-004, D-011): the
WCAG- and Better-Ads-grounded checks (`E-014`–`E-018`, `E-020`, `E-022`, `E-023`) cite a
published standard as the authority and never claim a measured effect on any user; `E-019`
and `E-021` are graded on what they mechanically cause, not on an unevidenced engagement
outcome; `E-024` is demoted below a finding entirely rather than dressed up as one. None of
the eleven checks in this skill ever produces the sentence "this will hurt engagement" —
only "this obstructs access or comprehension, per {standard/mechanism}."
