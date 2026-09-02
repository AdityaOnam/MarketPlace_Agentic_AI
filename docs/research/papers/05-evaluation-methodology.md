# 05 — Evaluation methodology

Literature review supporting the evaluation harness for the Agent Skill Marketplace (Adobe
University Hackathon 2026, Round 3). The question this brief answers: *how do we rigorously
measure detection quality, action quality, determinism and generalization for a system that
emits findings about an arbitrary website?*

**Honesty conventions used here**

- `Status: VERIFIED` — the record was retrieved (arXiv metadata API / publisher page) and the
  title, author list, venue and abstract read directly. `Status: SEARCH-ONLY` — the item
  appeared in search results with a plausible title/venue but could not be opened.
- All quantitative results below are as stated in the abstract or paper of the cited work.
  Where an abstract reports no number, this is written as "none reported in abstract".
- Statements that are our own reasoning, not the paper's claim, are marked `(our inference)`.
- Sources: **31 entries — 29 VERIFIED, 1 VERIFIED (bibliographic record only), 1 SEARCH-ONLY.**
  No entry in this file was written from memory without retrieval.

**Retrieval method note.** Most entries were verified via the arXiv Atom metadata API
(`export.arxiv.org/api/query?id_list=...`), which returns the canonical title, author list,
publication date and abstract for a given identifier. This verifies existence, authorship and
venue, and the abstract's claims. It does **not** verify claims made only in a paper's body;
where a number below is not from the abstract, it is flagged.

---

## A. LLM-as-a-judge: validation and the critique literature

### P-05.01 · Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena
Zheng, Chiang, Sheng et al. · NeurIPS 2023 Datasets & Benchmarks Track · 2023 ·
https://arxiv.org/abs/2306.05685 · **Status: VERIFIED**

- **Mechanism.** A strong LLM is prompted to compare or score model outputs; agreement with
  human preference is then measured against a human-labelled reference set. The paper's real
  contribution is not the judge but the *validation protocol* for a judge, and the explicit
  naming of position bias, verbosity bias and self-enhancement bias as failure modes.
- **Key quantitative result.** GPT-4 judges reach **over 80% agreement with human
  preferences** on MT-Bench/Chatbot Arena — "the same level of agreement between humans".
  Scale: 3K expert votes (MT-Bench), 30K conversations with preference labels (Arena).
- **Transfer to our eval harness.** The 80%-and-that-equals-human-agreement figure sets the
  ceiling we are allowed to claim. Any judge we use for suggested-action quality must be
  validated against a human-labelled subset before its scores are reported, and the
  human–human agreement on that same subset must be reported alongside it as the ceiling.
- **Pitfall.** ~80% agreement on *preference between two answers* does not transfer to
  *absolute scoring of a single finding*, which is the harder task and the one we actually
  need. Citing this number as licence for a single-answer graded judge overstates it.

### P-05.02 · G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment
Liu, Iter, Xu et al. · 2023 · https://arxiv.org/abs/2303.16634 · **Status: VERIFIED**

- **Mechanism.** Chain-of-thought plus a *form-filling* paradigm: the judge is given evaluation
  steps and fills in a structured score form rather than emitting free-form praise. Scores are
  weighted by token probability to break ties.
- **Key quantitative result.** Spearman **0.514** with human judgments on summarization,
  substantially above prior automatic metrics.
- **Transfer to our eval harness.** Adopt form-filling: our judge never writes prose about a
  finding; it fills a fixed schema of binary fields. This is the shape our
  suggested-action rubric takes (§ harness, item 4).
- **Pitfall.** The paper itself flags that LLM judges may **prefer LLM-generated text**. Our
  findings *are* LLM-generated, so a naive judge grading our own output is biased toward
  approving it — the failure mode P-05.06 quantifies.

### P-05.03 · Prometheus: Inducing Fine-grained Evaluation Capability in Language Models
Kim, Shin, Cho et al. · ICLR 2024 · 2023 · https://arxiv.org/abs/2310.08491 ·
**Status: VERIFIED**

- **Mechanism.** An evaluator model trained on a large collection of *user-supplied,
  fine-grained score rubrics* (Feedback Collection: 1K rubrics, 20K instructions, 100K
  responses) rather than a single generic "is this good" scale.
- **Key quantitative result.** Pearson **0.897** with human evaluators on customized rubrics,
  vs. GPT-4's **0.882** and ChatGPT's **0.392** on the same setup.
- **Transfer to our eval harness.** The gap 0.897/0.882 vs. 0.392 is the strongest evidence in
  this corpus that *rubric specificity, not judge size, drives judge reliability*. Our budget
  should go into writing precise per-criterion rubrics, not into using the largest judge.
- **Pitfall.** The rubrics in this work are supplied by the same people who write the
  reference answers. A rubric written by whoever wrote the audit skill will encode that
  skill's assumptions and inflate its score (our inference); rubric authorship must be
  separated from skill authorship in our protocol.

### P-05.04 · JudgeBench: A Benchmark for Evaluating LLM-based Judges
Tan, Zhuang, Montgomery et al. · ICLR 2025 · 2024 · https://arxiv.org/abs/2410.12784 ·
**Status: VERIFIED**

- **Mechanism.** Converts hard existing datasets into response pairs with *objectively*
  known-correct labels (knowledge, reasoning, math, coding), so judge quality is measured
  against ground truth rather than against human preference, which conflates style with
  correctness.
- **Key quantitative result.** On these challenging pairs, strong judges including GPT-4o
  perform **only slightly better than random chance**.
- **Transfer to our eval harness.** Decisive for our design: a judge may *not* be used to
  decide whether a technical finding is factually correct. Judge use is confined to
  *subjective* dimensions (is the action specific, executable, well-targeted). Correctness of
  a finding is decided by a deterministic check against the frozen page snapshot, or by a
  human.
- **Pitfall.** Reporting a high judge-vs-human agreement on easy items and then applying the
  judge to hard items. Judge agreement must be reported *stratified by item difficulty*, or
  it is an average over a distribution we do not evaluate on.

### P-05.05 · Large Language Models are not Fair Evaluators
Wang, Li, Chen et al. · 2023 · https://arxiv.org/abs/2305.17926 · **Status: VERIFIED**

- **Mechanism.** Positional bias: the judge's verdict depends on which candidate is presented
  first. Mitigations proposed are multiple evidence calibration, balanced position calibration
  (swap and aggregate), and human-in-the-loop calibration.
- **Key quantitative result.** By **merely changing the order** of candidates, Vicuna-13B can
  be made to beat ChatGPT on **66 out of 80** queries — i.e. the ordering alone can flip the
  headline conclusion.
- **Transfer to our eval harness.** Every judged comparison in our ablations (system-with-skill
  vs. system-without-skill) is run in **both orders and the results averaged**; a comparison
  whose verdict flips under swap is recorded as a tie, not resolved by picking one.
- **Pitfall.** Position bias is not confined to pairwise mode. Ordering effects also apply to
  the *list of findings* we hand a judge; findings are shuffled per judging call (our
  inference, by analogy).

### P-05.06 · LLM Evaluators Recognize and Favor Their Own Generations
Panickssery, Bowman, Feng · 2024 · https://arxiv.org/abs/2404.13076 · **Status: VERIFIED**

- **Mechanism.** Self-preference. LLMs can distinguish their own outputs from others' at
  non-trivial accuracy, and fine-tuning experiments show a **linear correlation between
  self-recognition capability and the strength of self-preference bias** — evidence for a
  causal link, not just correlation.
- **Key quantitative result.** As above; the linear self-recognition/self-preference relation
  is the headline. Models score their own text higher despite humans judging quality equal.
