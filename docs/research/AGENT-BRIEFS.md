# Research agent briefs

Verbatim briefs for the eight domain agents that build the source corpus. Stored so the
review is reproducible and re-runnable: relaunching is copy-paste, not re-derivation.

**Run log**

| Date | Result |
| --- | --- |
| 2026-09-01 (run 1) | All 8 launched in parallel; all 8 terminated by an account session rate limit (HTTP 429) before writing any output file. Zero sources collected. |
| 2026-09-01 (run 2) | Relaunched 01, 05, 07, 08 at concurrency 4, with instructions to write output incrementally so a throttle cannot wipe the work. 02, 03, 04, 06 queued behind them. |

**Relaunch guidance:** launching all eight at once on Opus exhausted the session budget.
Relaunch in **batches of 2-3**, and consider a smaller model for the search-and-extract
work, reserving the larger model for the two agents whose output is a design rather than a
list (05 evaluation harness, 08 corpus plan). Agents 01, 05, 07, 08 are the highest value
if the budget only allows four.

---

## Shared preamble (prepend to every brief)

> You are a research agent on a literature review. Your output is a written file, plus a
> compact report back to me.
>
> **Project context.** We are building an "Agent Skill Marketplace" for the Adobe
> University Hackathon 2026 Round 3: a package of agentskills.io-format skills (a
> `SKILL.md` with YAML frontmatter + instructions, optional bundled `scripts/` and
> `references/`) with exactly one entrypoint skill. Pointed at ANY website, it audits the
> site read-only and emits one JSON report of findings (each with `id`, `title`,
> `severity`, `evidence`, `suggested_action`) plus a counts-by-severity summary. It must
> cover two halves: (a) OFF-SITE DISCOVERABILITY — why an AI assistant doesn't find, cite,
> or correctly represent the brand; (b) ON-SITE ENGAGEMENT — why visitors who arrive don't
> stay. It is graded on the skill design itself, on unseen sites, with false positives
> penalized as heavily as misses. Constraints: recommend-only, read-only, robots.txt
> respected, no authenticated areas, no rate abuse, <5 minutes per typical site, ≤50 MB zip.
>
> **Hard rules on honesty.**
> - Every entry MUST have a real URL you actually retrieved. Use WebSearch and WebFetch.
> - Mark each entry `Status: VERIFIED` (you fetched and read the abstract/paper) or
>   `Status: SEARCH-ONLY` (plausible title/venue in search results, could not open it).
> - Never invent a title, author list, venue, year, arXiv ID, or finding. If you cannot
>   verify something exists, DROP it rather than guess.
> - Label your own inferences `(our inference)`.
> - Do not pad to hit the target count. 11 real sources beat 15 with 4 invented.
> - Do not touch any file in the repo other than your assigned output file.

---

## 01 — GEO, AI search visibility, and LLM citation behaviour
**Output:** `docs/research/papers/01-geo-ai-search-visibility.md` · **Target:** 13-15 sources

Core evidence base for the discoverability half. Search for and verify:
- "GEO: Generative Engine Optimization" (Aggarwal et al., KDD 2024) plus follow-ups,
  replications, critiques
- Empirical studies of which sources LLM search products (ChatGPT Search, Perplexity,
  Google AI Overviews, Gemini, Copilot) actually cite — source-selection bias, domain
  concentration, citation accuracy/misattribution (incl. the Tow Center / Columbia
  Journalism Review AI-search citation studies)
- RAG retrieval and passage-selection dynamics: what makes a chunk retrievable and
  quotable (chunking, passage granularity, lexical vs. dense retrieval, extractiveness)
