# 07 — Evaluation Q&A

How we know whether any of this works. The organizers provide no test set and no example
sites, so the whole harness is ours.

Sources: `docs/EVALS.md` (protocol), `docs/evals/stage-e-report.md` (results),
`docs/CORPUS.md` (the sites).

---

## A. Protocol

### Q1. What are the six ground rules that apply to every metric?

**A.**
1. **Unit of analysis is the site, not the finding** — findings on one site are correlated;
   intervals come from a site-level cluster bootstrap (10,000 resamples with replacement).
2. **Every number is `point [lo, hi]` at 95%.** A metric on fewer than 10 sites is reported
   as a **raw count**, never a rate.
3. **Correctness is never decided by an LLM.** A model may run as a disagreement-finder, but
   no model output ever becomes a gold label.
4. **Everything runs against frozen snapshots** — one content-addressed fixture per site.
5. **Sample, not population** — the corpus is hand-picked under a recorded stratification
   rule, so every number estimates performance *on a sample we chose*. **That sentence travels
   with the numbers.**
6. **Run manifest** — every result row records harness version, skill-bundle git SHA, corpus
   snapshot ID, rubric version, models used, date, wall-clock.

### Q2. What is the gold-label taxonomy?

**A.** Four closed values per (site, check) cell, written **before** seeing any audit output:
`PRESENT` (with a locus and an evidence note pointing at what was read), `ABSENT` (checked,
clean), `UNMEASURABLE` (not observable read-only), `N/A` (does not apply to this archetype).

### Q3. How many labellers, and what does that cost?

**A.** **One.** The cost is stated rather than hidden: test–retest is evidence the rubric is
*applied consistently*; it is **not** evidence the rubric is not *systematically misread*,
which is what a second independent labeller would have bought. **Both recall and precision are
exposed to that.** The limitation is reported alongside both numbers, not footnoted.

### Q4. What is the reproducibility metric, and has it run?

**A.** Intra-rater test–retest: re-label a random 8-site subset ≥48 h later, blind, and compute
**Krippendorff's α** over the 4-category label per check. A check that cannot reach **α ≥ 0.67
against the labeller's own second pass is cut**. **It has not yet run** — the apparatus is
built and the subset drawn, but the second pass must be done by hand. Until it runs, **no cut
rule may be acted on**: a check is cut on a reproducible number, not a single pass.

### Q5. What is the matching rule?

**A.** A predicted finding `P` matches a gold finding `G` iff (1) same check class
(`P.id == G.id`) **and** (2) same locus — canonicalised URL matches, and either the CSS
selector matches or evidence token-Jaccard ≥ 0.6.

### Q6. What was condition 3, and why was it removed?

**A.** *"Grounded evidence — `P.evidence` appears verbatim in the frozen snapshot."* It was
**unsatisfiable by construction**: every check emits constructed prose describing the defect,
never a copy-pasted excerpt. In its first real run it forced every match to `False` and pinned
**all 26 checks at precision 0.00 and recall 0.00** — measuring evidence-writing style, not
detection accuracy. Removed as D-028.

### Q7. Isn't removing a gate exactly the self-serving change the protocol warns about?

**A.** Yes — and it is labelled as such in the document itself: *"This is a loosening of the
matching rule, in the direction this document's own §5 warns about."* The mitigation is that
**the removed gate is still computed and printed**. `score_dev.py` reports, per check, what
fraction of its matches *would* have passed the verbatim test, on the line under precision.
The guard was demoted from gate to disclosure, not deleted — so the number that benefits from
the loosening always appears next to the measure of how much loosening it took.

### Q8. What are the targets and cut rules?

| Metric | Target | Cut rule |
| --- | --- | --- |
| Precision | ≥ 0.90 | check removed below 0.75 |
| Recall | ≥ 0.70 | check cut or redefined below 0.40 |
| Clean-site FP rate | ≤ 0.05 | check cut above 0.15 |
| Severity-exact rate | ≥ 0.75 | — |
| Mean ordinal severity error | ≤ 0.4 | — |
| Held-out precision | within 15 pp of dev | — |
| Suggested-action criteria met | mean ≥ 0.80 | — |
| Schema conformance | **100%, every run — the gate** | — |

### Q9. How is suggested-action quality scored?

