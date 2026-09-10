# Evaluation plan

How we measure whether the audit marketplace is any good. The organizers provide no test
set and no example sites, so this harness is entirely ours — and the rubric lines it must
answer are detection accuracy (few misses **and** few false positives), suggested-action
quality, output design, composition, and generalization.

**This is the reduced protocol adopted as D-017 on 2026-09-04.** It replaces the D-010
harness, which was sized for two independent labellers and unlimited wall-clock. What was
cut, and why each cut is a real loss rather than a rebrand, is in D-017 and summarised in
§9 below. Read that section before quoting any number from this document.

## 0. Ground rules that apply to every metric

- **Unit of analysis is the site, not the finding.** Findings on one site are correlated;
  intervals are computed by **site-level cluster bootstrap** (10,000 resamples of sites with
  replacement), never by treating findings as independent.
- **Every number is reported as `point [lo, hi]`** at 95%. A metric computed on fewer than 10
  sites is reported as a raw count and explicitly not as a rate.
- **Correctness is never decided by an LLM.** A model may run as a disagreement-finder
  (§1), but no model output ever becomes a gold label. Judging is confined to the
  subjective advice rubric in §4.
- **Everything is run against frozen snapshots.** Each corpus site is captured once (HTTP
  response, headers, robots.txt) into a content-addressed fixture. All grading, re-running
  and judging happens against the fixture. Snapshots no longer contain a rendered DOM or
  screenshots — per D-015 there is no headless browser in the grading sandbox, so a
  rendered capture would measure a code path that never executes when it counts.
- **Sample, not population.** The corpus is hand-picked under a recorded stratification
  rule (D-017.6). Every reported number estimates performance **on a sample we chose**, not
  a population rate. This sentence travels with the numbers.
- **Run manifest.** Every result row records: harness version, skill-bundle git SHA, corpus
  snapshot ID, rubric version, model + version for the audit, model + version for any
  disagreement-finder pass, date, and wall-clock.

## 1. Gold-label protocol

**One labeller.** Gold finding lists are produced *before seeing any audit output*, from a
fixed check taxonomy, recording one of:

- `PRESENT`: defect exists (requires `locus` and an `evidence` note pointing at what was read)
- `ABSENT`: checked, site is clean
- `UNMEASURABLE`: signal cannot be observed read-only
- `N/A`: check does not apply to this archetype

**Reproducibility metric — intra-rater test–retest.** A random 8-site subset is re-labelled
**≥ 48 h later, blind to the first pass**. Agreement is Krippendorff's alpha over the
4-category label, per check ID, first pass vs second.

- A check that cannot reach **α ≥ 0.67 against the labeller's own second pass** is cut. A
  check nobody can reproduce — including its own author — is not a check.
- Every `PRESENT` label must cite evidence the labeller actually read in the snapshot.
  *(Until 2026-09-10 this read "100% of `PRESENT` labels must have their evidence string
  found verbatim in the snapshot." Gold evidence in practice is a summary — `"144 words"`,
  `"canonical.href is null"` — not a quotation, so the literal form was never met by the
  gold data either. See D-028.)*

**What this buys and what it does not.** Test–retest is evidence the rubric is *applied
consistently*. It is not evidence the rubric is not *systematically misread*, which is what
a second independent labeller would have bought. **Both recall and precision are exposed to
that.** Until 2026-09-10 this paragraph claimed precision was largely protected "because
every match is separately verified verbatim against the snapshot (§2.3)" — D-028 removed
that verification from the matching rule, so the protection it claimed no longer exists.
What remains is the reported grounding rate (§2), which discloses the exposure rather than
removing it. This limitation is reported alongside both numbers, not footnoted.

**Disagreement-finder (optional, non-authoritative).** A model may re-read the snapshots
and flag check/site cells where it disagrees with the human label. Its output is a
**queue for human adjudication**, never a label and never an input to any agreement
statistic. Its value is catching human oversight on recall; using it as a second rater
would make the agreement number measure only that two similar systems agree.

## 2. Detection metrics and matching rule

A predicted finding `P` matches a gold finding `G` iff both hold:

