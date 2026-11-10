# 10 — Constructive Q&A: where a critic would push

The questions a sharp grader, judge, or interviewer actually asks — plus the internal
inconsistencies found while assembling this pack. Nothing here is rhetorical: each answer is
either a defence that holds, or an admission with a next step.

---

## A. Attacks on the architecture

### Q1. "Your orchestrator does no cross-skill reasoning. Isn't it just a concatenator?"

**A.** It was two claims larger than it is now, and both retractions are in the design
documents that made the claims — not discovered by you. What survives is structural: severity
ordering, the site-wide rollup, meta-evaluation, and budget arbitration. **Some layer has to
sort, dedupe by page, and translate abandoned stages into declared limitations**, whether it
composes three analysers or thirty.

The honest form of the concession: *"That is a narrower claim than D-013 originally made, and
it is the honest one."*

### Q2. "Then why not collapse to one skill? A single well-built skill scores fully."

**A.** Two reasons that survive the merge test. First, the collector boundary buys enforceable
determinism and an enforceable budget **regardless of analyser count** — analysers with no
network tool cannot break the render-pass constraint. Second, `crawl-access-audit` (reads a
text file, hard-mechanical verdicts) and `entity-identity-audit` (structured data and
cross-page text, mostly theoretical/practitioner verdicts) differ genuinely in evidence type
and severity semantics.

**The weak point, stated in our own docs:** the remaining three-way split *"has not been
tested the way O-1 was — there is no known cross-skill dependency left to test between them,
which is either confirmation they are correctly separated or an untested assumption,
depending on how much weight the absence of a found dependency should carry. Recorded as open
rather than resolved."*

### Q3. "Isn't five skills just the AI-bloat the officials warned about?"

**A.** The defence is that we ran the test they implied. Six became five **on measured
evidence** — byte-identical output across 42 sites after the merge. A marketplace that has
merged a boundary is in a different position from one that has only argued for its
boundaries.

---

## B. Attacks on the evidence

### Q4. "Your precision numbers come from gold labels you wrote yourself. Why should I believe them?"

**A.** You shouldn't believe them further than the protocol supports, which is exactly what
the reports say. Three specific concessions are printed alongside the numbers:
- **One labeller.** Test–retest shows the rubric is *applied consistently*, not that it isn't
  *systematically misread*. Both recall and precision are exposed.
- **Grounding rate near zero.** Precision means *"fired where a defect was flagged"*, not
  *"and for the same reason."* Anyone quoting precision is obliged to quote grounding beside it.
- **Hand-picked corpus.** Every number estimates performance on a sample we chose.

### Q5. "You removed a matching condition and your scores went from 0.00 to 1.00. That's grading yourself."

**A.** The condition was unsatisfiable by construction — no check quotes its source, so **no
prediction could ever pass it**, and it pinned every check at zero including ones later
confirmed correct by hand. The mitigation is that the removed gate **is still computed and
printed under every precision figure**. It was demoted from gate to disclosure, not deleted.

### Q6. "Four checks fail your own cut rules and you shipped them anyway."

**A.** Correct, and it is stated in the results report rather than buried. The reasons split:
`CHK-D-007`'s 0.50 FP rate is a **measured base-rate effect** deliberately left in (structured
data exists on 44.1% of domains); two trips point at gold rows queued for adjudication; one
(`CHK-E-022`) is an unexplained trip against code. And **no cut rule may be acted on at all
until the reproducibility pass runs** — a check is cut on a reproducible number, not a single
pass.

### Q7. "Six of your 32 checks have no evidence-ledger row."

**A.** True, and it is the sharpest documentation gap in the repo. `CHK-D-029`–`D-034` (the
vertical-schema family) ship without ledger rows, while the ledger's own gate states *"a check
may not ship until its row is complete and at least one supporting source is VERIFIED."*
**Mitigating:** all six are recommendation-only and can never create a scored finding, so the
severity discipline the gate protects is not actually breached. **Next step:** write six rows,
or state the exemption explicitly in the ledger's gate.

### Q8. "Two of your checks have no supporting research at all."