**A.** Five **atomic binary criteria**, never a 1–5 score: targeted, mechanism-sound, specific
enough for a non-expert to execute, correctly prioritised, non-manipulative. Scored by a
single-model pass plus a human read of the complete advice set on 5 sites. Two are mechanical
and hard: **criterion 5 at 1.00, blocking** (the prohibited-recommendation scan), and
**action-locus coherence** — every finding's action must name the locus of its own finding,
because the officials called out disconnected fixes explicitly.

### Q10. Why was a three-model judge panel cut?

**A.** *"A judge panel exists to make a subjective score trustworthy, and we cannot afford the
human anchor that would validate the panel. An unvalidated panel is not more trustworthy than
an honest single pass with a human read."*

### Q11. What is the held-out protocol?

**A.** 12 sites drawn by the same procedure and strata as dev, **selected and sealed before
the harness was built**. Total budget: **3 looks**, each logged. Any inspection beyond the
aggregate metric converts that site to dev, permanently. It is currently untouched. What 12
sites buy is detection of a **collapse** (0.90 → 0.60), not of a 10 pp drift — the interval is
roughly ±15 pp, and saying so is the point.

---

## B. The corpus

### Q12. What sets exist?

**A.** Dev (24 sites, 6 archetypes × 4, four of them non-English), held-out (12, sealed),
negative controls (15, 2–3 per dimension across 7 dimensions including `offsite_identity`),
adversarial (6), plus runtime-sample and phase-specific sets.

### Q13. How were negative controls chosen?

**A.** By **fetching and reading their markup**, not by reputation — each is curated clean on
*one named dimension*. That matters: a site's reputation says nothing about whether its
`<h1>` structure is sound.

### Q14. What is the negative set actually good for?

**A.** Catching a check that fires on every clean site. With 1–3 observations per
check-dimension cell it **cannot separate 0.05 from 0.15**, so it reports **counts, never
rates**, and it runs first because it is the cheapest possible refutation.

### Q15. What did the adversarial set find?

**A.** One of its six sites exposed a false-positive mechanism affecting **10 checks at once**
— an unfetchable page being read at face value as a page with no content (D-023) — which was
fixed **before any gold label was written**.

---

## C. Composition tests

### Q16. What three composition tests exist, and what did each return?

**A.**
1. **Leave-one-skill-out ablation** — ran on 36 sites. **Reported, not gated**, because any
   disjoint partition passes it. Its sharper form asked: *does removing the skill owning
   `CHK-D-003` change what `CHK-E-019` does anywhere?* On all 36 real sites, **no**.
2. **Merge test** — `render-extractability-audit` and `engagement-defect-audit` merged into
   `content-engagement-audit` and re-run against all 42 available sites: **every finding,
   every locus, every severity byte-identical** to the pre-merge output. Schema conformance
   unaffected, runtime unaffected. The boundary bought nothing measurable → merged for real.
3. **Bundle-sufficiency** — each analyser must run to completion with the network disabled.
   Verified by grep: **zero networking imports** in any analyser script.

### Q17. What is the honest reading of the ablation result?

**A.** That it proves almost nothing on its own, and the architecture document says so
*before* reporting it: removing any skill removes its checks and recall drops mechanically.
Stating that plainly matters more than claiming a test we haven't earned.

---

## D. Measured results (Stage E, 2026-09-10)

### Q18. What was measured, against what?

**A.** 624 gold cells — 24 dev sites × the 26 checks that existed at labelling time, 100%
labelled — against `harness/out/dev/*.report.json`, scored by `harness/score_dev.py`.

### Q19. What are the headline numbers?

**A.** Of the 15 checks with a defined precision at n ≥ 10 sites, **11 are ≥ 0.90 and 8 are
1.00**. Clean-site FP is **0.00 on 14 of the 21 checks that have one**. Eight of these are
perfect on both axes (`CHK-D-001`, `D-005`, `D-013`, `E-014`).

### Q20. Which checks trip a cut rule, and what is being done?

**A.** Eight trips across six checks. **Six of the eight point at the gold data or the
worksheet schema, not at check code**, and sit in `docs/evals/adjudication-queue.md` with a
suggested resolution and **no label written**. Only `CHK-D-007` (a measured base-rate effect,
deliberately untouched) and `CHK-E-022` are unexplained trips against code. **None were acted
on**, because the reproducibility pass has not run.

