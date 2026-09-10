---
name: content-engagement-audit
description: Determine whether the content a machine reader receives is complete, substantial, well-structured, internally reachable, explicitly stated, and non-duplicated, AND detect on-site defects known to obstruct user access or content comprehension — accessibility violations, mobile layout failures, content-blocking overlays, blank first paint, autoplaying media with sound, structural layout instability, heading/landmark integrity failures, and missing trust signals. Covers mechanisms B (how assistants use sources), C (how machines "read" a page), E (personalization and prior context), and F (why machines drop content) from the brief's appendix. Use as the content-and-engagement stage of a website audit, after the evidence bundle has been collected. Detects defects, never predicts engagement outcomes.
license: Apache-2.0
allowed-tools: []
---

# Content & Engagement Audit

Formerly two skills — `render-extractability-audit` (mechanisms B/C) and
`engagement-defect-audit` (mechanisms E/F) — merged 2026-09-04 as **D-025**, after the
leave-one-skill-out ablation (`harness/ablation.py`) found the one genuine cross-skill rule
between them (O-1: `CHK-E-019` defers to `CHK-D-003`) never actually changed
`CHK-E-019`'s outcome on any of 36 real sites. `docs/DECISIONS.md` has the full evidence
trail; the short version is that keeping these separate bought nothing measurable, so they
merge for real rather than staying split on architectural taste alone.

Seventeen checks, in two families that still think about different questions but now share
one evaluate() call:

- **Mechanisms B/C — is the fact actually here, in text, where a non-rendering reader
  would receive it?** A page that assembles its content only after load, or states a fact
  implicitly, buries it, or never states it as an unambiguous number or definition, is
  invisible to a program reading the way a crawler does — even though a human sees it fine.
- **Mechanisms E/F — does a visitor's actual experience of the page work?** Accessibility
  failures, layout that breaks on mobile, overlays that block content at load, media that
  autoplays with sound, structural integrity failures. Per **D-008**, this half detects
  defects known to obstruct access and comprehension; it never predicts bounce rate, dwell
  time, scroll depth, or conversion — those are field engagement outcomes not observable
  read-only (LIM-04).

**This skill declares no tools and makes no network requests.** It is a pure function from
an evidence bundle to findings. All fetching and the shared render pass happened in
`site-evidence-collector`.

## When to use

Invoked by `audit-orchestrator` with an evidence bundle, after (or alongside)
`crawl-access-audit` — a site an AI cannot fetch at all makes these findings describe
content nothing will reach, which the orchestrator says explicitly using
`crawl-access-audit`'s result.

## Inputs

The `pages`, `rendered`, and `links` sections of an evidence bundle
(`site-evidence-collector/references/bundle-schema.md`). Reads nothing else — in particular,
never `robots` or `anchors`.

| Section | Fields used |
| --- | --- |
| `pages[]` | `main_text_words`, `headings`, `page_type`, `extraction_ok`, `lang`, `images[]`, `form_controls[]`, `interactive_empty`, `links[]`, `media[]`, `landmarks`, `noscript`, `meta.viewport`, `contact_signals`, `dates`, `trigram_hash`, `main_text`, `url`, `status` |
| `rendered[]` | `main_text_words`, `h1_count`, `computed_styles.contrast_pairs`, `viewports.mobile_375.*` |
| `links[]` | `results[].http_status`, `skipped[]` |

## Output

Up to seventeen finding envelopes in the standard format (`docs/ARCHITECTURE.md` §4.2).
Every check emits an envelope even when clean (`state: "absent"`), and `not_applicable`
where an exclusion in the FP guard took the check out of scope for this site. Five checks
never appear in `findings[]` regardless of state:

- **`CHK-D-010` and `CHK-E-021`** ship `recommendation_only: true` (demoted 2026-09-04,
  D-022 — both fired too broadly on real sites to function as a confirmed-defect claim;
  the underlying advice remains good).
- **`CHK-E-024`** ships `recommendation_only: true` under the single-source rule (D-004):
  its support reduces to one unreplicated study, and it must never appear in `findings[]`
  at any severity.
