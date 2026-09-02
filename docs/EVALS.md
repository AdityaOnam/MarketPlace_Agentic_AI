# Evaluation plan

How we measure whether the audit marketplace is any good. The organizers provide no test
set and no example sites, so this harness is entirely ours — and the rubric lines it must
answer are detection accuracy (few misses **and** few false positives), suggested-action
quality, output design, determinism, composition, and generalization.

## 0. Ground rules that apply to every metric

- **Unit of analysis is the site, not the finding.** Findings on one site are correlated;
  intervals are computed by **site-level cluster bootstrap** (10,000 resamples of sites with
  replacement), never by treating findings as independent.
- **Every number is reported as `point [lo, hi]`** at 95%. A metric computed on fewer than 10
  sites is reported as a raw count and explicitly not as a rate.
- **Correctness is never decided by an LLM judge**. Judges are used only for the subjective
  advice-quality rubric.
- **Everything is run against frozen snapshots.** Each corpus site is captured once (HTML,
  rendered DOM, response headers, robots.txt, screenshots, timing) into a content-addressed
  fixture. All grading, re-running and judging happens against the fixture.
- **Run manifest.** Every result row records: harness version, skill-bundle git SHA, corpus
  snapshot ID, rubric version, model + version for the audit, model + version for each judge,
  date, and wall-clock.

## 1. Gold-label protocol and agreement

Two independent labellers produce a gold finding list *before seeing any audit output*. 
Each labeller works from a fixed check taxonomy, recording one of:
- `PRESENT`: defect exists (requires `locus` and verbatim `evidence`)
- `ABSENT`: checked, site is clean (negative controls)
- `UNMEASURABLE`: signal cannot be observed read-only
- `N/A`: check does not apply to this archetype

**Agreement metric**: Krippendorff's alpha over the 4-category label, per check ID.
- Target: **>= 0.80**; provisional acceptance 0.67-0.80. Below 0.67 is cut from marketplace.
- 100% of `PRESENT` labels must have their evidence string found verbatim in the snapshot.

## 2. Detection metrics and matching rule

A predicted finding `P` matches a gold finding `G` iff all three hold:
1. **Same check class.** `P.id == G.id`
2. **Same locus.** Canonicalised URL matches, and either CSS selector matches or >= 0.6 token Jaccard on evidence.
3. **Grounded evidence.** `P.evidence` appears **verbatim** in the frozen snapshot.

**Severity handling**:
- Headline precision/recall are severity-blind.
- Severity mismatch is tracked via a confusion matrix and ordinal error.

**Metrics targets (per check ID and stratum)**:
- **Precision**: **>= 0.90** (checks <0.75 are removed).
- **Recall**: **>= 0.70** (checks <0.40 are cut or redefined).
- **Severity-exact rate**: **>= 0.75**.
- **Mean ordinal severity error**: **<= 0.4**.
- **Precision uplift**: Must exceed the stratum base rate.

## 3. False-positive control: negative controls and abstention

**Negative-control set targets**:
- Clean-site FP rate: **<= 0.05** per check (fails on >15%).
- Findings-per-clean-site: **<= 0.1**.

**Abstention targets (using `not_determinable`)**:
- Coverage at operating point: **>= 0.70**.
- Abstention precision (abstained and gold `UNMEASURABLE`): **>= 0.60**.
- ECE over confidence bins: **<= 0.10**.

## 4. Suggested-action quality

Scored via atomic binary criteria, never a 1-5 score. Checked by a panel of 3 judges from 3 distinct model families.
1. **Targeted**: Addresses specific locus?
2. **Mechanism-sound**: Supported by research?
3. **Specific enough to execute**: Actionable by non-expert?
4. **Correctly prioritised**: Consistent with severity?
5. **Non-manipulative**: Avoids gaming AI retrieval?

Targets:
- Mean criteria-met fraction: **>= 0.80**.
- Criterion 5 (non-manipulative) pass rate: **1.00** (blocking defect).
- Panel-vs-human agreement: Within **10 pp**.
- Position-swap flip rate: **<= 0.05**.

## 5. Determinism and stability

Run frozen snapshot **k = 5** times.
- **Set stability**: **>= 0.90** of sites have identical set of (check_id, locus).
- **Severity stability**: **>= 0.85** have identical severities.
- **Full-report stability**: **>= 0.80** have identical ordering and counts.

## 6. Held-out generalization

Sites partitioned into `dev` and `held-out` before any skill is written. Held-out contains an archetype never used in dev.
- Held-out set run **at most 3 times**. Logged in `docs/evals/holdout-log.md`.
- Held-out precision: Within **10 pp** of dev precision.
- Held-out clean-site FP rate: **<= 0.10**.
- Unseen-archetype recall: **>= 0.50**.

## 7. Composition value (ablations)

Run `n + 1` configurations (full system, full-minus-one for each skill).
- Composite drop when skill removed: **> 0** (skill must earn its place).
- Pairwise unique-contribution: Each skill contributes **>= 10%** unique findings.
- Direction check: No skill whose removal improves the composite.

## 8. Runtime and cost

Measured against the 5-minute budget.
- p50 wall-clock: **<= 150 s**.
- p95 wall-clock: **<= 270 s**.
- Worst case (large site + headless): **<= 300 s**, or a graceful partial report.
- Zip size: **<= 50 MB**.

## Standing commitments

- Gold labels are written **before** looking at the audit's output.
- The held-out set is run at most a pre-declared number of times.
- Every reported metric carries a confidence interval.
- Negative results are recorded; failed checks are removed, not softened.