1. **Same check class.** `P.id == G.id`
2. **Same locus.** Canonicalised URL matches, and either CSS selector matches or ≥ 0.6 token
   Jaccard on evidence.

> **Condition 3 was removed on 2026-09-10 (D-028).** It read: *"Grounded evidence. `P.evidence`
> appears **verbatim** in the frozen snapshot."* It was unsatisfiable by construction — every
> one of the 26 checks emits `evidence` as constructed prose describing the defect
> (`"robots.txt line 120: Disallow: / applies to Applebot (retrieval-time AI crawler)"`),
> never as a copy-pasted excerpt of the source, so no prediction could ever satisfy it. In its
> first real run it forced every match to `False` and pinned **all 26 checks at precision 0.00
> and recall 0.00** — measuring evidence-writing style, not detection accuracy.
>
> This is a **loosening of the matching rule, in the direction this document's own §5 warns
> about**: we author both the checks and the gold labels, so a weaker matcher flatters us. The
> mitigation is that the removed gate is still computed. `harness/score_dev.py` reports, per
> check, what fraction of its matches *would* have passed the verbatim test, printed on the
> line under precision. The guard is demoted from gate to disclosure, not deleted — so the
> number that benefits from the loosening always appears next to the measure of how much
> loosening it took.

**Severity handling.** Headline precision/recall are severity-blind; severity mismatch is
tracked in a confusion matrix and as ordinal error, and never breaks or grants a match.

**Targets (per check ID and stratum):**

| Metric | Target | Cut rule |
| --- | --- | --- |
| Precision | ≥ 0.90 | check removed below 0.75 |
| Recall | ≥ 0.70 | check cut or redefined below 0.40 |
| Severity-exact rate | ≥ 0.75 | — |
| Mean ordinal severity error | ≤ 0.4 | — |
| Precision uplift | must exceed the stratum base rate | — |

## 3. False-positive control

**The headline clean-site FP rate comes from the `ABSENT` labels on the dev corpus**, where
every check receives a per-site verdict. Target: **≤ 0.05 per check**; a check firing on
more than 15% of sites labelled `ABSENT` for it is cut.

**The negative-control set is a screen, not a measurement.** Each negative-control site is
curated clean on *one named dimension*, so it can only test the checks in that dimension —
1–3 observations per check-dimension cell. That is enough to catch a check that fires on
every clean site and not enough to separate 0.05 from 0.15. It runs **first** because it is
the cheapest possible refutation, and it reports **counts, never rates**. A firing outside
a site's curated dimension goes to the adjudication queue, not to a score.

**Abstention** is reported descriptively: `not_determinable` envelopes per site, per check.
No target, no calibration metric. D-010's ECE-over-confidence-bins was specified against a
probabilistic system; these checks emit discrete states and have no bin to calibrate.

## 4. Suggested-action quality

Scored via atomic binary criteria, never a 1–5 score:

1. **Targeted** — addresses a specific locus
2. **Mechanism-sound** — supported by the cited research
3. **Specific enough to execute** — actionable by a non-expert
4. **Correctly prioritised** — consistent with assigned severity
5. **Non-manipulative** — does not game AI retrieval

Scored by a **single-model pass**, plus a **human read of the complete advice set on 5
sites**. (D-010's 3-model-family panel is cut: a judge panel exists to make a subjective
score trustworthy, and we cannot afford the human anchor that would validate the panel. An
unvalidated panel is not more trustworthy than an honest single pass with a human read.)

Two criteria are mechanical and hard:

- **Criterion 5 at 1.00, blocking.** Already implemented in `meta_evaluate`'s
  prohibited-recommendation scan against D-007's list.
- **Action-locus coherence.** Every finding's suggested action must name the locus of its
  own finding. The officials called out disconnected fixes explicitly
  (`OFFICIALS-QA.md` §3.4); this makes it a check rather than an aspiration.

Target: mean criteria-met fraction ≥ 0.80.

## 5. Stability and conformance

**Schema conformance is the gate: 100%, every run.** Every emitted report must validate
against `report-schema.md`. This replaces `pass^k` as the pass/fail line because it is what
is actually graded — "we are not looking for deterministic standard output as in what
output you produce; it is the structure that you need" (`OFFICIALS-QA.md` §2.1).

