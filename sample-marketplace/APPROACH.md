# Approach

## The core idea: audit the causal chain, not a checklist

The Round-2 appendix describes a strict sequence — a crawler must be **let in**,
must be able to **read** the page, and must be able to **pick out the fact**.
Everything the marketplace does is organised around that chain, extended with
trust and then with the human:

```
L0 Access        Can a machine reach it?            robots, status, noindex
L1 Readability   Is content in the raw response?    JS-render gap, non-text
L2 Extractability Can one clean fact be lifted?     schema, headings, prose
L3 Identity      Is it clear WHO this is?           entity, sameAs, freshness
L4 Engagement    Will a human who lands stay?       orientation, next step
```

Two consequences fall straight out of this, and they are the whole design:

1. **Severity is layer position, not check type.** A blocked crawler always
   outranks a missing FAQ schema, because failing L0 makes L2 unobservable.
2. **Skill boundaries are layer boundaries.** Each skill owns one layer, so
   every finding has exactly one home. That is genuine separation of concerns
   rather than five folders holding one idea.

## Why this generalises to unseen sites

The rubric's hardest criterion is generalization, so every check is written as
a **structural invariant**, never a site fingerprint:

- ❌ "flag sites built with Next.js"
- ✅ "flag any page whose raw HTML holds < 150 words while loading 5+ scripts,
  observed on ≥ 3 pages"

The second one has no idea what framework it is looking at. It measures the
*consequence* — the gap between what the browser shows and what the fetcher
gets — which is the thing that actually breaks retrieval. Every check is
phrased as an observation with a threshold and a sample size.

## Avoiding false positives (worth as many points as detection)

The rubric penalises over-flagging explicitly. Five gates apply before any
finding is emitted:

| Gate | Rule |
|---|---|
| Sample size | No sitewide claim from < 3 pages. Evidence always says `n/m sampled`. |
| Site type | No `Product` schema finding on a site with no commerce signals. |
| Intentionality | `Disallow: /admin` is correct behaviour, not a defect. |
| Alternative satisfaction | Facts in clean semantic HTML instead of JSON-LD → downgrade, don't flag. |
| Observation | If it was not observed, it is not a finding — it goes in `checks_not_assessed`. |

That last gate is why the orchestrator refuses to run downstream checks when
Layer 0 fails, instead of inventing plausible-sounding ones.

## Evidence discipline

Evidence is what separates an audit from an opinion. Every finding must cite a
**counted observation**: status codes, `n/m` ratios, quoted markup, named URLs.

- ✅ `"5/8 sampled pages return <150 words while loading 12+ scripts; /pricing returns 38 words and an empty <div id=\"__next\">."`
- ❌ `"The site relies too heavily on JavaScript."`

## Suggested actions carry a mechanism

The rubric asks for fixes that are "mechanism-sound". So every action ships
with a `mechanism` field explaining the causal chain from fix to outcome, plus
concrete `steps`, an `effort` estimate, and a `verify` line. Priority is then
severity adjusted by effort — a cheap fix for a medium problem should be done
before an expensive fix for a slightly worse one.

## Beyond-defect recommendations

`proactive-playbook.md` holds ten recommendations that fire even when nothing
is broken (quotable facts page, `sameAs` identity graph, off-site
corroboration, visible freshness dates, answer-first FAQs, context retention in
URLs). These are emitted as `info` + `proactive: true` so they are visibly
distinct from detected defects, and are skipped when a real finding already
covers the same ground.

## Engineering choices

- **stdlib only.** No pip install, nothing to resolve at runtime, no model
  weights — portable and well under 50 MB.
- **One crawl, all checks.** `lib/fetch_lib.py` fetches the page set once and
  every check reads the same set. Keeps the audit polite and inside 5 minutes.
- **Deterministic.** Fixed sort keys and fixed thresholds — same site, same
  report, every run.
- **Fail-soft.** A skill that errors or times out is recorded in
  `scope.checks_not_assessed`; it never takes the audit down.
- **Skills are additive.** Adding a skill means one row in `CHECK_SCRIPTS` and
  one entry in `marketplace.json` — no orchestrator logic changes.

## Remaining work for the full submission

The two extra skills follow the identical shape:

- **`structured-data-extraction`** (L2) — JSON-LD presence, parse validity,
  schema-type appropriateness for the page type, agreement between markup
  values and visible text, heading-tree sanity, facts locked in images/PDFs.
- **`entity-identity-corroboration`** (L3) — is the legal/brand name stated
  unambiguously, is there an `Organization` block with `sameAs`, do off-site
  sources corroborate the core facts, are dated pages stale, is the name shared
  with other entities (disambiguation risk).