- **`CHK-D-011` and `CHK-D-013`** ship `recommendation_only: true` (demoted 2026-09-09,
  D-027 — R-1 hand-verification opened every cited source for each and found none actually
  support the check's claim; a genuine evidence gap, not a citation mismatch. Kept as
  recommendations rather than cut since the underlying advice stands on its own).

## Procedure

1. **Gate on evidence, per section.** If `pages.status != "ok"`, checks reading `pages[]`
   emit `not_determinable`. Same for `rendered.status` (gates the render-dependent checks)
   and `links.status` (gates `CHK-D-009` only). Within a section, a page whose own fetch
   failed (`extraction_ok: false`) is excluded per-page, not read as "the page is genuinely
   empty" — ten checks were found doing this wrong on 2026-09-04 (D-023) and fixed. Never
   infer from a partial page set what the missing pages would have shown.
2. **Classify the site's rendering posture (`CHK-D-003`).** Compare the homepage's raw
   `main_text_words`/`h1_count` against the matching `rendered[]` values. **Definitional**,
   not threshold-fitted: if the raw fetch has no h1 and under 50 words while the render has
   ≥200, that content is categorically absent from what a non-rendering fetch receives.
3. **Evaluate `CHK-D-004`** (thin content), conditioned on `page_type` (skip
   contact/login/home — a homepage is framing, not content, D-022) and on `CHK-D-003`'s
   outcome.
4. **Evaluate `CHK-D-005`** (heading structure) on pages ≥500 words, excluding
   legal/FAQ/minimal-content archetypes.
5. **Evaluate `CHK-D-009`** (broken internal links) from `links.results[]`.
6. **Evaluate `CHK-D-010`** (extractable-evidence density), suppressed if `CHK-D-004` fired.
7. **Evaluate `CHK-D-011`** (pronoun-saturated claims) on home/about pages.
8. **Evaluate `CHK-D-013`** (near-duplicate templated content) via Jaccard over `main_text`.
9. **Evaluate the ten `CHK-E-0XX` checks** — full detail in `references/checks.md`.
10. **Apply rule O-1 in-skill, last.** If `CHK-D-003` and `CHK-E-019` are both `present`
    (they independently compute the same raw-vs-rendered gap on the homepage, by design —
    see the note below), mark `CHK-E-019`'s state `"suppressed"` with
    `suppressed_by: ["CHK-D-003"]`. This used to be `audit-orchestrator`'s job
    (`compose_report.apply_suppression`), back when the two checks lived in different,
    mutually-blind skills; now that one `evaluate()` call computes both, the suppression
    moved in-skill, the same way `CHK-D-004` already self-suppresses against `CHK-D-003`.
11. **Emit** all seventeen envelopes.

Full per-check detail — evidence strings, severity rules, FP guards, and suggested
actions — lives in [`references/checks.md`](references/checks.md), sourced directly from
`docs/research/EVIDENCE-LEDGER.md` so the two never drift silently out of sync.

## Note on CHK-D-003 / CHK-E-019 duplication

`CHK-E-019` (blank first paint) independently recomputes the same raw-vs-rendered
word-count gap `CHK-D-003` computes. **The duplication is deliberate**, kept from before
the merge: the two checks were authored to measure the same mechanism from two angles
(extractability vs. engagement) without reading each other's output, and step 10 above
reconciles them once, after both have run, rather than one being rewritten to depend on
the other's internals.

## Note on the check that used to be here

`CHK-E-023` (mobile ad density) was **cut on 2026-09-04 (D-018)**. It read only
`rendered[].viewports.mobile_375.ad_area_pct_total`, and with no headless browser in the
grading sandbox (D-015) its loop body never executed — it emitted nothing at all, not even
a `not_determinable` envelope. It was also already the most false-positive-prone check in
the ledger. `CHK-E-016` and `CHK-E-018` are equally render-dead and are **kept**: they are
dead because a tool is absent, not because the check is weak, and
`degraded_stages[].affected_checks` names them in every report so the reader is told they
were not measured.

## Executable checks

