# Website corpus

Development and held-out test sets of real websites. We are graded on unseen sites, so
the corpus exists to do two jobs: give us enough variety to *derive* generalizable checks,
and give us an untouched set to *measure* whether they generalized.

## Structure the corpus will take

| Set | Purpose | Hygiene rule |
| --- | --- | --- |
| **Dev** | Derive and tune checks; look at freely | 60 sites. Used for discovery. Gold labels needed on only 20. |
| **Held-out test** | Measure generalization | 30 sites. Pre-declared budget of 3 runs. Peeking converts a site to dev. |
| **Negative control** | Measure false positives | 24 sites (3 per check family). A check firing here is a defect. |
| **Adversarial / edge** | Measure graceful degradation | 12 sites (1 per edge condition). Must not crash or hallucinate. |

## 0. Design commitments

1. **The unit of analysis is the site, not the finding.** Findings within a site are correlated. All confidence intervals are computed with a site-level clustering correction.
2. **Sampling frames are pinned, never live.** Frames are committed with their list ID and date.
3. **Every eval run is against a frozen local snapshot we captured ourselves.** Storing both the raw HTTP response (WARC-equivalent) and the rendered DOM. The Wayback Machine is **not** used for this.
4. **Dev and held-out are drawn by the *same* procedure from the *same* strata.**
5. **No site name, brand, or selector from this corpus may appear in any shipped `SKILL.md` or script.** 

## 1. Dev corpus

**Size: 60 sites.**

**Stratification (6 x 3 design):**
- **Archetypes (10 sites each):** E-commerce/product catalogue, Documentation/knowledge base, SaaS/product marketing, News/editorial/blog, Local business/services, Portfolio/brochure/one-pager.
- **Popularity Tiers:** Within each archetype: 3 head (≤ 10k), 3 mid (10k–200k), 4 tail (> 200k or not on Tranco). 

**Secondary balance constraints:**
- ≥ 15 JS-rendered sites.
- ≥ 12 non-English sites (≥ 4 languages, ≥ 2 non-Latin scripts).
- ≥ 10 sites outside US/UK/EU.
- ≥ 20 mobile-first/responsive-only.
- Max 3 sites on any single CMS/platform.

**Procedure:**
1. Pin frames: Tranco list ID (popularity) and Common Crawl domain graph (for the long tail). The Online-Mind2Web list is dev-eligible-only.
2. Walk the shuffled list (recorded seed). Fetch home page, AI-assist label the archetype (human confirms).
3. Fill quotas, keeping a rejection log.
4. Freeze via snapshot. Commit `corpus/dev.csv`.

## 2. Held-out test corpus

**Size: 30 sites.** Drawn in the same pass as dev, maintaining archetype and tier proportions.

**Hygiene rules:**
- Stored separately (`corpus/heldout.enc.csv`). Labels not read during development.
- **Total run budget: 3 runs.** Pre-declared and logged in `DECISIONS.md`.
- Any manual inspection of a held-out site's pages or per-finding results beyond the aggregate metric immediately converts that site to dev.

## 3. Negative-control set

**Size: 24 sites** (3 sites for each of the 8 evaluation dimensions).

Sites that are explicitly verified as clean on a given dimension (e.g., has perfect structured data, has no accessibility violations, is explicitly evergreen). Any firing of a check on its corresponding negative-control site is treated as a hard defect.

## 4. Adversarial / edge set

**Size: 12 sites** (1 per condition).

Conditions include: JS-only SPA, robots.txt blocking `/`, robots.txt `Crawl-delay`, single-page site, very large site, non-English/non-Latin script, paywalled, parked domain, bot cloaking, challenge pages, slow origin, redirect chains.

**Requirement:** The skill must terminate within 5 minutes, emit valid JSON, and handle the failure gracefully (`not_determinable` or omitting checks).

## 5. Snapshotting and reproducibility

Live sites change. Every eval runs against a capture.
- Store raw HTTP response (status, headers, body).
- Store rendered DOM after JS execution.
- Store metadata (timestamp, UA, IP, robots.txt).
- Max 100 pages per site.

## 6. Sample size and confidence intervals

- We report precision and recall as **Wilson score intervals**, never Wald.
- Intervals correct for site-level clustering using a design effect (DEFF).
- With 30 held-out sites, the interval on precision (at p=0.90) will be roughly ±6 percentage points. 

## 7. Shipping constraints

- The final ≤50 MB zip contains **only** the skills and generic reference data.
- It contains **nothing derived from a specific site** (no snapshots, no lists).
- The raw/rendered snapshots stay local and are git-ignored.