- Attribution and citation faithfulness (ALCE, "Enabling LLMs to Generate Text with
  Citations", AIS / attributable-to-identified-sources evaluation)
- Ranking manipulation of conversational search engines, adversarial visibility work, LLM
  SEO spam — needed to separate legitimate recommendations from manipulative tactics,
  which we must not recommend
- AI-crawler access policy: robots.txt / AI-bot blocking trends ("Consent in Crisis: The
  Rapid Decline of the AI Data Commons" or similar), GPTBot/CCBot/ClaudeBot access data,
  the llms.txt proposal and any empirical evaluation of it
- Work measuring how brand/entity mentions across the wider web affect LLM answers

Per-source schema: `P-01.NN` · Full title · Authors/venue/year · URL · Status ·
**Mechanism** (what the system *does* — the causal behaviour, not the paper's
contribution) · **Key quantitative result** (with scope, or "none reported") · **Transfer
to our audit** (a concrete site-agnostic check measurable read-only) · **False-positive
risk** · **Eval implication**.

Close with `## Domain synthesis`: the 5-8 best-supported mechanisms, and where the
literature is thin, contested, or rests on a single non-replicated study.

---

## 02 — Agent architecture and reusable skill design
**Output:** `docs/research/papers/02-agent-architecture-skill-design.md` · **Target:** 13-15

Answers: *what does research say about authoring agent instructions and skill libraries so
behaviour is reliable, deterministic, and generalizes?* Cover:
- ReAct, Reflexion, Self-Refine, Plan-and-Solve, Tree of Thoughts, Least-to-Most,
  Self-Consistency, CoT and its faithfulness critiques
- Voyager (LLM skill library — directly analogous to a skill marketplace), ADAS
  "Automated Design of Agentic Systems", agent symbolic learning, LATS, ExpeL
- CoALA (Cognitive Architectures for Language Agents) and procedural/semantic/episodic
  memory distinctions
- Toolformer; tool-use and function-calling reliability; tool-selection error taxonomies;
  effect of tool-count on selection accuracy
- Structured-output reliability: JSON mode, constrained/grammar-constrained decoding, and
  what it costs in quality
- Determinism and variance: LLM output variance at temperature 0, prompt sensitivity,
  position/ordering effects, IFEval and successors
- Checklist/rubric-driven prompting; decomposing a judgment into atomic verifiable
  sub-questions
- Progressive disclosure and context management; "lost in the middle"; long-context
  degradation
- Prompt/skill portability across providers (our skills must be provider-neutral)

Per-source schema: `P-02.NN` · … · **Mechanism** · **Key quantitative result** ·
**Transfer to our skill design** (a concrete authoring decision, specific enough to act on
when writing a `SKILL.md`) · **Known failure mode** · **Eval implication**.

Close with `## Domain synthesis`: the 5-8 best-supported authoring rules, **plus an
explicit list of techniques that sound appealing but are not well supported** (e.g. where
CoT or self-critique has been shown not to help).

---

## 03 — Multi-agent orchestration, decomposition, and failure modes
**Output:** `docs/research/papers/03-multi-agent-orchestration.md` · **Target:** 13-15

Answers: *when does splitting work across skills help, when does it hurt, and what
orchestration pattern is most reliable?* The rubric line at stake: decomposition must
reflect genuine separation of concerns and not be padding. Cover:
- Orchestrator/worker, hierarchical, router, and blackboard patterns
- MetaGPT, AutoGen, CAMEL, ChatDev, AgentVerse — what they *demonstrate*, not propose
- **Failure-mode taxonomies**, especially "Why Do Multi-Agent LLM Systems Fail?" (MAST).
  This is the single most valuable thing to bring back.
- Multi-agent debate/ensembling: papers claiming gains AND papers showing gains vanish
  against a strong single-agent baseline at matched compute
- Error propagation and compounding error over agent chains; chain length vs. success rate
- Cost/latency of multi-agent vs. single agent at matched budget (we have <5 minutes)
- Decomposed prompting and sub-question generation; when decomposition improves
  faithfulness
- Result aggregation: merging findings from independent workers, deduping overlapping
  conclusions, reconciling disagreement
- Context/information loss at agent hand-off boundaries
- "Agent as a tool" / skill invocation semantics and interface contracts

Per-source schema: `P-03.NN` · … · **Mechanism** · **Key quantitative result** (with the
baseline it was measured against — flag weak or compute-unmatched baselines) · **Transfer
to our marketplace** (how many skills, boundaries where, how the entrypoint composes) ·
**Failure mode to defend against** · **Eval implication**.

Close with `## Domain synthesis`: evidence-backed decomposition principles; a direct answer
to "how many skills should this marketplace have, split along what axis?"; the failure
modes the entrypoint must defend against; and where this literature overclaims.

---

## 04 — Web agents and machine readability of pages
**Output:** `docs/research/papers/04-web-agents-page-understanding.md` · **Target:** 13-15

Answers: *how do machines actually read web pages, and what are the measurable,
generalizable signals of machine-unreadability?* Cover:
- Benchmarks and what they reveal about page representation: WebArena, VisualWebArena,
  Mind2Web / Multimodal-Mind2Web, WebVoyager, WebShop, WorkArena, BrowserGym/AgentLab,
  GAIA, AssistantBench, WebCanvas, Online-Mind2Web
- **Page representation**: raw HTML vs. DOM vs. accessibility tree vs. screenshot vs.
  markdown/text extraction — measured accuracy differences; HTML pruning/compression for
  LLMs (AutoWebGLM, HTML-pretrained models, ReaderLM / html-to-markdown work if
  research-backed)
- Boilerplate removal and main-content extraction (Readability evaluations, CleanEval and
  successors, the Trafilatura evaluation paper)
- Client-side rendering: measurements of how much content is missing without JS
  execution; raw HTTP fetch vs. headless-rendered DOM; SPA indexability
- Crawler behaviour and politeness: robots.txt compliance research, crawl-delay, crawl
  budget, sitemap effectiveness, web-measurement methodology
- Cloaking, bot detection, differential serving — our audit must not be fooled by it and
  must not itself evade detection
- How AI crawlers differ from classic search crawlers (do they execute JS? follow
  sitemaps?)
- Accessibility-tree research and the overlap between machine readability and human
  accessibility

Per-source schema: `P-04.NN` · … · **Mechanism** · **Key quantitative result** ·
**Transfer to our audit** (the check plus the comparison it requires, e.g. "fetch without
JS vs. rendered DOM, compare extracted main-text token overlap") · **False-positive
risk** · **Runtime cost** (flag if headless rendering is required) · **Eval implication**.

Close with `## Domain synthesis`: machine-readability signals ranked by evidence strength
× cheapness; a recommended crawl strategy for a <5-minute budget (page cap, sampling
across page types, when to pay for rendering); and signals that look attractive but are
unreliable.

---

## 05 — Evaluation methodology  ⭐ highest value
**Output:** `docs/research/papers/05-evaluation-methodology.md` · **Target:** 13-15

Answers: *how do we rigorously measure detection quality, action quality, determinism and
generalization for a system that emits findings about an arbitrary website?* Cover:
- **LLM-as-a-judge**: MT-Bench/Arena judge validation, G-Eval, Prometheus, JudgeBench —
  AND the critique literature: position bias, verbosity/length bias, self-preference,
  judge–human agreement ceilings, sensitivity to rubric wording
- **Checklist/rubric-decomposed evaluation**: CheckEval, FLASK, HealthBench-style
  expert-written rubrics, FActScore-style atomic-fact decomposition
- **Detection metrics**: precision/recall/F1 pitfalls under class imbalance, precision@k,
  calibration (ECE, reliability diagrams), ROC vs. PR curves for rare positives,
  cost-sensitive evaluation with asymmetric FP/FN costs
- **Reliability and variance**: pass@k vs. pass^k, test-retest reliability, variance in
  agent benchmarks, runs needed for significance, "Adding Error Bars to Evals"
- **Benchmark methodology critiques**: τ-bench / τ²-bench, SWE-bench construction
  critiques, contamination and leakage, construct validity of agent benchmarks
- **Inter-annotator agreement**: Cohen's/Fleiss' kappa, Krippendorff's alpha, and the
  agreement level required to trust a gold set
- **Abstention / selective prediction / conformal prediction** for false-positive control
  — how a system says "not determinable" instead of emitting a wrong finding
- **Ablation methodology** for multi-component systems
- Evaluating *recommendation/advice* quality: actionability, specificity, harm of bad
  advice

Per-source schema: `P-05.NN` · … · **Mechanism** · **Key quantitative result** ·
**Transfer to our eval harness** · **Pitfall** (how the method misleads if applied naively).

Then — **the most important part of the output** — a `## Proposed evaluation harness`
section designed from the evidence, covering: (1) gold-label protocol and how agreement is
measured, given we label with AI assistance; (2) detection metrics including the
predicted-to-gold finding **matching rule** and severity-mismatch handling; (3)
false-positive control with a deliberate negative-control set and an "unmeasurable"
category; (4) suggested-action quality as atomic binary criteria; (5) determinism repeat-run
protocol and stability metric; (6) held-out generalization protocol, stratification,
contamination avoidance; (7) ablations proving each skill earns its place; (8) runtime/cost
against the 5-minute budget. For each: the metric, the target threshold, and **what result
would falsify our design**.

---

## 06 — Structured data, entity grounding, corroboration, freshness
**Output:** `docs/research/papers/06-structured-data-entity-grounding.md` · **Target:** 13-15

Grounds two Round-2 mechanisms: explicit-and-unambiguous facts get extracted; corroborated
facts get believed; ambiguous entities get confused. Cover:
- **Structured data at web scale**: Web Data Commons schema.org/JSON-LD adoption and
  quality studies; structured-data error research; whether markup measurably improves
  extraction; microdata/RDFa/JSON-LD comparisons
- **Information extraction from HTML**: closed/open IE, table extraction, attribute-value
  extraction from product pages (WDC product corpus, OpenTag/MAVE-style work), the measured
  gap between explicit text and implied information
- **Entity linking and disambiguation**: BLINK, ReFinED, GENRE, EL benchmarks, NIL /
  unlinkable entities, name ambiguity, LLM-era entity linking; knowledge-graph presence
  (Wikidata/Wikipedia) as a disambiguation anchor and any measurement of its effect on LLM
  answers
- **Corroboration**: truth discovery, fact verification (FEVER and successors),
  multi-source claim verification, evidence aggregation; frequency of a fact in
  pretraining ↔ recall accuracy
- **Freshness**: FreshQA/FreshLLMs, TempLAMA and temporal knowledge probing, staleness in
  RAG, dateline/last-modified signals, decay of accuracy on time-sensitive queries
- **Long-tail entity hallucination**: popularity ↔ accuracy relationships ("When Not to
  Trust Language Models" / PopQA-style findings)
- **Quotability**: what makes a sentence extractable standalone — self-containedness,
  decontextualization, atomic claim extraction

Per-source schema: `P-06.NN` · … · **Mechanism** · **Key quantitative result** ·
**Transfer to our audit** (for off-site checks, specify what is realistically measurable
without paid APIs) · **False-positive risk** (e.g. a site with no products correctly has no
Product schema) · **Eval implication**.

Close with `## Domain synthesis`: extraction/trust mechanisms ranked; a concrete, cheap,
read-only method for assessing entity ambiguity and off-site corroboration for an arbitrary
brand — stating plainly what is **not** measurable within our constraints; and freshness
signals with their traps (evergreen content is not stale).

---

## 07 — On-site engagement: observable page properties ⭐ hardest half
**Output:** `docs/research/papers/07-onsite-engagement-evidence.md` · **Target:** 13-15

The constraint that defines this brief: **we cannot measure bounce rate or dwell time for
an arbitrary site.** We observe only page-side properties. So the research needed is
whatever links an OBSERVABLE PAGE PROPERTY to a MEASURED ENGAGEMENT OUTCOME. Cover:
- **Performance ↔ engagement**: Core Web Vitals (LCP, INP, CLS) research, CrUX / HTTP
  Archive analyses linking them to bounce and conversion, load-time abandonment studies,
  the research behind the CWV thresholds, INP replacing FID, mobile vs. desktop
- **Dwell time and bounce**: dwell time as a relevance/satisfaction signal, "good
  abandonment", post-click behaviour modelling, known weaknesses of bounce rate
- **Information foraging / information scent** (Pirolli & Card and successors) and
  empirical tests of scent in navigation
- **Readability and comprehension**: reading-ease measures and their validity, text
  complexity ↔ task success, scanning behaviour (F-pattern eye-tracking) — flagging which
  of this is practitioner rather than peer-reviewed research
- **Accessibility ↔ usability**: WCAG conformance and measured task success; what fraction
  of real barriers automated tools (axe et al.) actually catch — needed to calibrate our
  claims
- **First impressions**: visual complexity and prototypicality (Lindgaard 50ms, Tuch et
  al.), aesthetics ↔ perceived usability
- **Interstitials, popups, ads, layout shift** as abandonment causes; ad density ↔
  engagement
- **Mobile usability**: viewport, tap targets, responsive design, measured mobile
  abandonment
- **Navigation and IA**: menu depth/breadth, search vs. browse, orientation and wayfinding
- **Trust signals**: Stanford Web Credibility work and modern replications
- **Content structure ↔ task completion**: headings, chunking, answer-first writing

Additional honesty rules for this domain: mark `Type: PEER-REVIEWED | INDUSTRY (not
peer-reviewed)` and `Evidence strength: CAUSAL | CORRELATIONAL | THEORETICAL |
PRACTITIONER OBSERVATION`. Widely-repeated industry statistics are often unsourced or
misattributed — **if a number cannot be traced to its primary source, say so explicitly
rather than repeating it**. Distinguish correlation from causation in every entry.

Per-source schema adds: **Observable proxy** — what a read-only crawler can actually
measure on an arbitrary page; *if it is not observable without analytics or user testing,
say so plainly — that is a valuable finding.*

Close with `## Domain synthesis`: signals ranked by evidence strength × crawler
observability; an explicit list of engagement problems that are REAL but NOT observable
read-only, and how to handle them honestly ("not determinable" vs. omit); how to assign
severity when most evidence is correlational; and a warning list of popular engagement
"best practices" that lack good evidence.

---

## 08 — Web corpora and sampling methodology  ⭐ enables train/test split
**Output:** `docs/research/papers/08-web-corpora-and-sampling.md` · **Target:** 12-15

Two parts.

**Part 1 — corpora, with real access terms.** Tranco (the manipulation-resistant top-sites
ranking + the critique literature on top-list instability/bias); HTTP Archive and the
Chrome UX Report (fields, BigQuery access, free tier, representativeness); Common Crawl
(WARC/WAT/WET, index, host/domain graphs, coverage-bias research); Web Data Commons
(schema.org extractions, product corpora); ClueWeb22 and similar research corpora; WebArena
/ VisualWebArena / WorkArena self-hosted site clones and Mind2Web / Online-Mind2Web site
lists as reproducible targets; any curated corpora of accessibility or site-quality labels;
any public dataset of AI-assistant citations. **Flag anything requiring payment,
credentials, or an application process, and record licences — "unclear" is an acceptable
and preferred answer to guessing.**

**Part 2 — sampling and split methodology (the important half).** Stratified sampling and
which strata matter (archetype: e-commerce / docs / SaaS marketing / news / local business
/ portfolio / SPA; tech stack; size; language; region; popularity tier); sample-size
determination for detection-metric confidence intervals — give the actual formula and a
number; benchmark contamination and adaptive overfitting (reusable holdout, ImageNet/CIFAR
replication studies); negative-control construction; reproducibility of web measurement
under change (WARC capture, Wayback as a fixture source and its limits); ethics and
legality of research crawling.

Per-source schema: `P-08.NN` · … · `Kind: PAPER | DATASET-DOC | TOOL` · **What it gives
us** · **Access** (be specific; flag blockers) · **Licence** · **Transfer to our corpus
plan** · **Limitation / bias**.

Then — **the most important part** — `## Proposed corpus & split plan`: (1) dev corpus size,
sampling procedure, stratification, source — an executable procedure; (2) held-out test
corpus size, stratification, and the hygiene rule (when it may be run, how many times, what
happens if we look at it); (3) negative-control set construction per dimension; (4)
adversarial/edge set (JS-only SPA, robots-blocked, one-page site, huge site, non-English,
paywalled, parked domain, cloaking) and what each tests; (5) snapshotting for
reproducibility; (6) sample size for a usable confidence interval on detection
precision/recall, with the calculation; (7) what goes in the ≤50 MB submission zip vs. what
stays in the dev repo.