`scripts/content_engagement_checks.py` implements all seventeen checks —
`evaluate(bundle) -> list[envelope]`, in the dependency order the procedure above requires
(`CHK-D-004` reads `CHK-D-003`'s result, `CHK-D-010` reads `CHK-D-004`'s, `CHK-E-019`'s
fate is decided last against `CHK-D-003`'s). `CHK-D-013`'s near-duplicate comparison runs
directly on `pages[].main_text` rather than `trigram_hash` (a single hash can prove two
pages identical or different but not produce a similarity *percentage*, which Jaccard
needs). `CHK-E-014`'s six sub-checks are graded independently, and its contrast sub-check
uses the real WCAG relative-luminance formula.
`CHK-D-010`/`CHK-D-011`/`CHK-D-013`/`CHK-E-021`/`CHK-E-024`'s `recommendation_only` flag
is enforced in code, not just documented.

## Checks at a glance

| Check | Mechanism | Strength | Ceiling | Notes |
| --- | --- | --- | --- | --- |
| CHK-D-003 | C — JS-rendering gap | HARD-MECHANICAL | critical | — |
| CHK-D-004 | C — thin main content | CORRELATIONAL | medium | Suppressed by CHK-D-003 (JS-SPA); excludes home |
| CHK-D-005 | B/C — absent/generic headings | THEORETICAL | low | Archetype exclusion only |
| CHK-D-009 | B — broken internal links | THEORETICAL/CORRELATIONAL | low | — |
| CHK-D-010 | B/C — low extractable-evidence density | CORRELATIONAL | low | **Recommendation-only**; suppressed by CHK-D-004 |
| CHK-D-011 | C — pronoun-saturated key claims | THEORETICAL/HEURISTIC | low | **Recommendation-only** (D-027); page-type exclusion |
| CHK-D-013 | C — near-duplicate templated content | CORRELATIONAL | low | **Recommendation-only** (D-027) |
| CHK-E-014 | E — machine-detectable WCAG failures | HARD-MECHANICAL / NORMATIVE | high (a–e), medium (contrast) | `alt=""` is correct for decorative |
| CHK-E-015 | E — viewport meta / zoom-blocking | HARD-MECHANICAL / NORMATIVE | high (zoom), medium (meta/overflow) | Exclude desktop-only sites |
| CHK-E-016 | E — standalone tap targets | NORMATIVE | medium | Exclude inline text links |
| CHK-E-017 | E — non-descriptive anchor text | NORMATIVE / THEORETICAL | medium | Exclude aria-labeled links |
| CHK-E-018 | E — content-blocking overlay | HARD-MECHANICAL / NORMATIVE | high | Suppress cookie/age-gate |
| CHK-E-019 | C/E — blank first paint | HARD-MECHANICAL / CAUSAL | high | Suppressed by CHK-D-003 (rule O-1) |
| CHK-E-020 | E — autoplaying media with sound | NORMATIVE | medium | `autoplay muted` is fine |
| CHK-E-021 | E — images/iframes missing dimensions | THEORETICAL | low | **Recommendation-only** |
| CHK-E-022 | E — missing landmark/heading integrity | NORMATIVE / PRACTITIONER | high (no h1), medium (other) | — |
| CHK-E-024 | E — missing trust signals | CORRELATIONAL (single-study) | **recommendation-only** | Commercial archetypes only |

## False-positive discipline

The largest risks, carried forward from both predecessor skills:

1. **Treating "different from how a human reads it" as a defect.** Every content-side
   check is conditioned on page type or archetype precisely because a thin contact page,
   a narrative about-us page, or a legitimately duplicated legal template is normal, not a
   discoverability problem.
2. **`CHK-E-014`: flagging `alt=""` as missing alt text.** Empty alt on decorative images
   is correct per WCAG. Test `image.alt === null`, not `!image.alt`.
3. **`CHK-E-018`: flagging cookie banners and age-verification gates.** Legal compliance,
   not a defect — suppress when `dismissible_hint` is `"cookie"` or `"age"`.
4. **`CHK-E-019`: firing without checking the noscript fallback.** A JS-only site with a
   `<noscript>` fallback carrying >50 words is not blank.
