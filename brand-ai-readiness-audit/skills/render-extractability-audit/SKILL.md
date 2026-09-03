---
name: render-extractability-audit
description: Determine whether the content a machine reader receives is complete, substantial, well-structured, internally reachable, explicitly stated, and non-duplicated, by comparing raw-fetch text against the shared render pass and scanning extracted main text in an evidence bundle. Use as the content-quality stage of a website audit, covering mechanisms B (how assistants use sources) and C (how machines "read" a page) from the brief's appendix — the difference between a page that reads well to a human and one a program can actually extract a fact from.
license: Apache-2.0
allowed-tools: []
---

# Render & Extractability Audit

Mechanisms B and C of the brief: a page that assembles its content only after load, or
states a fact implicitly, buries it, or never states it as an unambiguous number or
definition, is invisible to a program reading the same way a crawler does — even though a
human sees it fine. This skill covers seven checks that are all, in one way or another, "is
the fact actually here, in text, where a non-rendering reader would receive it."

**This skill declares no tools and makes no network requests.** It is a pure function from
an evidence bundle to findings. All fetching and the shared render pass happened in
`site-evidence-collector`.

## When to use

Invoked by `audit-orchestrator` with an evidence bundle, after (or alongside)
`crawl-access-audit` — a site an AI cannot fetch at all makes these findings describe
content nothing will reach, which the orchestrator says explicitly using
`crawl-access-audit`'s result. Its own `CHK-D-003` finding is read by `audit-orchestrator`
when composing `engagement-defect-audit`'s `CHK-E-019`: both checks independently measure
the same raw-vs-rendered gap on the homepage, by design (analysers are blind to each other),
and the orchestrator collapses a shared JS-only root cause into one reported defect rather
than four. See `docs/ARCHITECTURE.md` §4.3.

## Inputs

The `pages`, `rendered`, and `links` sections of an evidence bundle
(`site-evidence-collector/references/bundle-schema.md`). Reads nothing else — in particular,
never `robots` or `anchors`.

## Output

Zero to seven findings in the standard envelope (one per check, at most one occurrence
each — the checks are page-scoped internally, but each emits a single site-level verdict
per `docs/BUNDLE-SCHEMA.md`'s coverage walk). Emits `absent` explicitly wherever a check ran
clean, and `not_applicable` where an exclusion in the FP guard took the check out of scope
for this site (e.g. `CHK-D-005` on a legal-only archetype) — the negative-control evaluation
needs all three of "checked and clean", "excluded by rule", and "never ran" to be
distinguishable.

## Procedure

1. **Gate on evidence, per section.** If `pages.status != "ok"`, every check reading
   `pages[]` emits `not_determinable` with `pages.reason` and stops there. Same for
   `rendered.status` (gates `CHK-D-003` only) and `links.status` (gates `CHK-D-009` only).
   Never infer from a partial page set what the missing pages would have shown.
2. **Classify the site's rendering posture (`CHK-D-003`).** Compare the homepage's
   `pages[].main_text_words` / `h1_count`-from-`headings` against the matching
   `rendered[].main_text_words` / `h1_count`. This is a **definitional** check, not a
   threshold fitted to an effect size (see R-2 in `docs/research/EVIDENCE-LEDGER.md`): if
   the raw fetch has no h1 and under 50 words of main text while the render has ≥200, that
   content is categorically absent from what a non-rendering fetch receives.
3. **Evaluate `CHK-D-004`** (thin content) across the sampled static pages, conditioned on
   `page_type` (skip contact/login) and on `CHK-D-003`'s outcome — a JS-SPA whose thinness
   is explained by step 2 does not also get charged here.
4. **Evaluate `CHK-D-005`** (heading structure) on pages with ≥500 words, excluding
   legal/FAQ/minimal-content archetypes.
5. **Evaluate `CHK-D-009`** (broken internal links) from `links.results[]`, excluding
   entries in `links.skipped[]` (already filtered for robots-disallowed and fragment links
   by the collector).
6. **Evaluate `CHK-D-010`** (extractable-evidence density) by scanning `main_text` for a
   definition, a number with a unit, or an explicit comparison, on non-thin,
   non-informational pages. **Suppressed if `CHK-D-004` fired** — a page already flagged as
   too thin to extract from doesn't need a second, narrower content complaint.
7. **Evaluate `CHK-D-011`** (pronoun-saturated claims) on home/about pages, excluding
   narrative/blog page types where first-person or referential prose is the genre norm.
8. **Evaluate `CHK-D-013`** (near-duplicate templated content) via Jaccard similarity over
   `pages[].trigram_hash` across ≥3 pages, excluding legitimate variant and legal/ToS pages.
9. **Emit** the envelope for all seven checks, `present`/`absent`/`not_applicable`/
   `not_determinable` as evaluated above.

Full per-check detail — evidence strings, severity rules, FP guards, and suggested
actions — lives in [`references/checks.md`](references/checks.md), sourced directly from
`docs/research/EVIDENCE-LEDGER.md` so the two never drift silently out of sync.

## Executable checks

`scripts/render_extractability_checks.py` implements all seven checks — `evaluate(bundle)
-> list[envelope]`, run in the dependency order the procedure above requires (CHK-D-004
reads CHK-D-003's result; CHK-D-010 reads CHK-D-004's). CHK-D-013's near-duplicate
comparison runs directly on `pages[].main_text` rather than on `trigram_hash`: a single
hash of a whole trigram set can prove two pages identical or different, but cannot
produce a similarity *percentage*, which Jaccard requires — `docs/BUNDLE-SCHEMA.md`'s
claim that the hash alone "supports CHK-D-013's Jaccard comparison" doesn't hold up, and
`main_text` is already in the bundle at no extra cost, so the check uses that directly.

## Checks at a glance

| Check | Mechanism | Strength | Ceiling | Suppressed by (this skill) |
| --- | --- | --- | --- | --- |
| CHK-D-003 | C — JS-rendering gap | HARD-MECHANICAL | critical | — |
| CHK-D-004 | C — thin main content | CORRELATIONAL | medium | CHK-D-003 (JS-SPA case) |
| CHK-D-005 | B/C — absent/generic headings | THEORETICAL | low | — (archetype exclusion only) |
| CHK-D-009 | B — broken internal links | THEORETICAL/CORRELATIONAL | low | — |
| CHK-D-010 | B/C — low extractable-evidence density | CORRELATIONAL | medium | CHK-D-004 |
| CHK-D-011 | C — pronoun-saturated key claims | THEORETICAL/HEURISTIC | low | — (page-type exclusion only) |
| CHK-D-013 | C — near-duplicate templated content | CORRELATIONAL | medium (per element-count rule in the ledger's severity column: `low`) | — |

## False-positive discipline

The largest risk in this skill is treating "different from how a human reads it" as a
defect. Every check here is conditioned on page type or archetype (D-009) precisely because
a thin contact page, a deliberately narrative about-us page, or a legitimately duplicated
legal template is not a discoverability problem — it is normal. `CHK-D-003` is the one
exception deliberately built to need no such conditioning: its definitional trigger (no h1,
&lt;50 words raw, ≥200 rendered) is either true or it isn't, which is what makes it safe to
rate `critical` at all.
