# Stage B and B′ — first contact with real websites

Run 2026-09-04. This is the first time anything in this project was executed against a live
site; every accuracy property claimed before today was a design argument tested on synthetic
bundles.

**Sets run:** 12 negative-control sites, 24 dev sites. Held-out remains sealed and was not
touched (`holdout-log.md` records zero looks). Adversarial not yet run.

**What may be concluded from these numbers:** that a check misfires, and why. **What may
not:** any rate. The negative-control set is a screen (`EVALS.md` §3), the dev corpus has no
gold labels yet, and the corpus is hand-picked (`corpus-selection.md`).

---

## 1. Headline

| | Before Stage C fixes | After |
| --- | --- | --- |
| Findings across the 12 clean sites | 356 | **107** |
| Sites firing inside their own curated clean dimension | 8 / 12 | **7 / 12** |
| `CHK-D-027` firings on clean sites | 6 / 12 | **0 / 12** |
| Archetype accuracy (36 sites) | 22% | **17%** |
| Schema conformance | 12/12 | **36/36** |
| Harness crashes | 4 sites | **0** |

The finding-count collapse is the result that matters most, and it is not a detection
improvement — it is a *reporting* one. Roughly half came from repairing four false-positive
mechanisms (D-020) and half from no longer printing one site-template defect once per page
(D-019).

## 2. Five crashes, in shipped code

The audit is required to "produce a valid bundle with the affected sections marked partial
or unavailable — **never an exception**". It raised on 4 of the first 36 real sites.

| Crash | Cause | Fix |
| --- | --- | --- |
| `RecursionError` ×3 call sites | `html_tree.find_all`, `_strip_boilerplate_text` and `_extract_headings` each recursed once per DOM level; one real site produced a ~1000-deep tree | All three traversals made iterative |
| `AttributeError: 'list' has no attribute 'lower'` | `@type` in JSON-LD is legitimately a string *or* an array; `_organization_blocks` assumed a string. Took down four checks at once | `_org_type_names` normalises both |
| `ValueError: unknown url type` | A site serves `{{ site.url }}/sitemap.xml` — an unrendered template left in its published robots.txt | `Sitemap:` values validated as absolute URLs before use |

None of these are exotic. They are a deep DOM, an array-valued schema.org type, and a
templating bug on someone else's server. Three of the five were in the collector, which is
the component every other skill depends on.

## 3. The negative-control screen

Seven of twelve curated-clean sites still fire inside their own clean dimension. Each was
traced to the site's actual HTML rather than judged in aggregate, and the traces fall into
three groups — the split is more useful than the count.

**(a) The check was right; our curation was wrong.** `CHK-D-007` (missing Organization
JSON-LD) fired on two sites listed as clean on `entity_identity`. Fetching them found
**zero** `application/ld+json` blocks on one. The row was an assumption, never verified.
Logged as a rejection.

**(b) Real, if minor, defects on genuinely well-built sites.** `CHK-E-014` and `CHK-E-022`
still fire on both accessibility exemplars — one unnamed link in a shared header, one page
with no `h1`, one page missing `<main>`. Verified true. **The lesson is about the corpus
design, not the checks:** no real site is perfectly clean on a whole dimension, so "curated
clean" can never be more than "clean enough to be a strong prior". This is a further reason
the set is a screen and not a measurement.

**(c) Genuine false-positive mechanisms — four found and repaired (D-020).** All four are in
D-020; the pattern worth repeating here is that **three of the four lived in the collector,
not in any analyser.** `engagement-defect-audit/SKILL.md` had documented the correct guard
for the alt-text case for months ("test `alt === null`, not `!alt`") and no analyser could
ever have implemented it, because `<img alt>` and `<img>` had already been flattened to the
same value upstream. A false-positive guard is worth nothing if the evidence reaching it has
lost the distinction the guard depends on.

### Still open, ranked by exposure

| Check | Exposure | Assessment |
| --- | --- | --- |
| `CHK-E-021` (images without dimensions) | 10/12 clean sites | Near-universal on the real web, `THEORETICAL` strength, `medium` severity. **The weakest surviving check.** Cut, or demote to `recommendations[]`, in Stage C |
| `CHK-E-022` (no `h1` / no `<main>`) | 10/12 | Individually true; fires everywhere. Candidate for severity demotion |
| `CHK-D-007` (no Organization JSON-LD) | 9/12 | Genuinely absent on most sites. Real, but "everyone fails it" needs base-rate conditioning per D-009 |
| `CHK-E-014` | 9/12 | Much improved after the decorative-image fix; the residue is real |
| `CHK-D-004` / `CHK-D-010` on a documentation site | 1 each | `D-004` flagged a 197-word landing page as thin; `D-010` claimed a documentation site contains no definitions. Both need investigating before gold labelling |

## 4. Stage B′ — the archetype classifier: 17%

**6 of 36 correct. 25 of the 30 misses are `unknown`; 5 are confident wrong labels.**

This is the most consequential result of the day, because `archetype` is not a finding — it
is an *input to suppression*, so its errors propagate instead of staying local. It also
gates the vertical-specific insight the officials named as a differentiator
(`OFFICIALS-QA.md` §3.3).

Two mechanical causes were found and fixed:

1. **The proportion rules were reading the wrong population.** "≥40% of the site is
   documentation" was evaluated against the *fetched sample*, which `select_static_sample`
   deliberately stratifies and caps at 4 per page type. A stratified sample cannot preserve
   the proportion the rule asks about — the sampler exists to flatten it. Now computed over
   the discovered inventory.
2. **A blocked site was being labelled confidently.** With zero pages fetched, the
   `total <= 5 → brochure` fallback labelled sites that had simply refused us. Now
   `unknown`.

Neither fix moved the number, because the dominant cause is upstream of both:
`classify_page_type` returns `other` for most real URLs. Its path patterns were written
against idealised URL shapes; on real sites 190 of 200 documentation URLs were labelled
`other` because the paths are `/templates/`, `/getting-started/`, `/content-management/`.

**Tuning stopped here deliberately.** Further pattern work against these same 36 sites would
be fitting the classifier to the corpus — the exact failure the asymmetric-justification
rule exists to prevent. The number stands at 17% and the decision is escalated as **D-021**.

Mitigating, and worth stating precisely: `unknown` is **safe by design** — it suppresses
every archetype-conditioned check, so the dominant failure mode costs *capability*, not
correctness. The five confident wrong labels are the dangerous ones, and they are the whole
of the correctness risk here.

## 5. Runtime

Wall-clock is **not** yet a valid measurement of the marketplace. The harness enforces a 1.0
s per-host gap — four times the collector's own 250 ms floor — because politeness on someone
else's server matters more than our benchmark. One live collection took 1033 s under that
gap. Replayed from frozen snapshots, p50 is 2.7 s and max 12.7 s, which bounds the
*analysis* cost but not the fetch cost.

A real p50/p95 against the 300 s cap needs a run at the collector's declared budget, and is
outstanding.

## 6. What Stage B did not do

- **No gold labels exist.** No precision, recall, or clean-site FP *rate* has been measured,
  and none may be quoted. That is Stage D.
- **Held-out is untouched**, 3 looks intact.
- **Adversarial set not run.**
- **R-1 (hand-verification of one source per check) remains open** and still blocks ship.