### Q21. What is the single most important sentence in the results report?

**A.** *"Those [grounding] rates are at or near zero for every check in the corpus."*
Precision here means **"fired where a defect was flagged"**, not **"and for the same reason."**
Anyone quoting a precision number from that report is obliged to quote the grounding rate
beside it.

### Q22. What does "no check was tuned to make a number look better" mean concretely?

**A.** Every cut-rule trip was diagnosed to the same standard, and the **split** was reported:

| Check | Real defect found | Effect |
| --- | --- | --- |
| `CHK-D-006` | definition regex accepted one sentence shape; JSON-LD suppression couldn't reach a misfiled About page | prec 0.57 → 1.00, FP 0.67 → 0.00, **recall 0.73 → 0.55** |
| `CHK-E-014` | hidden `rel="me"` verification anchor read as an unnamed control | prec/recall 0.88 → 1.00, FP 0.67 → 0.00 |
| `CHK-D-001` | robots parser had no RFC 9309 metacharacter support | prec 0.67 → 1.00 |
| `CHK-D-004` | page-type exclusion defeated by a misfiled contact page | prec 0.69 → 0.75 |
| `CHK-D-010` | English-only detectors asserting "no evidence" about German and Greek text | FP 0.23 → 0.08 |

And the ones that were **not** defects — `CHK-D-004`'s three index-page rows, `CHK-D-002`'s
bookshop.org row whose own notes contradict its label, `CHK-D-010`'s two German rows,
`CHK-E-015`'s two render-gap rows, `CHK-E-021`'s smashingmagazine row — went to adjudication
**unchanged**.

### Q23. What two findings from the diagnosis pass "deserve to outlive the numbers"?

**A.**
1. **The page-type/archetype classifier is a recurring single point of failure.** It defeated
   `CHK-D-006`'s suppression, `CHK-D-004`'s exclusion, and forced `CHK-E-024` to `N/A` on four
   commercial sites during labelling. Three separate checks, one upstream cause. (This drove
   the classifier rebuild in D-034.)
2. **One `CHK-D-010` recall drop was circularity, not regression.** Two German-site rows had
   been model-authored by running the same English-only regexes the check used — so they
   agreed with a bug, and fixing the bug turned them into misses. *That is the
   no-model-authored-labels rule failing in the concrete.*

### Q24. Why were three sites voided?

**A.** Grading needs both sides to have seen the same evidence. `tailscale.com` and
`www.thalia.de` were audited with zero pages collected; `vitejs.dev` ships 1 frozen snapshot
against 11 audited pages. **The corpus gap is disclosed, not repaired** — which is why several
`graded` counts are lower than in the first run.

### Q25. What has *not* been measured?

**A.** Stated plainly rather than omitted:
- **Reproducibility** — the 8-site test–retest has not run.
- **Severity metrics** — severity-exact rate and mean ordinal error need a gold severity
  column the current CSV doesn't have.
- **Held-out corpus** — untouched by design; the log is empty.
- **Four render checks** — `E-014` contrast, `E-015` overflow, `E-016`, `E-018` have no
  rendered evidence anywhere in the harness run.
- **Recall carries a ~±12 pp interval and is the weakest number reported.**

### Q26. What are the standing commitments the harness is held to?

**A.** Gold labels written before looking at output; the held-out set opened ≤3 times, every
look logged; every metric carries a CI or is a count; negative results recorded and failed
checks removed rather than softened; **asymmetric justification** — any change that *raises*
scores needs written justification plus a negative-control re-run in the same commit;
*"a finding we cannot reproduce is a bug, not a finding"*; and *"prefer cutting a check to
shipping one we cannot defend."*

### Q27. How do you run the harness?

```bash
python harness/run_audit.py --site example.com          # one live site
python harness/run_audit.py --set dev --offline         # replay frozen snapshots
python harness/score_dev.py                             # precision / recall / clean-site FP
python harness/retest.py --emit                         # draw the 8-site blind worksheet
python harness/ablation.py dev negative                 # composition tests
python harness/stability.py                             # k=3 live runs
python harness/package.py --zip                         # gates, then build the zip
```

Two rules the harness enforces: gold labels are **human-authored only**, and you must **never
read `harness/out/dev/*.report.json` while deciding what a label should be** — that is the
tool's own verdict, and using it makes the evaluation circular.