- **Transfer to our eval harness.** Hard constraint: **the judge model family must differ from
  the model family that generated the audit**, and the pairing is recorded in the run
  manifest. If only one family is available, judge scores are reported as "self-judged,
  upper bound" and only human-labelled scores are quoted as results.
- **Pitfall.** Anonymising outputs is not a fix — the finding is that models recognise their
  own text *without* being told whose it is.

### P-05.07 · Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models
Verga, Hofstätter, Althammer et al. · 2024 · https://arxiv.org/abs/2404.18796 ·
**Status: VERIFIED**

- **Mechanism.** PoLL — a panel of several smaller judges from *different model families*,
  aggregated, instead of one large judge. Diversity across families is what reduces
  intra-model bias.
- **Key quantitative result.** The panel outperforms a single large judge while being
  **over seven times less expensive**.
- **Transfer to our eval harness.** Where we can afford it, the suggested-action rubric is
  scored by a 3-judge panel drawn from distinct families with majority vote per binary
  criterion; disagreement rate per criterion is itself reported, because a criterion the
  panel cannot agree on is a badly-written criterion (our inference).
- **Pitfall.** A panel of three judges that share training data or a common ancestor is one
  judge with extra cost. Family diversity must be documented, not assumed.

### P-05.08 · Limits to scalable evaluation at the frontier: LLM as Judge won't beat twice the data
Dorner, Nastl, Hardt et al. · ICLR 2025 · 2024 · https://arxiv.org/abs/2410.13341 ·
**Status: VERIFIED**

- **Mechanism.** A theoretical + empirical result on debiasing schemes that use a cheap LLM
  judge plus a small amount of ground truth. It bounds how much judge labels can substitute
  for real labels.
- **Key quantitative result.** When the judge is **no more accurate than the model being
  evaluated**, debiasing methods **cannot reduce the required amount of ground truth by more
  than half**.
- **Transfer to our eval harness.** Sets the budget arithmetic. We cannot label 10 sites by
  hand and judge-label 200 more and claim the precision of a 210-site study; the effective
  sample is at best ~2× the human-labelled portion. Confidence intervals are computed on the
  human-labelled count, and judge-extended numbers are reported separately and labelled as
  such.
- **Pitfall.** The common move of reporting a judge-scored metric over a large auto-labelled
  set with a tight-looking interval. The interval is not real; the label noise is not in it.

---

## B. Rubric and checklist decomposition

### P-05.09 · CheckEval: A reliable LLM-as-a-Judge framework for evaluating text generation using checklists
Lee, Kim, Kim et al. · EMNLP 2025 · 2024 · https://arxiv.org/abs/2403.18771 ·
**Status: VERIFIED**

- **Mechanism.** Replaces a graded score (1–5) with a **checklist of decomposed binary
  questions**; the score is the aggregate of yes/no answers. Each decision is traceable to a
  specific question, so disagreement is localisable.
- **Key quantitative result.** Increases average agreement **across models by 0.45** and
  **reduces score variance**.
- **Transfer to our eval harness.** This is the single most directly applicable result in the
  corpus. Every subjective dimension in our harness — suggested-action quality, evidence
  sufficiency — is expressed as binary criteria, never as a 1–5 score. Aggregation is by
  count of criteria met.
- **Pitfall.** Binary decomposition moves the subjectivity into the *wording of each question*
  rather than removing it. Questions whose panel disagreement is high must be rewritten, and
  the rewrite must happen on dev sites only, never on the held-out set.

### P-05.10 · FLASK: Fine-grained Language Model Evaluation based on Alignment Skill Sets
Ye, Kim, Kim et al. · ICLR 2024 Spotlight · 2023 · https://arxiv.org/abs/2307.10928 ·
**Status: VERIFIED**

- **Mechanism.** Decomposes a coarse score into *per-instance skill sets* — the criteria
  applied depend on what the instruction actually requires, rather than one fixed rubric
  applied to everything.
- **Key quantitative result.** Reports high correlation between model-based and human-based
  evaluation under the fine-grained protocol; no single headline number in the abstract.
- **Transfer to our eval harness.** Our rubric must be **conditional on finding type**. Judging
  a schema.org finding and a Core Web Vitals finding with the same five criteria produces a
  score that measures neither. Each check class carries its own criterion list.
- **Pitfall.** Per-type rubrics make cross-type aggregation meaningless. Report per-check-class
  scores; a single "action quality" headline number across all types is not comparable across
  systems (our inference).

### P-05.11 · HealthBench: Evaluating Large Language Models Towards Improved Human Health
Arora, Wei, Soskin Hicks et al. · OpenAI · 2025 · https://arxiv.org/abs/2505.08775 ·
**Status: VERIFIED**

- **Mechanism.** Physician-written, per-conversation rubric criteria; a model grader checks
  each criterion against the response. Demonstrates rubric-based grading at scale in a domain
  where wrong advice is harmful — structurally the same as ours.
- **Key quantitative result.** 5,000 multi-turn conversations, **262 physicians**, **48,562
  rubric criteria** — roughly 10 bespoke criteria per item. Scores span 16% (GPT-3.5 Turbo) to
  60% (o3).
- **Transfer to our eval harness.** Two lessons: (a) criteria are written **per item**, not
  globally, and (b) the achievable score is far below 100% and low scores are informative
  rather than a sign of a broken rubric. Our gold labels are per-site criterion lists, and we
  do not tune the rubric until scores look good.
- **Pitfall.** Cost. ~10 criteria per site written by hand is the real constraint on our corpus
  size, and it is the reason the dev/held-out split must be small and stratified rather than
  large and random (our inference).

### P-05.12 · FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation
Min, Krishna, Lyu et al. · EMNLP 2023 · 2023 · https://arxiv.org/abs/2305.14251 ·
**Status: VERIFIED**

- **Mechanism.** Decomposes generated text into **atomic facts** and scores the percentage
  supported by a reliable source. Precision is computed over atoms, not over documents.
- **Key quantitative result.** ChatGPT scores **58%** factual precision on biography
  generation; the automated estimator has **<2% error rate** vs. human atoms and was run over
  6,500 generations from 13 LMs.
- **Transfer to our eval harness.** Our unit of evaluation is the **individual finding**, and
  within a finding, the **evidence string** is checked atomically against the frozen snapshot:
  does the quoted evidence literally appear at the cited location? This gives us a
  deterministic, non-judge grounding check — the cheapest and most decisive false-positive
  filter we have.
- **Pitfall.** Atom-level precision rewards a system that emits many trivially-true atoms. It
  must be paired with a recall measure and with a *materiality* criterion, or a system that
  reports "the page has a `<title>` tag" scores well.

### P-05.13 · AdaRubric: Task-Adaptive Rubrics for Reliable LLM Agent Evaluation and Reward Learning
Ding et al. · KnowFM @ ACL 2026 · 2026 · https://arxiv.org/abs/2603.21362 · **Status: VERIFIED**

- **Mechanism.** Generates a task-specific rubric per agent trajectory and scores step by step,
  instead of applying one fixed rubric to every trajectory.
- **Key quantitative result.** **Pearson r = 0.79** human correlation and **Krippendorff's
  alpha = 0.83** reliability; training on the resulting preference pairs improves task success
  by **+6.8-8.5%**.
- **Transfer to our eval harness.** Confirms two things we need: per-task rubrics are viable at
  agent-trajectory granularity, and alpha ~ 0.83 is the level a *well-constructed automated*
  rubric reaches — a realistic target for our own gold-label agreement, not 0.95.