**Set stability is reported, not gated.** Measured once at **k = 3 on 5 sites**, reported as
counts of sites whose (check_id, locus) set is identical across all three runs. No
threshold, and it may not drive an architecture decision. The three named instability
sources remain worth watching in that count: evergreen-vs-time-sensitive classification,
archetype labelling, and suggested-action wording.

## 6. Held-out generalization

12 sites, drawn by the same procedure and strata as dev, **selected and sealed before the
harness is built**.

- **Total run budget: 3 looks**, each logged in `docs/evals/holdout-log.md`.
- Any inspection beyond the aggregate metric converts that site to dev, permanently.
- Held-out precision within **15 pp** of dev precision.
- Held-out clean-site FP rate ≤ 0.10.

**What 12 sites buy:** detection of a *collapse* (0.90 → 0.60), not of a 10 pp drift. The
interval is roughly ±15 pp. Stating this is the point; a tighter claim from 12 sites would
be false precision.

## 7. Composition value

Two tests, in increasing order of how much they can embarrass the design. **Both have now
run** (2026-09-04, D-025) — see `docs/ARCHITECTURE.md` §7 and `docs/DECISIONS.md` for the
full results; this section keeps the protocol description, not the outcome.

1. **Leave-one-skill-out ablation**, at matched token budget. **Reported, not gated** —
   `ARCHITECTURE.md` §7 is explicit that any disjoint partition passes this, because
   removing a skill mechanically removes its checks. Run via `harness/ablation.py` against
   the 36-site dev+negative corpus: the raw per-skill count is as expected, and the sharper
   version (does removing the skill owning `CHK-D-003` change what `CHK-E-019` does) found
   O-1 never fired on any real site — the result that motivated the merge below.
2. **The merge test**, the deciding one. D-016 already reduced the orchestrator's genuine
   cross-skill surface to a single rule (O-1) connecting exactly one pair of analysers, and
   the ablation above found that rule never fired on real data. `render-extractability-audit`
   and `engagement-defect-audit` were merged into `content-engagement-audit` and re-run
   against all 42 available sites: findings, loci, and severities came back byte-identical
   to the pre-merge two-skill output, and schema conformance and runtime were unaffected.
   The boundary bought nothing measurable — merged for real, not left as a hypothetical.
3. **Bundle-sufficiency**: each analyser must run to completion on the bundle alone with
   the network disabled. Any analyser needing a fetch has the wrong boundary. Held before
   and after the merge — checked by grep, zero networking imports in any analyser script.

## 8. Runtime

Measured against the 5-minute wall-clock cap, which per `OFFICIALS-QA.md` §1.3 **includes
model inference**.

- p50 wall-clock ≤ 150 s
- p95 wall-clock ≤ 270 s
- Worst case ≤ 300 s, or a graceful partial report
- Zip size ≤ 50 MB

## 9. What this protocol cannot tell us

Stated here so it cannot be quietly dropped between here and the report:

| Limitation | Consequence |
| --- | --- |
| One labeller | Systematic misreading of the rubric is undetectable. Recall is the exposed number |
| 24 dev sites | Recall interval ≈ ±12 pp — our weakest number |
| 12 held-out sites | Detects a collapse, not a 10 pp drift (≈ ±15 pp) |
| Hand-picked corpus | Estimates performance on a chosen sample, not a population rate |
| Negative controls at 12 sites | A screen. Counts only. Cannot establish an FP *rate* |
| No rendered snapshots | Six render-dependent checks are unmeasurable by construction, disclosed via `degraded_stages[]` rather than evaluated |

## Standing commitments

- Gold labels are written **before** looking at the audit's output.
- The held-out set is opened at most 3 times, and every look is logged.
- Every reported metric carries a confidence interval, or is reported as a count.
- Negative results are recorded; failed checks are removed, not softened.
- **Asymmetric justification** (D-010, retained): any change to matcher, rubric, or
  composite that *raises* scores requires written justification plus a negative-control
  re-run in the same commit. Score-lowering changes do not.
- **A finding we cannot reproduce is a bug, not a finding.**
- **Prefer cutting a check to shipping one we cannot defend.**