**A.** `CHK-D-011` and `CHK-D-013` — every cited source was opened by hand and none discusses
the claim. That was found by *our own* verification pass, recorded as a genuine evidence gap
rather than a citation mismatch, and both were demoted to recommendation-only. The alternative
readings — that they should have been cut, or never authored — are both defensible; the
position taken is that the advice stands on its own terms and ships as advice, not as a
finding.

### Q9. "Your `critical` severity rests on a taxonomy nothing cites."

**A.** Also ours, also flagged: the R-1 pass found that *"neither cited source establishes the
retrieval-vs-training taxonomy that the critical/low split itself rests on."* It should cite
vendor crawler documentation (OpenAI/Anthropic/Google) directly. **This is a known,
undischarged gap on a `critical`-severity check** — and the single highest-value unfinished
citation in the repo.

---

## C. Attacks on coverage

### Q10. "Mechanism D is half of the discoverability story and you don't measure it."

**A.** Correct, declared as LIM-01 and LIM-02 in every report. The audit checks *the anchoring
the site itself provides* for corroboration, not whether corroboration occurred. The officials
explicitly permitted fetching third-party sites for cross-corroboration, so **the constraint
here is ours** (determinism, runtime, and no keyed API), not theirs. A defensible extension
exists — keyless public sources like Wikidata or Wayback — and was scoped in
`FETCH-STRATEGY.md` §6 but not shipped.

### Q11. "Your engagement half doesn't answer the question the officials actually asked."

**A.** The strongest criticism available, and it is written down in our own notes. Satya framed
engagement as **context carry-over**: does the landing experience relate to the intent that
brought the visitor there? Our engagement half is *entirely stage-agnostic defect detection*.
Read-only proxies were identified — deep-link behaviour, self-contained landing context, query
parameter preservation, title/meta vs content mismatch — and **none shipped**. It is listed as
Action #7 in `OFFICIALS-QA.md` and is the clearest remaining "beyond the common denominator"
opening.

### Q12. "A third of your engagement checks don't run in the grading sandbox."

**A.** Four sub-checks: contrast, 375 px overflow, tap targets, load-time overlay. Two other
render-dependent checks re-derive a one-sided static signal capped one tier lower. The
handling is the point: they are named in `degraded_stages[]` in every report, so a reader is
told they were not measured rather than left to infer it from absence. One check with no
static proxy at all (`CHK-E-023`) was cut rather than kept as a check that silently emits
nothing.

### Q13. "Your archetype classifier abstains most of the time."

**A.** An 84-site run returned `unknown` for 61% of sites before the D-034 rebuild, and
`brochure` was wrong on almost every site it labelled. Post-rebuild it is **explicitly not yet
validated on a blind list**. The design choice — abstain rather than guess — is right, because
a wrong confident label activates suppression rules written for a different kind of site. But
it has a real cost: every abstention suppresses the archetype-conditioned checks, and the
officials named vertical-specific insight as a rewarded differentiator. **The classifier is
the biggest single lever left in this project.**

### Q14. "The diagnosis pass called the classifier a single point of failure. Was it fixed?"

**A.** It was rebuilt (D-034 → D-036), and the specific bugs that defeated `CHK-D-006`'s
suppression and `CHK-D-004`'s exclusion were fixed. But the *structural* observation stands:
three separate checks failed for one upstream cause, and nothing in the architecture prevents
a fourth from doing so. There is no classifier-accuracy number measured on a blind list.

---

## D. Internal inconsistencies found while assembling this pack

These are real, small, and fixable. Recording them is more useful than smoothing them over.

### Q15. What is the site-wide rollup threshold — 2 pages or 3?

**A.** **Two.** `ROLLUP_MIN_PAGES = 2` in `compose_report.py:160`, and both
`audit-orchestrator/SKILL.md` step 5b and `report-schema.md` say "2 or more". But
`docs/ARCHITECTURE.md` §4.4 and the marketplace `README.md` both still say **"≥ 3 pages"** —
stale text from before the threshold was lowered. **Fix:** update those two sentences.

### Q16. How many checks are there — 26 or 32?

**A.** **32.** `CHECK_TITLES` has 32 entries, and the orchestrator's SKILL.md, the marketplace
README and the root README all say 32. But `docs/ARCHITECTURE.md` §5 still says **"26 checks,
disjoint"** and its skill map omits `CHK-D-029`–`D-034` from `entity-identity-audit`'s row.
**Fix:** the file declares itself *"authoritative for check ownership"*, so it is the one that
most needs updating.