- **Pitfall.** An auto-generated rubric can drift toward what the system under test happens to
  do. Our rubric criteria are frozen and version-pinned before a run, and rubric changes bump a
  version number recorded in the results table.

### P-05.14 · Autorubric: A Unifying Framework for Rubric-Based LLM Evaluation on Non-Verifiable Tasks
Rao, Callison-Burch · COLM 2026 · 2026 · https://arxiv.org/abs/2603.00077 ·
**Status: VERIFIED**

- **Mechanism.** Infrastructure for rubric-based evaluation of *non-verifiable* tasks, with
  configurable bias mitigations (position bias, criterion conflation) and psychometric
  diagnostics over the criterion set.
- **Key quantitative result.** No single headline accuracy; the reported finding is that
  **"configuration effects do not support a universal mitigation stack"** — the right
  de-biasing configuration is task-dependent, and criterion-specific failures are visible.
- **Transfer to our eval harness.** Two direct imports: (a) run *psychometric diagnostics on
  our own rubric* — per-criterion variance, criterion-criterion correlation, and criteria that
  never discriminate — and drop criteria that always fire the same way; (b) do not copy a
  de-biasing recipe from a paper and assume it transfers; measure position-swap flip rate on
  our own rubric.
- **Pitfall.** "Criterion conflation" is our most likely rubric bug: a criterion like
  "actionable" silently bundles specificity, correctness and effort. Each must be its own
  binary.

### P-05.15 · FeedEval: Pedagogically Aligned Evaluation of LLM-Generated Essay Feedback
Chu, Kim, Yi · 2026 · https://arxiv.org/abs/2601.04574 · **Status: VERIFIED**

- **Mechanism.** Splits *feedback quality* into three separately-modelled dimensions —
  **specificity, helpfulness, validity** — with a dedicated evaluator per dimension rather than
  one "is this good feedback" score. Validity is framed as natural-language inference against
  the rubric description.
- **Key quantitative result.** Abstract reports strong alignment with human judgment and a
  downstream check: feedback rated high by FeedEval **leads to more effective revisions**. No
  single agreement coefficient in the abstract.
- **Transfer to our eval harness.** The closest analogue in the literature to what we must
  grade: our `suggested_action` field is advice, and advice quality is not one number. We adopt
  the same split — *specificity*, *helpfulness/actionability*, *validity (is it entailed by the
  evidence we cited)* — and the validity dimension is implemented as entailment against our own
  `evidence` string, which is checkable.
