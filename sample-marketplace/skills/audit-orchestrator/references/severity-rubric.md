# Severity & priority rubric

Applied verbatim so two runs on the same site produce the same ranking.
Severity = *how bad the problem is*. Priority = *how urgently to act*, which
also weighs effort.

## Severity

Severity is the **layer** the failure sits in, adjusted by **breadth**.

### Base severity by layer

| Layer | Meaning | Base |
|---|---|---|
| L0 — Access | Machine cannot reach the page at all (blocked, 5xx, redirect loop) | `critical` |
| L1 — Readability | Reachable but content is not in retrievable text (JS-only, image-only, PDF-only) | `high` |
| L2 — Extractability | Readable but facts are not cleanly attributable (no schema, no headings, buried claims) | `medium` |
| L3 — Identity & trust | Extractable but entity is ambiguous, stale, or uncorroborated | `medium` |
| L4 — Engagement | Fine for machines, weak for humans (orientation, next steps, context) | `medium` |

The ordering encodes the causal chain from the Round-2 appendix: a failure at
L0 makes everything below it irrelevant, so it always outranks a richer-sounding
L2 finding.

### Breadth modifier

| Share of sampled pages affected | Adjustment |
|---|---|
| ≥ 80% or affects a primary template (home/product/pricing) | +1 level |
| 30–79% | no change |
| < 30% and no primary template | −1 level |

Clamp to `critical … low`. A finding with confidence `low` may not exceed
`medium`.

### Money-page rule

If the affected page is the homepage, a product/pricing page, or the page a
brand-name query would land on, never assign below `high` for L0/L1 failures.

## Priority

`priority = severity`, then adjust once:

| Condition | Adjustment |
|---|---|
| Fix is `effort: low` (config, one meta tag, one JSON-LD block) | +1 level |
| Fix is `effort: high` (re-platform, SSR migration, content rewrite) and severity ≤ `medium` | −1 level |
| Finding is `proactive: true` | cap at `medium` |

Rationale: a cheap fix for a medium problem should be done before an expensive
fix for a slightly worse one.

## Confidence

| Level | Use when |
|---|---|
| `high` | Directly observed on ≥ 3 pages, or a definitive single artefact (`robots.txt` line, HTTP status). |
| `medium` | Observed on 1–2 pages, or inferred from a strong proxy signal. |
| `low` | Heuristic or sample too small. **Report it, but say so in evidence, and cap severity at `medium`.** |

## Guarding against false positives

The rubric is worth nothing if the checks over-fire. Before emitting:

1. **Sample size gate.** No sitewide claim from < 3 pages. Say
   `"3/3 sampled"`, never `"the whole site"`.
2. **Site-type gate.** Do not flag missing `Product` schema on a site with no
   commerce signals; do not flag a thin homepage on a single-page brochure
   site whose content is genuinely one page.
3. **Intentionality gate.** A `Disallow: /admin` is correct behaviour, not a
   finding. Only flag disallows that cover content pages.
4. **Alternative-satisfaction gate.** If the goal is met another way (facts in
   clean semantic HTML instead of JSON-LD), downgrade to `low`/`info` and say
   so, rather than flagging the missing mechanism.
5. **Observation gate.** If you did not observe it, it is not a finding.