### Q17. Does the evidence ledger name the right owning skills?

**A.** No — every row says `marketplace_auditor` or `TBD (Phase 2)`. **This one is
disclosed, not drift:** the ledger's own header states *"the `Owning skill` column is
superseded by the skill map in ARCHITECTURE.md §5"*. It is still worth a cleanup pass, because
a grader reading the ledger first sees a monolith.

### Q18. Does the Stage E report cover all shipped checks?

**A.** No — it measures **26**, the set that existed at labelling time. The six vertical-schema
checks are unmeasured. That is consistent with the gold file (624 = 24 × 26) but should be
said in the results report rather than inferred from the arithmetic.

### Q19. Does `content-engagement-audit` still declare inputs it can never receive?

**A.** It lists `rendered[]` among its inputs, which is empty in every graded run. That is
*correct* — the skill is provider-neutral and a runtime with a browser would populate it — but
a reader may take it as a claim about what actually happens. The degraded-stages machinery
exists precisely to make the distinction visible; the input table could say so in a clause.

---

## E. "What would you do next?" — ranked

### Q20. If you had one more day, what would you do?

**A.**
1. **Run the 8-site intra-rater test–retest.** It is the one item on the critical path, it
   gates every cut rule, and without it no check has a *reproducible* number.
2. **Cite the retrieval-vs-training taxonomy** to vendor crawler docs. It is the undischarged
   gap under a `critical` severity — the single most attackable claim in the marketplace.
3. **Fix the three documentation inconsistencies above** (rollup threshold, check count,
   ledger ownership). Cheap, and a grader reading statically will hit them.

### Q21. If you had one more week?

**A.**
4. **Validate the archetype classifier on a blind list.** It gates the vertical-specific
   differentiator the officials explicitly said they reward, and it has already caused three
   check failures.
5. **Ship one context-carry-over check.** Even one well-evidenced landing-intent signal would
   move the engagement half from "defect detection" toward the question as the officials frame
   it.
6. **Write the six missing ledger rows** for `CHK-D-029`–`D-034`.

### Q22. What would you *not* do, even with unlimited time?

**A.**
- **Query a live generative engine** to check citation status. Visibility is a distribution
  across runs, prompts and time; it would break determinism, runtime and reproducibility at
  once, and it would produce a number that cannot be reproduced by the reader.
- **Tune a check to clear a cut line.** The asymmetric-justification rule exists for exactly
  this, and every fix so far has been traced to a defect in the check, the corpus, or the gold
  data — not to the number.
- **Recommend `llms.txt` as a substantive fix** to look more complete. The refusal is stated
  visibly instead.
- **Add skills to look decomposed.** The merge test exists to catch that, and it already has.

---

## F. Rehearsal questions

Short-answer prompts for a viva. If you can answer each in two sentences, you know the project.

1. Why is `absent` emitted instead of dropped?
2. Why is `alt=""` not a violation?
3. Why is a training-crawler block only `low`?
4. Why does a hybrid crawler blocked at root count as retrieval-class?
5. Why does severity roll up to the worst instance, not the mean?
6. Why is Step 3 of the procedure empty rather than deleted?
7. Why does the report record a render stage that never started?
8. Why was `CHK-E-023` cut but `CHK-E-016` kept, when both are render-dead?
9. Why does `CHK-D-013` use Jaccard on `main_text` rather than the trigram hash?
10. Why are `canonical_consistency` and `canonical_majority` different detector names?
11. Why is `top_priorities[]` empty rather than padded with a class-3 item?
12. Why are meta-evaluation warnings not corrected automatically?
13. Why can't a model write a gold label?
14. Why is the negative-control set reported as counts and never as a rate?
15. What does the grounding rate printed under every precision figure mean?
16. Why did `CHK-D-006`'s recall *fall* when it was fixed, and why report that?
17. What is the one cross-skill suppression rule, and why doesn't it exist anymore?
18. Why does `unknown` archetype suppress checks instead of running them with defaults?
19. What is the difference between `not_determinable` and `absent` in a reader's hands?
20. Name the single most attackable claim in the marketplace and say why.