- **Pitfall.** The downstream-revision check is the only real validation of an advice rubric,
  and we mostly cannot run it (we cannot fix a stranger's website and re-measure). Our advice
  scores are therefore *proxy* scores and must be labelled as such (our inference).

---

## C. Detection metrics under class imbalance and calibration

### P-05.16 · The Relationship Between Precision-Recall and ROC Curves
Davis, Goadrich · ICML 2006, pp. 233-240, DOI 10.1145/1143844.1143874 ·
https://ftp.cs.wisc.edu/machine-learning/shavlik-group/davis.icml06.pdf ·
**Status: SEARCH-ONLY** (bibliographic record confirmed via dblp
`dblp.org/rec/conf/icml/DavisG06` and the ACM DOI listing; the PDF itself did not render for
retrieval, so the claims below are as reported in those listings, not read from the paper)

- **Mechanism.** Establishes the formal correspondence between ROC space and PR space: a curve
  dominates in ROC space iff it dominates in PR space; introduces the *achievable* PR curve.
- **Key quantitative result.** Structural rather than numeric. Two operational consequences
  reported: **linear interpolation between points in PR space is incorrect**, and **optimising
  AUC-ROC does not guarantee optimising AUC-PR**.
- **Transfer to our eval harness.** Our positives (real findings on a page) are rare relative to
  the space of checks that could fire. We report **precision/recall and PR-based summaries, not
  ROC/AUC**, and we never interpolate a PR curve when reporting.
- **Pitfall.** Because this entry is SEARCH-ONLY, do not quote a specific theorem number from it
  in the submission; cite it for the general claim only, or open the PDF first.

### P-05.17 · The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets
Saito, Rehmsmeier · PLOS ONE, 2015 · DOI 10.1371/journal.pone.0118432 ·
https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432 ·
**Status: VERIFIED**

- **Mechanism.** The PR baseline moves with the positive-class prevalence; the ROC curve does
  not. Therefore ROC can look identical for a classifier whose real-world usefulness collapsed
  when the positive class became rare.
- **Key quantitative result.** In a literature survey of **33 studies** on large imbalanced
  datasets, **~67% used ROC** as the primary evaluation and **only 6% used PRC**. Simulations
  show PRC correctly exposes a performance difference between the balanced and imbalanced case
  that ROC "fail[s] to explicitly show".
- **Transfer to our eval harness.** Every detection metric we report carries the **prevalence of
  the positive class in that stratum** next to it. A precision of 0.9 on a stratum where 80% of
  sites have the defect is barely above the base rate; the same number where 10% have it is a
  real result.
- **Pitfall.** Aggregating precision across strata with different prevalences produces a number
  driven by the stratum mix, not by the detector. Report per-stratum, then a prevalence-weighted
  aggregate, and say which is which.

### P-05.18 · On Calibration of Modern Neural Networks
Guo, Pleiss, Sun et al. · ICML 2017 · https://arxiv.org/abs/1706.04599 · **Status: VERIFIED**

- **Mechanism.** Establishes that model confidence systematically diverges from empirical
  accuracy, and that a one-parameter post-hoc correction (temperature scaling) fixes much of it.
  The measurement apparatus — reliability diagrams and expected calibration error — is what we
  reuse.
- **Key quantitative result.** Modern (deeper, wider, batch-normed, weakly-regularised) networks
  are **markedly less calibrated** than older ones; temperature scaling is "surprisingly
  effective" across most datasets.
- **Transfer to our eval harness.** If a finding carries a confidence, we bin findings by stated
  confidence and plot observed precision per bin — a reliability diagram over findings, plus
  ECE. This is what makes a confidence-gated abstention threshold defensible rather than
  arbitrary.
- **Pitfall.** ECE is bin-count sensitive and can be made to look good by choosing bins. Fix the
  bin scheme in advance and report it; also report per-bin counts, since a bin with four
  findings has no meaningful precision.

---

## D. Reliability, variance, and statistical honesty

### P-05.19 · Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations
Miller · 2024 · https://arxiv.org/abs/2411.00640 · **Status: VERIFIED**

- **Mechanism.** Treats an eval as a sampling problem: questions are drawn from a
  super-population, so the reported score is an estimate with a standard error. Gives formulas
  for standard errors, clustered questions, paired differences between two systems, and
  power/sample-size planning.
- **Key quantitative result.** Methodological; the abstract offers recommendations and formulas
  rather than a benchmark number.
- **Transfer to our eval harness.** This is the paper our reporting format is built on. (a)
  Every metric gets a CI. (b) Findings from the *same site* are **clustered** — they are not
  independent samples, and treating each finding as an independent trial understates the error
  badly; our unit of resampling is the **site**, via a site-level cluster bootstrap. (c)
  Ablations are **paired** comparisons on the same sites, which is far more powerful than
  comparing two independent means.
- **Pitfall.** The clustering point is the one that will bite us: 12 sites x 20 findings is 12
  samples, not 240. Any interval computed as if it were 240 is too narrow.

### P-05.20 · tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains
Yao, Shinn, Razavi et al. · 2024 · https://arxiv.org/abs/2406.12045 · **Status: VERIFIED**

- **Mechanism.** Evaluates agents over dynamic multi-turn interaction, and introduces
  **pass^k** — the probability that *all* k independent trials succeed — as opposed to pass@k,
  the probability that *at least one* succeeds. pass^k measures reliability; pass@k measures
  best-of-k.
- **Key quantitative result.** State-of-the-art agents (GPT-4o) succeed on **fewer than 50%** of
  tasks, and **pass@8 is under 25%** in the retail domain — consistency across trials is far
  worse than single-trial success suggests.
- **Transfer to our eval harness.** Our determinism metric is a **pass^k-style all-runs-agree
  rate**, not a mean over runs. A site where 3 of 5 runs produce the same finding set scores 0
  on stability, not 0.6. This matches the rubric's demand for determinism.
- **Pitfall.** pass^k is brutal and will look bad early. That is the point; do not silently
  switch to a mean-over-runs number when pass^k is unflattering.

### P-05.21 · tau^2-Bench: Evaluating Conversational Agents in a Dual-Control Environment
Barres, Dong, Ray et al. · 2025 · https://arxiv.org/abs/2506.07982 · **Status: VERIFIED**

- **Mechanism.** Extends tau-bench to an environment where both the agent and the user can
  change shared state, and provides **fine-grained analysis separating reasoning errors from
  communication/coordination failures**.
- **Key quantitative result.** Significant performance drops moving from single-control to
  dual-control settings; the abstract does not give a single headline percentage.
- **Transfer to our eval harness.** The error-attribution idea transfers directly: when an audit
  run fails, our harness must record *which stage* failed — fetch/crawl, extraction, check
  logic, or report assembly — rather than only that the finding was wrong. Without this the
  ablations cannot be interpreted.
- **Pitfall.** Failure taxonomies invite post-hoc category invention. The stage categories must
  be fixed before the runs, and "other" must be a permitted, counted bucket.

### P-05.22 · Evaluating Large Language Models Trained on Code (Codex / HumanEval; origin of pass@k)
Chen, Tworek, Jun et al. · 2021 · https://arxiv.org/abs/2107.03374 · **Status: VERIFIED**

- **Mechanism.** Introduces the pass@k estimator: sample n >= k completions and estimate the
  probability that at least one of k succeeds. Included here as the contrast case for P-05.20.
- **Key quantitative result.** Codex solves **28.8%** of HumanEval problems at one sample, but
  **70.2%** with 100 samples per problem — a 2.4x gap between capability and reliability.
- **Transfer to our eval harness.** The 28.8 -> 70.2 gap is the argument for why a single run of
  our audit proves nothing about determinism. We report both: single-run quality *and* the
  all-runs-agree stability rate.
- **Pitfall.** pass@k with large k is a capability claim, not a product claim. Quoting a
  best-of-k number for a system that ships one run is the classic overstatement.

### P-05.23 · A Survey on LLM-as-a-Judge
Gu, Jiang, Shi et al. · 2024 · https://arxiv.org/abs/2411.15594 · **Status: VERIFIED**

- **Mechanism.** Survey of the judge paradigm: how to build reliable judges, consistency
  improvement, bias mitigation, and evaluation of judges themselves.
- **Key quantitative result.** Survey; no primary experimental number in the abstract.
- **Transfer to our eval harness.** Used as an index into the bias taxonomy rather than as
  evidence. Cite the primary sources (P-05.05, P-05.06, P-05.08) for the individual claims.
- **Pitfall.** Citing a survey for a specific empirical number is a common way an unverified
  claim enters a document. Do not do it here.

---

## E. Benchmark construction, contamination, and construct validity

### P-05.24 · Establishing Best Practices for Building Rigorous Agentic Benchmarks
Zhu, Jin, Pruksachatkun et al. · 2025 · https://arxiv.org/abs/2507.02825 · **Status: VERIFIED**

- **Mechanism.** Audits existing agentic benchmarks for flawed task design and flawed reward /
  outcome-validity, then proposes an **Agentic Benchmark Checklist (ABC)** covering task
  validity and outcome validity.
- **Key quantitative result.** Flaws can cause **performance estimation errors of up to 100%**;
  applying ABC to CVE-Bench **reduced performance overestimation by 33%**.
- **Transfer to our eval harness.** The most important governance document for us: we are
  *building* an agentic benchmark, and the "up to 100%" error figure is what happens when the
  grader accepts something that is not actually the task. Concretely: our matcher must not
  credit a finding that names the right check but points at the wrong page or wrong element,
  and our gold set must be constructible without reference to what the system emitted.
- **Pitfall.** Outcome validity fails silently and almost always in our favour. Every change to
  the matcher that increases scores must be scrutinised harder than one that decreases them.

### P-05.25 · SWE-Bench+: Enhanced Coding Benchmark for LLMs
Aleithan, Xue, Mohajer et al. · 2024 · https://arxiv.org/abs/2410.06992 · **Status: VERIFIED**

- **Mechanism.** Empirical teardown of a widely-used benchmark: identifies solution leakage
  (the answer is present in the issue text or comments) and weak tests (a wrong patch passes).
- **Key quantitative result.** **32.67%** of successful patches involved solution leakage;
  **31.08%** passed due to weak test cases; the headline resolution rate falls from **12.47% to
  3.97%** after filtering. Over **94%** of issues predate the model knowledge cutoff.
- **Transfer to our eval harness.** Two direct analogues. *Leakage*: a site whose problems are
  described in its own public docs, or a site used as an example while writing the skill, must
  not appear in the test set. *Weak tests*: our matching rule must be strict enough that a
  vague finding cannot match a specific gold finding.
- **Pitfall.** The 12.47 -> 3.97 collapse is the size of error possible from grader weakness
  alone — roughly 3x. Assume our first-draft numbers are similarly inflated until the matcher
  has been adversarially checked.

### P-05.26 · Time Travel in LLMs: Tracing Data Contamination in Large Language Models
Golchin, Surdeanu · ICLR 2024 Spotlight · 2023 · https://arxiv.org/abs/2308.08493 ·
**Status: VERIFIED**

- **Mechanism.** Detects whether a dataset instance was seen in pretraining, via guided
  instruction completion and comparison against a reference.
- **Key quantitative result.** **92% and 100% accuracy** in detecting contamination across seven
  datasets; finds GPT-4 contaminated with AG News, WNLI and XSum.
- **Transfer to our eval harness.** Our test corpus is *the public web*, which is by definition
  in pretraining. We therefore cannot claim an uncontaminated test set; we can only claim the
  system was not *developed against* those sites. This limitation is stated in the submission
  rather than hidden. Preferring **recently-changed pages** and judging against **frozen local
  snapshots** is a partial mitigation (our inference).
- **Pitfall.** A site the judge model "knows" may be graded on memory rather than on our
  evidence string. Supplying the snapshot in the judging context reduces this.

### P-05.27 · Do ImageNet Classifiers Generalize to ImageNet?
Recht, Roelofs, Schmidt et al. · 2019 · https://arxiv.org/abs/1902.10811 ·
**Status: VERIFIED**

- **Mechanism.** Rebuilds new test sets following the original collection process and re-scores
  existing models — measuring how much of reported accuracy is specific to the original test
  set.
- **Key quantitative result.** Accuracy drops of **3-15% on CIFAR-10** and **11-14% on
  ImageNet** on freshly collected test sets. The authors attribute the drop to the new images
  being slightly harder, not to adaptive overfitting.
- **Transfer to our eval harness.** Budget an expected drop of this magnitude between our dev
  corpus and the unseen sites the graders use. A threshold set at exactly the dev-corpus score
  will be missed on unseen sites; targets are set with headroom, and the dev-vs-held-out gap is
  itself a reported metric.
- **Pitfall.** The paper's own conclusion (difficulty, not overfitting) is often mis-cited as
  proof of adaptive overfitting. Cite it for the *size of the drop*, not for its cause.

### P-05.28 · Generalization in Adaptive Data Analysis and Holdout Reuse
Dwork, Feldman, Hardt et al. · 2015 · https://arxiv.org/abs/1506.02629 · **Status: VERIFIED**

- **Mechanism.** Formalises why repeatedly querying a holdout set with adaptively chosen
  hypotheses destroys its validity, and gives a mechanism enabling "the validation of a large
  number of adaptively chosen hypotheses" against the same holdout, unified via approximate
  max-information.
- **Key quantitative result.** Theoretical; guarantees are expressed via differential privacy /
  approximate max-information rather than a benchmark number.
- **Transfer to our eval harness.** Justifies the held-out access budget as a *hard rule with a
  counter*, not an aspiration: a pre-declared number of looks, each logged with a date, the
  system version, and what was learned. The rule that the held-out set may only produce a
  pass/fail against a pre-registered threshold — not a ranked list of what to fix — is the
  practical version of budgeted access (our inference).
- **Pitfall.** "We only looked twice" is unfalsifiable without a log. The log must be committed
  in the repo, and a look that was not logged is treated as having happened.

---

## F. Abstention, selective prediction, and false-positive control

### P-05.29 · Selective Question Answering under Domain Shift
Kamath, Jia, Liang · ACL 2020 · https://arxiv.org/abs/2006.09462 · **Status: VERIFIED**

- **Mechanism.** Trains a separate **calibrator** to decide whether to answer, rather than
  thresholding the model's own softmax. The calibrator is trained on model behaviour over
  *diverse out-of-domain* data, which is what makes it work under shift.
- **Key quantitative result.** At a fixed **80% accuracy** target, the calibrator answers
  **56%** of questions vs. **48%** using softmax probability alone — an 8-point coverage gain at
  matched accuracy.
- **Transfer to our eval harness.** The evaluation shape we adopt for abstention: report a
  **risk-coverage curve** — precision as a function of the fraction of candidate findings the
  system is willing to emit. Our "not determinable" category is the abstention arm, and it is
  measured, not merely permitted. "Answers 56% at 80% accuracy" is exactly the format our
  false-positive control target should take.
- **Pitfall.** Abstention can be gamed: a system that abstains on everything hard has perfect
  precision and useless coverage. Precision must never be reported without coverage next to it.

### P-05.30 · A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification
Angelopoulos, Bates · 2021 · https://arxiv.org/abs/2107.07511 · **Status: VERIFIED**

- **Mechanism.** Given any black-box scorer and a held-out calibration set, produces prediction
  sets with a **distribution-free, finite-sample coverage guarantee** at a user-chosen level,
  under exchangeability.
- **Key quantitative result.** Tutorial; the guarantee itself is the result (coverage at the
  user-specified probability, by construction).
- **Transfer to our eval harness.** A principled way to pick the emit/abstain threshold: score
  candidate findings on a calibration split of dev sites, choose the score cut that bounds the
  error rate at our chosen level, then freeze it. This turns "we set the threshold at 0.7" into
  a defensible number.
- **Pitfall.** Exchangeability is the assumption, and websites are **not** exchangeable across
  archetypes — a threshold calibrated mostly on e-commerce sites carries no guarantee on a docs
  site. Calibrate per stratum, or state the caveat plainly (our inference).

---

## G. Inter-annotator agreement

### P-05.31 · Survey Article: Inter-Coder Agreement for Computational Linguistics
Artstein, Poesio · Computational Linguistics 34(4), pp. 555-596 · 2008 ·
https://aclanthology.org/J08-4004/ · **Status: VERIFIED (bibliographic record only)** — the ACL
Anthology landing page confirms title, authors, journal, volume, year and pages; the PDF did not
render as text on retrieval, so no claim below is quoted from the body.

- **Mechanism.** Survey of chance-corrected agreement coefficients for annotation work: the
  kappa family (Cohen's kappa, Fleiss/Carletta's K, Scott's pi) and Krippendorff's alpha, and
  the circumstances under which each applies.
- **Key quantitative result.** **Not extracted — the body was not retrieved. Do not attribute a
  specific threshold recommendation (e.g. alpha >= 0.8) to this paper in the submission without
  opening it first.**
- **Transfer to our eval harness.** Cited as the standard reference for *why* raw percent
  agreement is insufficient and a chance-corrected coefficient must be reported. Our gold-label
  protocol reports Krippendorff's alpha, which handles multiple coders, missing labels, and
  ordinal severity distances — properties raw agreement and Cohen's kappa lack.
- **Pitfall.** Chance-corrected coefficients are unstable and can be misleadingly low when one
  category dominates — exactly our situation on negative-control sites, where nearly every label
  is "no finding". Report alpha alongside the marginal distribution, and prefer per-category
  agreement on rare categories (our inference).

---

## Domain synthesis

Best-supported methodological commitments, in descending order of evidential strength:

1. **Decompose subjective judgment into binary criteria.** CheckEval's +0.45 agreement gain and
   reduced variance (P-05.09), FLASK (P-05.10) and HealthBench's 48,562 per-item criteria
   (P-05.11) all point the same way. This is the most consistent finding in the corpus.
2. **Do not let a judge decide factual correctness.** JudgeBench (P-05.04) shows frontier judges
   near chance on hard objective items, and P-05.08 bounds how far judge labels can substitute
   for real ones. Correctness is checked deterministically against a frozen snapshot; the judge
   is confined to advice quality.
3. **Judges are biased in ways that flip conclusions.** Position bias can invert a headline
   result (P-05.05: 66 of 80 queries from reordering alone), and self-preference is causally
   linked to self-recognition (P-05.06). Swap-and-average and cross-family judging are
   mandatory, not optional.
4. **Reliability is not capability.** tau-bench's pass^k (P-05.20) and the Codex 28.8 -> 70.2
   gap (P-05.22) show that one good run is not evidence of a deterministic system.
5. **Grader weakness inflates scores by a large factor.** SWE-Bench+ (3x collapse, P-05.25) and
   the agentic-benchmark checklist ("up to 100%" estimation error, P-05.24) are the strongest
   warnings against trusting our own first numbers.
6. **Use PR, not ROC, and always report prevalence.** P-05.16, P-05.17.
7. **Cluster by site when computing intervals.** P-05.19. This is the most likely statistical
   error we would otherwise make.
8. **Abstention must be measured as a risk-coverage trade-off**, never as precision alone
   (P-05.29), and its threshold can be set principledly (P-05.30).

**Where the literature is thin or contested for our purposes.**

- *Evaluating advice quality* is the weakest-supported area. FeedEval (P-05.15) is the closest
  analogue and it concerns educational feedback with a downstream revision check we cannot
  replicate. We found no source validating a rubric for *technical remediation advice about
  websites*. Our advice metric is therefore a designed proxy, not a validated instrument, and
  must be described that way.
- *Judge agreement ceilings* are reported on preference tasks (P-05.01, ~80%) and generalise
  poorly to absolute single-item scoring, which is what we need. Treat 80% as an optimistic
  ceiling, not a target.
- *Contamination* is unavoidable for us (P-05.26): the test corpus is the public web. No source
  in this corpus offers a fix; the honest move is disclosure.
- *Krippendorff's alpha thresholds* are widely quoted at 0.8/0.67, but we did not retrieve the
  body of the standard reference (P-05.31), so no threshold is attributed to a source here. The
  one empirical alpha we verified for an automated rubric is **0.83** (P-05.13).
- *Ablation methodology* for multi-component agent systems has no dedicated source in this
  corpus. The ablation design below is built from the paired-comparison statistics of P-05.19
  and the error-attribution idea of P-05.21 — that combination is our inference, not a cited
  method.

---

# Proposed evaluation harness

Designed from the evidence above. This section is written to replace the placeholder body of
`docs/EVALS.md`; it keeps that file's eight measurement targets and four standing commitments
intact and supplies the definitions, thresholds and protocols they promised.

Everything below is our design decision unless it cites a `P-05.NN`. Thresholds are our
judgment calls informed by the cited numbers; where a threshold has no evidential anchor, that
is stated.

## 0. Ground rules that apply to every metric

- **Unit of analysis is the site, not the finding.** Findings on one site are correlated;
  intervals are computed by **site-level cluster bootstrap** (10,000 resamples of sites with
  replacement), never by treating findings as independent (P-05.19).
- **Every number is reported as `point [lo, hi]`** at 95%. A metric computed on fewer than 10
  sites is reported as a raw count and explicitly not as a rate.
- **Correctness is never decided by an LLM judge** (P-05.04, P-05.08). Judges are used only for
  the subjective advice-quality rubric (§4), and only under the bias controls in §4.
- **Everything is run against frozen snapshots.** Each corpus site is captured once (HTML,
  rendered DOM, response headers, robots.txt, screenshots, timing) into a content-addressed
  fixture. All grading, re-running and judging happens against the fixture, not the live site.
  Without this, determinism (§5) is unmeasurable, because the site changes underneath us.
- **Run manifest.** Every result row records: harness version, skill-bundle git SHA, corpus
  snapshot ID, rubric version, model + version for the audit, model + version for each judge,
  date, and wall-clock. A result without a manifest row is not a result.

## 1. Gold-label protocol and agreement

**Procedure.** For each corpus site, two independent labellers produce a gold finding list
*before seeing any audit output* (EVALS.md standing commitment 1). Each labeller works from a
fixed **check taxonomy** — a closed, versioned list of check IDs (e.g. `offsite.schema.missing`,
`onsite.cwv.lcp_slow`) — and for each check ID records one of:

| Label | Meaning |
| --- | --- |
| `PRESENT` | The defect exists on this site. Requires a `locus` (canonical URL + element/selector or byte-offset) and a verbatim `evidence` string from the snapshot. |
| `ABSENT` | Checked, and the site is clean on this dimension. This is what makes negative controls possible. |
| `UNMEASURABLE` | The signal genuinely cannot be observed read-only within our constraints. |
| `N/A` | The check does not apply to this site archetype (e.g. `Product` schema on a personal blog). |

Labelling is AI-assisted: a model proposes candidate labels with evidence, and each human
labeller independently accepts, rejects or edits. This is a **verification** workflow, not a
generation workflow — the human must open the snapshot at the cited locus for every `PRESENT`.

**Blinding.** The AI assistant used for labelling must be a different model family from the one
running the audit (P-05.06), and must never be given the audit's output for that site.

**Agreement metric.** Krippendorff's alpha over the 4-category label, computed **per check ID**,
plus the marginal label distribution alongside it (P-05.31 pitfall). Severity is labelled on an
ordinal scale and gets its own ordinal-weighted alpha.

| Metric | Target | Falsifier |
| --- | --- | --- |
| Krippendorff's alpha, per check ID | **>= 0.80**; provisional acceptance 0.67-0.80 with the check flagged | A check ID that cannot reach 0.67 after one round of definition-sharpening is **cut from the marketplace**, not softened. If two careful humans cannot agree the defect is present, we have no basis for claiming our skill detects it. |
| Fraction of gold `PRESENT` labels whose evidence string is found verbatim in the snapshot | **100%** | Any shortfall means the labelling process itself hallucinates; the gold set is void and must be re-done. |

*Anchor:* the only empirical alpha we verified for a comparable automated-rubric setting is
**0.83** (P-05.13), so 0.80 is a demanding-but-achieved level, not an arbitrary one. The 0.67
floor is a conventional figure we could **not** trace to a retrieved primary source (P-05.31) —
it is used here as our own operational floor and is labelled as such.

**Disagreement resolution.** A third labeller adjudicates. The pre-adjudication alpha is what
gets reported; the post-adjudication set is what gets used. Reporting only the post-adjudication
set hides the real uncertainty.

## 2. Detection metrics, the matching rule, and severity

### 2.1 The matching rule (the highest-stakes definition in this harness)

A predicted finding `P` matches a gold finding `G` iff **all three** hold:

1. **Same check class.** `P.id` and `G.id` map to the same node in the versioned check taxonomy.
   Free-text title similarity is *not* used — it is exactly the "weak test" failure that
   collapsed SWE-bench numbers 3x (P-05.25).
2. **Same locus.** Same canonicalised URL (scheme/host/trailing-slash/query-order normalised),
   **and** — where `G` specifies an element — either the same CSS selector path or an
   `evidence` string with >= 0.6 token-level Jaccard overlap with `G.evidence`.
3. **Grounded evidence.** `P.evidence` appears **verbatim** in the frozen snapshot at the cited
   locus (the FActScore-style atomic grounding check, P-05.12). A finding whose evidence cannot
   be located in the snapshot is a **hard false positive** regardless of whether its claim
   happens to be true — an ungrounded claim is not a finding.

Matching is **one-to-one**, computed by greedy assignment over descending match score; a
predicted finding may consume at most one gold finding and vice versa. Surplus predictions that
duplicate an already-matched gold finding are counted as **false positives**, not ignored —
otherwise a system can spam near-duplicates for free.

Then: `TP` = matched pairs; `FP` = unmatched predictions; `FN` = gold `PRESENT` with no match.

### 2.2 Severity handling

Severity mismatch does **not** break a match, but is tracked separately:

- **Headline precision/recall are severity-blind.**
- **Severity-exact precision** = TP where `P.severity == G.severity`, divided by all predictions.
- A full **severity confusion matrix** is reported. Systematic inflation (predicting `high` where
  gold says `low`) is a distinct, reportable failure — it is the "cry wolf" failure the rubric's
  false-positive penalty is really about.
- **Severity-weighted error**: mean absolute ordinal distance over matched pairs.

### 2.3 Metrics and targets

Reported **per check ID** and **per archetype stratum**, each with the stratum's positive-class
**prevalence** printed next to it (P-05.17). Aggregates are PR-based; **no ROC/AUC is reported**
and PR curves are never linearly interpolated (P-05.16).

| Metric | Target | Falsifier |
| --- | --- | --- |
| Per-check precision | **>= 0.90** | A check below 0.75 precision on dev is removed from the marketplace and logged in the rejected ledger (EVALS.md commitment 4). Given the rubric penalises FPs as heavily as misses, a low-precision check has negative expected value. |
| Per-check recall | **>= 0.70** | A check below 0.40 recall is not detecting the thing it claims to detect; it is cut or redefined to the narrower case it actually finds. |
| Severity-exact rate among TPs | **>= 0.75** | Below 0.5 means our severity field is noise and should be replaced by a two-level (`issue` / `observation`) scale rather than a four-level one. |
| Mean ordinal severity error | **<= 0.4** | Systematic positive bias (mean signed error > +0.5) falsifies the severity calibration and forces a re-anchoring of the severity definitions. |
| Precision uplift over the "always fire" baseline | **> 0** with the CI excluding 0 | If a check's precision is not distinguishable from the stratum prevalence, the check is a constant, not a detector. This is the single cheapest sanity test and it must be run for every check. |

### 2.4 Sample size (the actual calculation)

Wilson/normal half-width for a proportion is approximately `1.96 * sqrt(p(1-p)/n_eff)`. With
clustering, `n_eff = n_findings / deff` where `deff = 1 + (m - 1) * rho` for `m` findings per
site and intra-site correlation `rho` (P-05.19).

Working values: `p = 0.85` (target precision), `m = 12` findings/site, `rho = 0.2` (assumed;
must be estimated from the first real run and the calculation redone).

- `deff = 1 + 11 * 0.2 = 3.2`
- 24 dev sites x 12 = **288 findings** -> `n_eff = 90` -> half-width `= 1.96 * sqrt(0.85*0.15/90)`
  `= +/- 7.4 pp`
- 12 sites x 12 = 144 findings -> `n_eff = 45` -> **+/- 10.4 pp**

**Conclusion: ~24 dev sites is the floor for a precision estimate with a usable interval; below
~12 sites we report counts, not rates.** If the measured `rho` comes out above 0.4, `deff` rises
to 5.4 and the dev corpus must grow to ~40 sites or the interval claim must be dropped — that is
the falsifier for this sizing.

## 3. False-positive control: negative controls and abstention

### 3.1 Negative-control set

Per check dimension, a set of sites hand-verified as `ABSENT` on that dimension (and only that
dimension — a site can be a negative control for schema markup and a positive for CWV).
Constructed by the §1 protocol with both labellers required to agree on `ABSENT`.

| Metric | Target | Falsifier |
| --- | --- | --- |
| **Clean-site FP rate** = fraction of negative-control sites where the check fires at all | **<= 0.05** per check | Any check firing on more than 15% of its own negative controls is removed. This is the rubric's stated failure mode and is not negotiable by argument. |
| **Findings-per-clean-site** | **<= 0.1** | A check that fires once on 5% of clean sites is tolerable; one that fires four times on 5% of them is producing correlated noise and is cut. |

### 3.2 Abstention / `UNMEASURABLE`

The report schema carries an explicit `not_determinable` status alongside `severity`. Abstention
is measured, not merely permitted (P-05.29).

- **Coverage** = fraction of applicable check-site pairs where the system emits a verdict
  (`PRESENT` or `ABSENT`) rather than abstaining.
- **Risk-coverage curve**: precision as a function of coverage, swept over the confidence
  threshold. Reported as a curve *and* as the single operating point we ship.
- **Abstention correctness** (EVALS.md item 3): of the pairs where the system abstained, the
  fraction where gold is `UNMEASURABLE`. This separates honest abstention from dodging.

| Metric | Target | Falsifier |
| --- | --- | --- |
| Coverage at the shipped operating point | **>= 0.70** | Below 0.5 the audit is refusing to do its job; the framing of the checks is wrong, not the threshold. |
| Abstention precision (abstained ∧ gold `UNMEASURABLE`) | **>= 0.60** | Below 0.35 means `not_determinable` is being used as a hedge on measurable things and should be removed from the schema — a hedge that is not correlated with genuine unmeasurability is worse than nothing. |
| Reliability diagram / ECE over confidence-binned findings, 5 fixed bins, per-bin counts shown | ECE **<= 0.10** | If confidence does not correlate with observed precision (monotonicity violated across bins), the confidence field is dropped from the output entirely rather than shipped as decoration (P-05.18). |

**Threshold selection.** The emit/abstain cut is fixed by conformal-style calibration on a
dedicated calibration split of dev sites, **per archetype stratum** (P-05.30), then frozen. It is
never tuned on the held-out set.

## 4. Suggested-action quality

Scored as **atomic binary criteria**, never a 1-5 score (P-05.09, P-05.14). Criteria are
**conditional on check class** (P-05.10) — a schema finding and a performance finding do not
share a rubric — but every class instantiates the same five slots, derived from the
specificity / helpfulness / validity split of P-05.15 plus two of our own:

1. **Targeted** — does the action address the specific locus cited in `evidence`, not the
   general topic?
2. **Mechanism-sound** — is the stated causal path from action to outcome supported by the
   evidence base in `docs/research/papers/`, and does the wording avoid overclaiming causation
   where the underlying evidence is correlational?
3. **Specific enough to execute** — could a competent web developer begin work from this text
   without asking a clarifying question?
4. **Correctly prioritised** — is the stated effort/impact ordering consistent with the
   severity assigned?
5. **Non-manipulative and in-scope** — does it stay recommend-only, and does it avoid tactics
   that game AI retrieval rather than genuinely improve the site?

**Entailment sub-check (deterministic, not judged):** does the action reference at least one
concrete artefact (URL, element, header, file) that exists in the snapshot? A failure here is
scored 0 on criterion 1 without invoking a judge.

**Judge protocol (mandatory bias controls).**

- **Panel of 3 judges from 3 distinct model families** (P-05.07), majority vote per criterion.
- **Cross-family constraint:** no judge may share a family with the audit model (P-05.06). If
  this is impossible, results are labelled "self-judged (upper bound)" and no headline claim is
  made from them.
- **Position control:** every pairwise judgment run in both orders, results averaged; a verdict
  that flips under swap is recorded as a tie (P-05.05).
- **Ordering control:** the finding list is shuffled per judging call.
- **Judge validation:** before use, the panel is validated against a human-labelled subset of at
  least 50 findings; **panel-vs-human agreement is reported next to human-vs-human agreement on
  the same subset** (P-05.01), and stratified by finding difficulty (P-05.04 pitfall).
- **Rubric diagnostics** (P-05.14): per-criterion panel disagreement rate, per-criterion
  variance, and criterion-criterion correlation. A criterion with near-zero variance is
  uninformative and is dropped; a pair with correlation > 0.9 is conflated and merged.

| Metric | Target | Falsifier |
| --- | --- | --- |
| Mean criteria-met fraction, per check class | **>= 0.80** | A class below 0.5 has a broken action template, not a scoring problem. |
| Criterion 5 (non-manipulative) pass rate | **1.00** | Any failure is a blocking defect. Recommending manipulation is a rubric-level disqualifier, not a scoring deduction. |
| Panel-vs-human agreement | within **10 pp** of human-vs-human on the same subset | If the panel is more than 15 pp below the human ceiling, judge scores are dropped from the report and only the human-labelled subset is quoted (P-05.08). |
| Position-swap flip rate | **<= 0.05** | Above 0.15 the rubric wording is order-sensitive and must be rewritten before any score is reported. |

**Honest caveat to carry into the submission:** no source we retrieved validates a rubric for
technical remediation advice. This is a designed proxy, and it is described as one.

## 5. Determinism and stability

Run each frozen snapshot **k = 5** times, identical inputs, default decoding settings as shipped.
Reported as an all-runs-agree rate in the spirit of pass^k, **not** as a mean over runs
(P-05.20, P-05.22).

Three nested stability metrics, from weakest to strictest:

1. **Set stability** — fraction of sites where all 5 runs produce the identical set of
   `(check_id, locus)` pairs.
2. **Severity stability** — set-stable **and** identical severity on every finding.
3. **Full-report stability** — severity-stable **and** identical ordering and identical
   `summary` counts (byte-identical after normalising volatile fields such as timestamps).

Also reported: **per-finding stability** = for each gold-matched finding, the fraction of runs in
which it appeared — this localises *which* checks are flaky rather than only that the report is.

| Metric | Target | Falsifier |
| --- | --- | --- |
| Set stability @ k=5 | **>= 0.90** of sites | Below 0.70 the audit is not deterministic in any useful sense; the offending checks must be rewritten as deterministic script-backed checks rather than model-judgment checks. |
| Severity stability @ k=5 | **>= 0.85** | Below 0.6, severity is emitted by an unstable process and must be derived from a deterministic rule table keyed on the check ID, not inferred per-run. |
| Full-report stability @ k=5 | **>= 0.80** | Failure here specifically indicts report assembly (ordering, dedup, counts), which is fixable by making ordering a total deterministic sort — so a persistent failure means the assembly step has a real bug. |

**Note on the honest interpretation.** Instability is *not* averaged away. A finding present in
3 of 5 runs is reported as unstable, not as a 0.6-confidence finding, unless the confidence
calibration in §3.2 has been validated to support that reading.

## 6. Held-out generalization

**Split.** Sites are partitioned into `dev` (used freely) and `held-out` (budgeted) **before any
skill is written**. Stratified by archetype (e-commerce / docs / SaaS marketing / news / local
business / portfolio / JS-heavy SPA), and additionally balanced across tech stack, size, language
and rendering mode. The held-out set contains at least one archetype **never used in
development**, to measure archetype transfer specifically.

**Hygiene rule (EVALS.md commitment 2, made operational via P-05.28).**

- The held-out set may be run **at most 3 times** before submission.
- Each run is logged in a committed `docs/evals/holdout-log.md` with date, git SHA, the
  pre-registered thresholds being tested, and the pass/fail outcome.
- A held-out run returns **pass/fail against pre-registered thresholds only** — never a ranked
  list of what to fix. Per-finding held-out output is not read.
- An unlogged look is treated as having happened; if the counter would exceed 3, the remaining
  budget is zero and the last logged result stands.

**Contamination disclosure (P-05.26).** Our test corpus is the public web and is by construction
in pretraining data. We do not claim an uncontaminated test set. We claim only that the system
was not *developed against* these sites, and we mitigate by preferring recently-changed pages and
by judging against frozen local snapshots supplied in context.

**Leakage rule (P-05.25).** Any site consulted while writing a skill — even once, even as an
example — is permanently marked `dev` and can never move to held-out. This is tracked in the
corpus manifest, not in memory.

| Metric | Target | Falsifier |
| --- | --- | --- |
| Held-out precision | within **10 pp** of dev precision | A drop greater than 20 pp means the checks are tuned to dev sites. P-05.27 measured 11-14% drops on freshly-collected test sets for a far more constrained task, so we budget headroom accordingly and set dev targets above the numbers we need. |
| Held-out clean-site FP rate | **<= 0.10** (double the dev target) | Exceeding 0.20 falsifies the abstention calibration's transfer across strata, exactly the exchangeability failure P-05.30 warns about. |
| Unseen-archetype recall | **>= 0.50** | If recall collapses on an archetype never seen in development, the skills encode archetype-specific heuristics rather than general checks, and the generalization claim in the submission must be withdrawn. |

## 7. Ablations: does each skill earn its place?

For a marketplace of `n` skills, run `n + 1` configurations on the **dev** corpus: full system,
and full-minus-one for each skill. All configurations run on the **same sites** so the comparison
is **paired** — far more powerful than comparing independent means (P-05.19).

**Primary ablation statistic:** paired difference in a pre-declared composite = severity-weighted
F-score minus a false-positive penalty, with the FP penalty weighted equal to the miss penalty,
matching the rubric's stated symmetry. Reported with a paired bootstrap CI over sites.

**Secondary, per-ablation diagnostics** (P-05.21): when removing skill *S* degrades output, the
harness attributes the degradation to a fixed stage taxonomy — `fetch/crawl`, `extraction`,
`check-logic`, `report-assembly`, `other` — declared before the runs.

**Overlap matrix.** For each pair of skills, the fraction of gold findings that both can detect
alone. High pairwise overlap is direct evidence of padding rather than separation of concerns.

| Metric | Target | Falsifier |
| --- | --- | --- |
| Composite drop when skill *S* is removed | **> 0** with the paired CI excluding 0, for **every** skill | A skill whose removal does not measurably degrade the composite is **merged or cut** before submission. This is the decomposition-is-not-padding rubric line, tested rather than asserted. |
| Pairwise unique-contribution | each skill contributes **>= 10%** of findings that no other skill finds | Two skills with >80% mutual overlap are one skill split for appearances and must be merged. |
| Direction check | no skill whose removal *improves* the composite | If removing a skill improves the system, it is actively harmful and is removed regardless of how good its design looks. |

**Guard against motivated grading (P-05.24).** Any change to the matching rule, rubric or
composite that *increases* scores requires a written justification and a re-run of the negative
controls in the same commit. Changes that decrease scores do not. This asymmetry is deliberate:
outcome-validity failures are silent and always flatter us.

## 8. Runtime and cost against the 5-minute budget

Measured per site on the frozen snapshot **and** on a live fetch (live is the number that
matters for the constraint; snapshot is the number that is reproducible).

Reported per archetype and, critically, at the **tail** — the constraint is a per-site deadline,
so the mean is the wrong statistic.

| Metric | Target | Falsifier |
| --- | --- | --- |
| p50 wall-clock, live, per site | **<= 150 s** | — |
| **p95** wall-clock, live, per site | **<= 270 s** (10% headroom under 300 s) | p95 above 300 s falsifies the crawl budget; the page cap or the rendering policy must change, not the timeout. |
| Worst case: largest site + headless rendering required | **<= 300 s**, or a graceful partial report with an explicit `coverage_incomplete` note | A hard timeout that yields *no* report is a total failure on that site and counts as recall 0 for every check — it must be impossible by construction. Partial-with-disclosure is always preferred to nothing. |
| Zip size of the submitted bundle | **<= 50 MB**, checked in CI | — |
| Requests issued per site; robots.txt compliance | 100% compliance; request rate under the declared politeness cap | Any robots violation or rate-abuse in the logs is a blocking defect, independent of quality scores. |

**Cost accounting.** Token and API cost per site is recorded per configuration so the ablations
in §7 are read at **matched budget** — a skill that improves quality only by spending 3x the
tokens has not shown that decomposition helps.

## 9. What the final report must contain

A results table with, for every metric above: point estimate, 95% CI, the n it was computed on
(sites *and* findings), the stratum, the prevalence, and the manifest row. Plus:

- The **rejected ledger**: every check that failed its own eval, with the number that killed it
  (EVALS.md commitment 4).
- The **held-out log**: all looks, dated.
- The **known-limitations** list, including at minimum: contamination is unavoidable (P-05.26);
  the advice rubric is an unvalidated proxy (P-05.15); several on-site engagement outcomes are
  not observable read-only and are handled by `not_determinable` rather than guessed; and any
  metric whose interval is too wide to support its claim.

## 10. Threats to validity of this harness itself

1. **We write both the checks and the gold labels.** Mitigation: closed taxonomy fixed first,
   labels written before seeing output, two independent labellers, alpha reported
   pre-adjudication. Residual risk remains and is disclosed.
2. **Small n.** 24 dev sites gives roughly +/- 7 pp on precision under our clustering assumption;
   many per-check numbers will have intervals too wide to distinguish 0.85 from 0.95. Where that
   is true, we say so rather than quoting the point estimate.
3. **Judge and audit may share a model family** if only one is available. Then all judge-derived
   numbers are upper bounds and are labelled as such (P-05.06).
4. **The matcher is the whole ballgame.** SWE-Bench+ (P-05.25) is the warning: a lenient matcher
   can inflate results by ~3x. The matcher must be adversarially reviewed by someone who did not
   write it, using deliberately vague synthetic predictions that *should* fail to match.
5. **rho is assumed, not measured.** The sample-size calculation in §2.4 rests on
   `rho = 0.2`. It must be re-estimated from the first full run and the corpus size revisited.

---
