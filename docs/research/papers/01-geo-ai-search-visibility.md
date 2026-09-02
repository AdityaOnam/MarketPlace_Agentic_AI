# 01 — GEO, AI search visibility, and LLM citation behaviour

Source corpus for the **off-site discoverability** half of the Agent Skill Marketplace
audit: why an AI assistant fails to find, cite, or correctly represent a brand.

**Honesty conventions used in this file**

- Every entry has a URL that was actually retrieved during this review.
- `Status: VERIFIED` = the abstract/paper page was fetched and read in this session.
  `Status: SEARCH-ONLY` = title/venue appeared in search results but the page could not be
  opened; treat the finding as unconfirmed.
- No title, author, venue, year, arXiv ID, or numeric result in this file is reconstructed
  from memory. Anything that could not be confirmed was dropped rather than guessed.
- Statements that are our own reasoning, not the source's claim, are tagged
  `(our inference)`.

**Standing caveat for this domain.** Almost all quantitative results here are measured
against a *specific* generative engine at a *specific* time. These products change
weekly. Any check we ship must therefore test a **property of the site** that the
literature says is causally upstream of retrieval/citation — never a claim about what a
particular engine currently does. (our inference)

---

## P-01.01 · GEO: Generative Engine Optimization

- **Authors/venue/year:** Pranjal Aggarwal, Vishvak Murahari, Tanmay Rajpurohit, Ashwin
  Kalyan, Karthik Narasimhan, Ameet Deshpande. Accepted to KDD 2024. arXiv v1 16 Nov 2023,
  v3 28 Jun 2024.
- **URL:** https://arxiv.org/abs/2311.09735
- **Status:** VERIFIED

**Mechanism.** A "generative engine" answers a query by retrieving a set of candidate web
sources and having an LLM synthesise them into one answer with inline attributions.
Visibility for a source is therefore not a rank position but *how much of the generated
answer is drawn from, and attributed to, that source*. Because the synthesis step is an
LLM reading source text, edits to the **wording of a page** — not just its link graph —
change how much of it survives into the answer. GEO formalises this as black-box
optimisation over page text against a visibility metric.

**Key quantitative result.** "GEO can boost visibility by up to 40% in generative engine
responses," measured on GEO-bench (queries across multiple domains with associated web
sources). The paper explicitly reports that **efficacy varies across domains**, motivating
domain-specific optimisation.

**Transfer to our audit.** This is the licence for the whole off-site half: page-level
textual properties are a legitimate, measurable lever on AI answer inclusion. Concretely,
audit whether a page's key claims are stated in *quotable, self-contained, attributable*
form — statistics with units and dates, direct quotation, cited authority — rather than
only as diffuse marketing prose. Each of these is checkable read-only from extracted main
text.

**False-positive risk.** High, if applied literally. The "40%" is an *upper bound across
the best method per domain*, not an expected effect for an arbitrary site; the headline
number is the strongest single result, not the average. Also, several GEO-style edits shade
into content manipulation (adding statistics or quotations that were not there). We must
recommend only edits that make **true** existing information more extractable, and never
recommend fabricating authority signals. Flagging "this page has no statistics" on a page
where statistics would be inappropriate (an About page, a contact page) is a clear FP.

**Eval implication.** Any GEO-derived check needs a negative-control page type where the
check should *not* fire. Report per-page-type precision, not a single pooled number, since
the source paper's own headline finding is that effects are domain-dependent.

---

## P-01.02 · Enabling Large Language Models to Generate Text with Citations (ALCE)

- **Authors/venue/year:** Tianyu Gao, Howard Yen, Jiatong Yu, Danqi Chen. EMNLP 2023.
  arXiv v1 24 May 2023, v2 31 Oct 2023.
- **URL:** https://arxiv.org/abs/2305.14627
- **Status:** VERIFIED

**Mechanism.** Splits "answering with citations" into an end-to-end pipeline — retrieve
supporting evidence, then generate an answer whose sentences carry citations — and scores
it on three axes: fluency, correctness, and **citation quality** (is the cited passage
actually entailing the sentence). The load-bearing insight for us: a source only earns a
citation if a *retrievable passage* from it *entails* a sentence the model wanted to
write. Retrievability and entailment are separate failure points.

**Key quantitative result.** On the ELI5 dataset, "even the best models lack complete
citation support 50% of the time." Automatic metrics are reported as strongly correlated
with human judgements.

**Transfer to our audit.** Check that a page contains passages that could *stand alone as
evidence for a claim*: a passage that answers a likely question in one place, without
requiring the surrounding page for context. Read-only proxies: presence of headed sections
whose text answers the heading; declarative sentences that name the subject rather than
using unresolved pronouns/"we"; FAQ-style question→answer pairs. All measurable from
extracted main text.

**False-positive risk.** Moderate. "Not self-contained" is a fuzzy judgement and an LLM
auditor will over-fire on stylistically informal but perfectly clear pages. Needs a high
bar and evidence quoting.

**Eval implication.** ALCE's structure argues for scoring our own findings the way ALCE
scores citations: each finding must carry an `evidence` string that *entails* the claimed
problem. An eval criterion falls out directly — does the quoted evidence actually support
the finding? This is a cheap, high-signal FP detector.

---

## P-01.03 · Consent in Crisis: The Rapid Decline of the AI Data Commons

- **Authors/venue/year:** Shayne Longpre, Robert Mahari, Ariel Lee, Campbell Lund, et al.
  (large author list; MIT Data Provenance Initiative and collaborators). arXiv 2407.14933,
  submitted 20 Jul 2024, revised 24 Jul 2024. 41 pages.
- **URL:** https://arxiv.org/abs/2407.14933
- **Status:** VERIFIED

**Mechanism.** Longitudinal audit of consent signals — `robots.txt` and Terms of Service —
across 14,000 web domains underlying AI training corpora. Documents a rapid rise in
AI-specific crawler restrictions, and — critically for an auditor — **systematic
inconsistency between what a site's ToS says and what its robots.txt permits**.

**Key quantitative result.** Within one year (2023–2024), restrictions rendered "~5%+ of
all tokens in C4, or 28%+ of the most actively maintained, critical sources in C4, fully
restricted from use." For ToS-expressed crawling restrictions, "a full 45% of C4 is now
restricted."

**Transfer to our audit.** Two concrete read-only checks. (1) Parse `/robots.txt` and
report which AI-relevant user-agents are disallowed — this is the single cheapest, most
defensible off-site finding available, since it is a direct causal block on the retrieval
step. (2) Report *inconsistency*: agent tokens disallowed while the site simultaneously
publishes content clearly intended for discovery. The paper's own finding that
robots.txt/ToS disagree at scale means we should present this as an **observation to
reconcile**, not automatically as a defect.

**False-positive risk.** High if we treat blocking as an error. Blocking AI crawlers is a
deliberate, legitimate publisher choice, and the paper frames it as expressed preference,
not misconfiguration. Our finding must be phrased as "AI assistants cannot retrieve this
site; if that is unintended, here is the line responsible" — with severity contingent on
apparent intent. Also: robots.txt syntax errors and overbroad `Disallow: /` under a
wildcard agent are genuinely accidental and are the defensible high-severity case.

**Eval implication.** Needs a negative-control set of sites that *intentionally* block AI
crawlers. If our audit reports those as high-severity defects, the check is
mis-specified. (our inference)

---

## P-01.04 · Ranking Manipulation for Conversational Search Engines

- **Authors/venue/year:** Samuel Pfrommer, Yatong Bai, Tanmay Gautam, Somayeh Sojoudi.
  EMNLP 2024 (Main). arXiv v1 5 Jun 2024, v3 25 Sep 2024.
- **URL:** https://arxiv.org/abs/2406.03589
- **Status:** VERIFIED

**Mechanism.** Conversational search engines load retrieved page text into the LLM context
for summarisation. Because that text enters the context window, **page content is an attack
surface**: adversarial strings injected into a site's own pages can promote it in the
engine's referenced-source ordering. The paper also measures the *non-adversarial* baseline
and finds LLMs "vary significantly in prioritizing product name, document content, and
context position."

**Key quantitative result.** A tree-of-attacks-based jailbreaking technique "reliably
promotes low-ranked products," and the attacks "transfer effectively" to production systems
including perplexity.ai. (Effect sizes are per-model in the paper body; the abstract states
reliability and transfer rather than a single headline number.)

**Transfer to our audit.** Two things. (1) The **guardrail**: this paper is the concrete
evidence that GEO-adjacent tactics have a manipulative tail. Our skill must have an
explicit non-recommendation list — no hidden text, no instruction-like strings aimed at
retrievers, no invisible/off-screen keyword blocks. (2) A **defensive check**: detect
hidden or visually-suppressed text on the audited site (display:none, zero-opacity,
off-viewport, white-on-white, or text present in HTML but absent from rendered output) and
report it as a risk, since it is both a manipulation signal and something an assistant may
ingest.

**False-positive risk.** Moderate-to-high for hidden-text detection: `display:none` is
ubiquitous and legitimate (collapsed accordions, mobile/desktop variants, screen-reader-only
labels, off-canvas menus). A naive "hidden text" check will fire on nearly every modern
site. Only unusually large hidden text blocks that differ substantively from visible content
are defensible, and even then the finding should be low severity.

**Eval implication.** Two-sided eval. First, a *behavioural* eval on our own skill: given a
site with weak visibility, does the skill ever recommend a manipulative tactic? Any
occurrence is a hard failure, not a scored miss. Second, the hidden-text check needs its
negative control built from ordinary sites with accordions and skip-links.

---

## P-01.05 · Measuring Attribution in Natural Language Generation Models (AIS)

- **Authors/venue/year:** Hannah Rashkin, Vitaly Nikolaev, Matthew Lamm, Lora Aroyo,
  Michael Collins, Dipanjan Das, Slav Petrov, Gaurav Singh Tomar, Iulia Turc, David
  Reitter. arXiv 2112.12870, v1 23 Dec 2021, v2 2 Aug 2022. (Later published in
  *Computational Linguistics*; only the arXiv record was verified here.)
- **URL:** https://arxiv.org/abs/2112.12870
- **Status:** VERIFIED

**Mechanism.** Defines **Attributable to Identified Sources (AIS)**: a generated statement
is attributable if a generic hearer, given the cited source, would affirm "according to this
source, <statement>". Operationalised as a **two-stage annotation pipeline** — stage 1 asks
whether the statement is even *interpretable standalone* (is it a self-contained proposition
whose referents resolve without extra context); only statements that pass stage 1 go to
stage 2, which asks whether the source supports them.

**Key quantitative result.** No single headline metric; the contribution is the framework
plus human-evaluation validation across three tasks (two conversational QA datasets, a
summarisation dataset, a table-to-text dataset), with released annotation guidelines.

**Transfer to our audit.** The stage-1 **interpretability gate** is the most directly
reusable idea in this whole brief. A page's sentences must survive decontextualisation to
be attributable to it. Concrete read-only check: sample the page's main-content sentences
and test whether each names its subject rather than relying on an antecedent elsewhere on
the page ("Our platform does X" with the brand named nowhere nearby; "It supports 12
languages" with no resolvable "it"). Pages whose headline value propositions are all
pronoun-anchored are structurally hard to quote.

**False-positive risk.** Moderate. Pronoun use is normal English; only a *concentration* of
unresolvable references in the passages that carry the page's key facts is a real problem.
A per-sentence check will over-fire badly; a per-page-density check with a threshold is
safer. (our inference)

**Eval implication.** Adopt AIS's two-stage structure for grading our own report:
(1) is the finding's `evidence` an interpretable standalone quote, (2) does it support the
finding. Also adopt its lesson that attribution judgement needs *written guidelines* before
annotation — our gold-labelling protocol needs the same.

---

## P-01.06 · AI Search Has a Citation Problem (Tow Center)

- **Authors/venue/year:** Klaudia Jaźwińska and Aisvarya Chandrasekar, Tow Center for
  Digital Journalism, Columbia Journalism Review, 6 March 2025.
- **URL:** https://www.cjr.org/tow_center/we-compared-eight-ai-search-engines-theyre-all-bad-at-citing-news.php
- **Status:** VERIFIED
- **Type:** Research-institute report (Tow Center), **not peer-reviewed**.

**Mechanism.** Tests the *reverse* direction from GEO: given a verbatim excerpt from a known
article, can the engine correctly identify and cite its source? This isolates the
attribution/misattribution failure mode from the retrieval failure mode. It shows that even
when a brand's content is unambiguously in the index, the assistant may credit it to the
wrong publisher, to a syndicated copy, or to a fabricated URL.

**Key quantitative result.** 1,600 queries (20 publishers × 10 articles × 8 tools) across
ChatGPT Search, Perplexity, Perplexity Pro, DeepSeek Search, Copilot, Grok-2, Grok-3 (beta),
Gemini. **Over 60% of responses were incorrect overall**; per-engine error rates ranged
from **37% (Perplexity)** to **94% (Grok 3)**. Over 50% of Gemini and Grok 3 responses
contained fabricated or broken URLs (Grok 3: 154/200 citations led to error pages).
DeepSeek misattributed sources 115/200 times. Chatbots rarely declined to answer. Engines
frequently cited **syndicated copies (Yahoo News, AOL) rather than the original
publisher** — and Perplexity Pro correctly identified excerpts from content it was blocked
from, including all 10 National Geographic articles despite the crawler block.

**Transfer to our audit.** Three checks fall out. (1) **Canonicalisation**: is there a
`rel=canonical`, is it self-consistent, and does the site consolidate duplicate/syndicated
versions? The syndication finding is direct evidence that duplicate copies steal
attribution. (2) **Link stability**: broken internal links and unstable URLs make fabricated
or dead citations more likely; a crawler can measure 404 rates and redirect chains
read-only. (3) **Unambiguous publisher identity on every page** — a machine-readable
publisher/organisation identity so an excerpt lifted from the page carries its owner with
it.

**False-positive risk.** Low-to-moderate for canonical/404 checks (mechanical, verifiable).
But we must not report *engine* misbehaviour as a *site* defect: the National Geographic
result is the engine violating a block, and nothing the site could fix. Any finding derived
from this source must point at something the site owner controls.

**Eval implication.** Confirms that "the assistant describes the brand wrongly" is a real
and common outcome, so our audit's discoverability half should be scored on
*misrepresentation risk factors* the site controls, not on our ability to predict a
particular engine's output. Also: the reported instability of repeated identical prompts is
a warning that any eval of ours that queries a live assistant will be non-deterministic and
needs repeat runs.

---

## P-01.07 · Source Coverage and Citation Bias in LLM-based vs. Traditional Search Engines

- **Authors/venue/year:** Peixian Zhang, Qiming Ye, Zifan Peng, Kiran Garimella, Gareth
  Tyson. arXiv 2512.09483 (cs.CL / cs.CY), 10 December 2025.
- **URL:** https://arxiv.org/abs/2512.09483
- **Status:** VERIFIED

**Mechanism.** Compares the *source-selection layer* of LLM search engines against
traditional search engines at scale, and runs a feature-based analysis to identify which
source properties predict selection. The framing that matters for us: LLM search draws from
a partly **different** pool than classic search, so classic SEO rank is not a sufficient
proxy for AI visibility.

**Key quantitative result.** 55,936 queries across six LLM search engines and two
traditional engines. LLM search engines cite with **greater domain diversity** than
traditional engines; **37% of domains are unique to LLM search engines**. They do **not**
outperform traditional engines on credibility, political neutrality, or safety metrics.

**Transfer to our audit.** Justifies auditing AI-discoverability as a distinct dimension
from classic SEO — a site can rank well and still be invisible to LLM search, and vice
versa. Practically: do not simply re-run an SEO checklist and relabel it "GEO". The audit
should check retrieval-layer prerequisites (crawler access, clean extractable text, stable
canonical URLs, machine-readable identity) separately from rank-oriented signals.

**False-positive risk.** Low as framing; but this paper does not license claiming any
specific site-side feature causes selection — the feature analysis is in the paper body and
was not verified here. Do not quote specific feature weights from this source.

**Eval implication.** Argues against using classic SEO tool output as our gold labels. Our
gold set must be labelled against retrieval/citation-relevant criteria directly. (our
inference)

---

## P-01.08 · News Source Citing Patterns in AI Search Systems

- **Authors/venue/year:** Kai-Cheng Yang. arXiv 2507.05301 (cs.IR), 7 July 2025. 15 pages,
  7 figures.
- **URL:** https://arxiv.org/abs/2507.05301
- **Status:** VERIFIED

**Mechanism.** Analyses citations produced in the wild by AI search systems (via the AI
Search Arena head-to-head platform) rather than in a lab setup. Establishes that citation
supply is **concentrated**: a small number of outlets absorb a disproportionate share, and
providers differ systematically from each other while models within a provider agree.

**Key quantitative result.** Over 24,000 conversations, 65,000 responses across OpenAI,
Perplexity, and Google models; over 366,000 citations, of which **9% reference news
sources**. News citations "concentrate heavily among a small number of outlets" and show a
pronounced liberal bias; low-credibility sources are rarely cited. Neither political leaning
nor quality of cited sources significantly influenced user satisfaction.

**Transfer to our audit.** Sets a realistic expectation ceiling we should encode in the
report's tone: for most brands, becoming a *cited source* is a concentrated, competitive
outcome, whereas becoming a *correctly-represented entity* is achievable. Our findings
should therefore prioritise "the assistant can retrieve and correctly describe you" over
"the assistant will cite you," and our `suggested_action` text must not promise citation
outcomes.

**False-positive risk.** Not a check-generating source; the risk is in *severity inflation*
— treating "not cited by AI search" as a site defect when concentration means most sites
will not be cited regardless of quality.

**Eval implication.** Any eval metric of ours framed as "did the brand get cited" is
confounded by domain-level concentration effects and should be avoided in favour of
site-side property checks. (our inference)

---

## P-01.09 · Synthetic Sources?: Auditing Generative Search Engine Citations for Evidence of AI-Generated Sources

- **Authors/venue/year:** Mowafak Allaham, Nicholas Diakopoulos. arXiv 2605.23684,
  submitted 22 May 2026. 11 pages + appendix.
- **URL:** https://arxiv.org/abs/2605.23684
- **Status:** VERIFIED

**Mechanism.** Audits what generative search engines cite, specifically whether cited pages
are themselves AI-generated. Also characterises the shape of the citation distribution: a
narrow set of repeatedly-cited domains alongside a long tail of minimally-cited domains.

**Key quantitative result.** Four engines (ChatGPT, Copilot, Gemini, Perplexity), 712
real-world queries across politics, health, environment. **~16% of cited sources showed
evidence of being AI-generated.** Citation distribution: a narrow repeatedly-cited core plus
a large minimally-cited tail. (Search results also surfaced Gini-index figures attributed to
this paper; those were **not** confirmed in the fetched abstract and are therefore not
reported here.)

**Transfer to our audit.** Relevant chiefly as a constraint on what we recommend. The
engines do not currently filter synthetic content well, which means "publish more content"
is a tactic that works in the short term and is exactly the wrong advice. Our
`suggested_action` set should bias toward *making existing true content extractable* rather
than *producing more content*. A defensible read-only check in this spirit: detect
thin/templated/near-duplicate pages within a site (high inter-page text similarity across
many URLs), which is a quality risk regardless of how it was produced.

**False-positive risk.** High for any "this looks AI-generated" detector — AI-text detection
is unreliable and we should not ship one. Near-duplicate detection within a single site is
mechanical and safer, but legitimately templated pages (product variants, location pages)
will trigger it, so severity must stay low and evidence must show the duplication.

**Eval implication.** Adds a specific prohibited-recommendation class to the behavioural
eval: the skill must never recommend generating bulk content, and must never assert that a
page is AI-written.

---

## P-01.10 · From Citation Selection to Citation Absorption: A Measurement Framework for GEO Across AI Search Platforms

- **Authors/venue/year:** Zhang Kai, He Xinyue, Yao Jingang. arXiv 2604.25707 (cs.IR),
  submitted 28 April 2026, revised 29 April 2026. 27 pages, 11 figures. Public dataset and
  pipeline released.
- **URL:** https://arxiv.org/abs/2604.25707
- **Status:** VERIFIED

**Mechanism.** Splits AI visibility into two distinct stages that must be optimised
differently: **citation selection** (the platform triggers search and picks sources) and
**citation absorption** (a cited page actually contributes language, evidence, structure, or
factual support to the generated answer). A page can be selected and contribute nothing.
Absorption is where page-side content properties bite.

**Key quantitative result.** Analysis of 602 controlled prompts across ChatGPT, Google AI
Overview/Gemini, and Perplexity: 21,143 valid search-layer citations, 23,745
citation-level feature records, 18,151 successfully fetched pages, 72 extracted features.
Citation **breadth and depth diverge** — Perplexity and Google cite more sources on average
while ChatGPT cites fewer but shows substantially higher average citation influence among
fetched pages. **High-influence pages tend to be longer, more structured, semantically
aligned, and richer in extractable evidence such as definitions, numerical facts,
comparisons, and procedural steps.**

**Transfer to our audit.** This is the single most directly actionable source in the brief,
because every high-influence property it names is observable read-only from a fetched page:
- presence of explicit **definitions** ("X is a …" sentences answering the page's own topic);
- presence of **numerical facts** with units;
- presence of **comparisons** (tables, "vs." sections, structured attribute lists);
- presence of **procedural steps** (ordered lists, how-to structure);
- **structure** (heading hierarchy depth and whether headings are descriptive);
- **length** of extractable main text vs. boilerplate.
These become concrete findings like "key pages contain no extractable definition of the
product" or "the comparison content exists only as an image."

**False-positive risk.** Moderate, and page-type dependent. These are correlates of
high-influence pages *in the studied prompt set*, which skews informational. A checkout
page, a pricing page, or a contact page should not be penalised for lacking procedural
steps. The properties are also **correlational** — the paper is a measurement framework, not
a causal intervention study, so we must phrase actions as "makes the page more extractable"
rather than "will increase citations."

**Eval implication.** Gives us a defensible feature set for the discoverability checks and,
because the dataset is public, a possible external sanity check on whether our checks
correlate with measured influence. Also supports scoring findings **per page type**.

---

## P-01.11 · Don't Measure Once: Measuring Visibility in AI Search (GEO)

- **Authors/venue/year:** Julius Schulte, Malte Bleeker, Philipp Kaufmann. arXiv 2604.07585,
  8 April 2026. 19 pages, 7 figures, 17 tables. Preprint, no venue stated.
- **URL:** https://arxiv.org/abs/2604.07585
- **Status:** VERIFIED

**Mechanism.** Argues from empirical measurement that AI-search visibility is a
**distribution, not a point**: answers vary across runs, prompts, and time, so a single query
is not a representative snapshot the way a classic SERP position is. Visibility must be
characterised with repeated measurements.

**Key quantitative result.** The abstract states the qualitative conclusion (need for
repeated measurement; visibility as a distribution) without a headline number. Search
results attributed specific Gini figures to this paper; those were **not** present in the
fetched abstract and are therefore **not reported here** as verified.

**Transfer to our audit.** Strong argument for a design constraint: **our audit must not
depend on querying a live generative engine and reading its answer.** That measurement is
non-deterministic, slow, rate-limited, and would blow the <5-minute budget and the
determinism requirement. Instead the audit should measure site-side properties that the
literature links to retrievability and absorption. This is a load-bearing scoping decision.

**False-positive risk.** N/A (methodological source). The risk it warns about is ours:
any check whose output depends on a live LLM search response will be irreproducible across
runs and will produce inconsistent findings on the same site.

**Eval implication.** Directly motivates a **repeat-run determinism protocol**: run the
audit N times on the same frozen site snapshot and measure finding-set stability (e.g.
Jaccard over finding `id`s, plus severity agreement). Instability is a defect even when
every individual finding is defensible. (our inference on the specific metric)

---

## P-01.12 · Can Performant LLMs Be Ethical? Quantifying the Impact of Web Crawling Opt-Outs

- **Authors/venue/year:** Dongyang Fan, Vinko Sabolčec, Matin Ansaripour, Ayush Kumar Tarun,
  Martin Jaggi, Antoine Bosselut, Imanol Schlag. COLM 2025 (camera-ready). arXiv 2504.06219,
  v1 8 Apr 2025, v2 5 Aug 2025.
- **URL:** https://arxiv.org/abs/2504.06219
- **Status:** VERIFIED

**Mechanism.** Defines the **data compliance gap (DCG)** — the performance difference between
models trained on opt-out-compliant corpora and non-compliant ones — and measures it in
pretraining-from-scratch and continual-pretraining settings. Relevant to us as the
counterweight to P-01.03: it quantifies what is actually lost when a domain opts out.

**Key quantitative result.** With 1.5B-parameter models, as of January 2025, compliance with
web opt-outs **does not degrade general knowledge acquisition (close to 0% DCG)**. In
specialised domains such as biomedical research, excluding major publishers **does** produce
performance declines.

**Transfer to our audit.** Calibrates severity for the robots.txt finding. For a general
brand, being excluded from *pretraining* corpora has a small effect on the aggregate model —
but that is a different thing from being excluded from *live retrieval*. Our audit should
therefore separate two distinct crawler classes and report them separately: **training-data
crawlers** (e.g. GPTBot, CCBot, ClaudeBot, Google-Extended) versus **search/retrieval
user-agents used to fetch pages at answer time**. Blocking the latter is the one that
directly prevents an assistant from citing you today; blocking the former is a policy choice
with weaker measured downstream impact for general knowledge.

**False-positive risk.** The main FP this source prevents: treating any AI-bot block as
equally severe. It is a real, evidence-backed distinction, and getting it wrong is the
easiest way for our audit to look naive to a grader.

**Eval implication.** The robots.txt check needs at least three labelled outcome classes in
the gold set — blocks retrieval-time fetching / blocks training crawlers only / blocks
neither — and the eval should verify we assign different severities to each.

---

## P-01.13 · Reconstructing Context: Evaluating Advanced Chunking Strategies for Retrieval-Augmented Generation

- **Authors/venue/year:** Carlo Merola, Jaspinder Singh. Second Workshop on
  Knowledge-Enhanced Information Retrieval, ECIR 2025. arXiv 2504.19754, 28 April 2025.
  13 pages.
- **URL:** https://arxiv.org/abs/2504.19754
- **Status:** VERIFIED

**Mechanism.** RAG systems must split documents into chunks to fit LLM input constraints.
Fixed-size chunking "often fragments context, resulting in incomplete retrieval and
diminished coherence in generation." Late chunking and contextual retrieval are two
techniques for preserving global context across chunk boundaries. The generalisable point
for us: **the retrieval unit is a fragment, not a page**, and a fragment that lost its
context when cut is both less retrievable and less usable.

**Key quantitative result.** Comparative finding rather than a single number: **contextual
retrieval preserves semantic coherence more effectively but requires greater computational
resources; late chunking is more efficient but sacrifices relevance and completeness.**
(Per-dataset numbers are in the paper body and were not verified here.)

**Transfer to our audit.** The site controls how gracefully its content survives chunking,
and that is measurable read-only. Checks: (a) does each major section sit under a
**descriptive heading** that a chunker will carry as context, or under generic headings
("Overview", "More", "Learn more")? (b) are key facts stated **within** the section they
belong to, or split across a heading and a distant paragraph? (c) is the main content
recoverable as clean text at all, or interleaved with nav/boilerplate that will end up
inside chunks? (d) does one page conflate many unrelated topics, so that any chunk mixes
subjects? Each of these degrades the retrievable unit regardless of which chunker is used.

**False-positive risk.** Moderate. The paper studies chunker design, not page authoring;
applying it to page structure is **our extrapolation** (our inference). We should keep these
findings at low-to-medium severity and phrase them as extraction-robustness observations
backed by quoted evidence (the actual generic heading, the actual boilerplate ratio), not as
"this will not be retrieved."

**Eval implication.** These checks depend entirely on our main-content extraction being
correct. The eval must include an extraction-quality stage: if boilerplate removal fails, the
structural checks will produce garbage findings. Measure extraction quality separately
before attributing errors to the checks. (our inference)

---

## P-01.14 · We Analyzed 137K Sites: 97% of llms.txt Files Never Get Read

- **Authors/venue/year:** Louise Linehan (contributor Xibeijia Guan), Ahrefs, 15 June 2026.
- **URL:** https://ahrefs.com/blog/llmstxt-study/
- **Status:** VERIFIED
- **Type:** INDUSTRY (not peer-reviewed). Vendor-run measurement using the vendor's own
  proprietary bot-analytics panel; sampling frame is Ahrefs-tracked domains with traffic,
  not a random sample of the web. Treat the direction as informative and the exact
  percentages as panel-specific.

**Mechanism.** Tests whether the proposed `llms.txt` convention is actually *consumed*. A
publishing convention only affects visibility if crawlers request the file. Measures request
logs for `/llms.txt` classified by user agent.

**Key quantitative result.** 137,210 domains, May 2026. **97% of existing llms.txt files
received zero requests** in the period; only ~3% (≈1,100 domains) got any traffic. Of
requests to files that did get traffic, 96% were bots, 19.5% came from named AI tools, and
12% from tools studying the standard itself. AI agents were 10.5% of all requests to
llms.txt files, and **AI retrieval bots just 1.1% of AI bot requests**. Zero AI bot requests
targeted llms.txt files that did not exist. Separately (search results only, `Status:
SEARCH-ONLY` for these): SE Ranking and Trakkr are reported to have found no predictive
value of llms.txt presence for AI citation frequency, and multiple 2026 adoption trackers
put adoption in the 5.9–10.1% range depending on sampling frame.

**Transfer to our audit.** A **negative** result that directly protects us from a popular
false positive: **do not emit a finding of "missing llms.txt."** It is the most fashionable
GEO recommendation of the moment and the best available measurement says nothing requests
it. If we mention it at all, it should be as an informational, lowest-severity note, clearly
labelled as unproven. This is a place where our audit can visibly out-perform a
practitioner checklist by *declining* to make a recommendation.

**False-positive risk.** This entry exists to eliminate a false positive rather than create a
check. The residual risk is over-correcting: it is also wrong to tell a site to *remove* an
existing llms.txt.

**Eval implication.** Add "recommends creating llms.txt as a substantive fix" to the
prohibited-recommendation list in the behavioural eval, alongside the manipulation tactics
from P-01.04. Add at least one negative-control site that lacks llms.txt and must produce
no finding about it.

---

## P-01.15 · Per-Entity Bias Mapping for AI Visibility: Why Brand Mentions Require Entity-Specific Calibration

- **Authors/venue/year:** Zoltan Varga. arXiv 2606.21595, submitted 19 June 2026. 26 pages,
  14 tables. Preprint; **single author, no stated venue**; Zenodo data/code repositories
  referenced.
- **URL:** https://arxiv.org/abs/2606.21595
- **Status:** VERIFIED
- **Evidence caveat:** the empirical study is **n=100 Hungarian B2B entities**, 1,400 probe
  runs, 2,062 sources. This is a single non-replicated study on a narrow, non-English,
  non-consumer sample. The direction is interesting; the magnitudes should not be
  generalised.

**Mechanism.** Argues that aggregate visibility metrics (mention rate, citation frequency)
are inadequate because entities have systematically different *error profiles*. Three named
failure modes: (1) underrepresented entities are invisible due to **weak knowledge-graph
presence**; (2) large entities suffer a "Brand Hallucination Paradox" where model
familiarity creates stronger surfaces for plausible-but-wrong completions; (3) entities in
under-served regions face a structural gap across knowledge graphs, NER, and entity linking.
A fourth dimension, "Parametric-Retrieval Lag Asymmetry," describes divergence between
retrieval-augmented and parametric memory update cycles.

**Key quantitative result.** Tier 1 (large) brands produced **52.69% fabricated citations
versus 37.87% for Tier 3 entities (+14.82 pp; p = 1.67e-11)**. Regulatory-framed queries
elevated fabrication to **56.77% vs 37.59% baseline (+19.2 pp)**. All within the Hungarian
B2B sample.

**Transfer to our audit.** Supports two off-site checks that are cheap and read-only.
(1) **Knowledge-graph anchoring**: does the site publish machine-readable
`Organization`/`Person` identity (schema.org, consistent NAP details, `sameAs` links to
authoritative external profiles)? Weak KG presence is named as the mechanism behind
invisibility for smaller entities, and `sameAs`/structured identity is the site-side lever.
(2) **Name ambiguity**: is the brand name a common word or shared with a better-known
entity, and does the site do anything to disambiguate (consistent full legal name, category
descriptor near the brand name, explicit "X is a <category> company" definition)?

**False-positive risk.** High if we over-read this source. It is one non-replicated preprint
on a narrow sample, and the "Brand Hallucination Paradox" in particular should **not** be
turned into a finding — we cannot measure fabrication rates for an arbitrary brand
read-only. Restrict the transfer to the structured-identity and disambiguation checks, which
are independently supported by ordinary structured-data practice. Also: a site with no
`sameAs` is not automatically broken; severity should be low unless the brand name is
genuinely ambiguous.

**Eval implication.** Anything derived from this source must be labelled in our own
documentation as resting on a single study. If a grader probes our evidence base, the
honest answer must be available. (our inference)

---

## Domain synthesis

### Best-supported mechanisms (ranked by evidence strength × read-only measurability)

1. **Crawler access is the hard gate, and it has two distinct classes.** Retrieval-time
   fetching and training-corpus crawling are different things with different consequences
   (P-01.03, P-01.12). Parsing `robots.txt` and reporting per-agent-class access is the
   cheapest, most mechanical, most defensible off-site check we have. Severity must depend
   on class and on apparent intent, never on "AI bot blocked = bad."
2. **Extractable evidence density predicts answer absorption.** Pages that contribute to
   generated answers are longer, more structured, and richer in definitions, numerical
   facts, comparisons, and procedural steps (P-01.10) — every one of which is observable in
   extracted main text. This is the strongest, most recent, largest-sample basis for the
   content-side checks, and it is measured across three platforms.
3. **Standalone interpretability of passages.** Attribution requires a statement that
   survives decontextualisation (P-01.05), and citation support fails half the time even for
   the best systems (P-01.02). Site-side: key claims should name their subject and sit in
   one place. Chunking research (P-01.13) reinforces this from the retrieval side —
   descriptive headings and topically coherent sections survive fragmentation.
4. **Page text is a real lever on generative answers.** GEO's core claim, with a KDD 2024
   venue behind it and up to 40% visibility gains reported (P-01.01), plus the
   independent finding that LLM search draws on a partly different source pool than
   classic search — 37% of domains unique to LLM search (P-01.07). Together these justify
   auditing AI-discoverability as its own dimension rather than recycling an SEO checklist.
5. **Attribution failure is common and partly site-controllable.** 60%+ error rates, over
   50% fabricated/broken URLs on two engines, and systematic citing of syndicated copies
   over originals (P-01.06). The site-controllable slice is canonicalisation, link
   stability, and unambiguous publisher identity on every page.
6. **Machine-readable entity identity is the lever for being *correctly represented*.**
   Weak knowledge-graph presence is the named mechanism for entity invisibility (P-01.15);
   `sameAs`, consistent naming, and an explicit category definition are the site-side
   response. Weaker evidence than 1–5, so lower severity.
7. **Visibility is a distribution, not a value.** Answers vary across runs, prompts, and
   time (P-01.11), and citation supply is heavily concentrated among a few domains
   (P-01.08, P-01.09). Consequence for design: **do not query a live generative engine as
   part of the audit**, and do not promise citation outcomes in `suggested_action` text.

### Where the literature is thin, contested, or single-study

- **The GEO headline number is fragile.** "Up to 40%" (P-01.01) is a best-method-per-domain
  upper bound from late 2023, on GEO-bench, against engines that no longer exist in the
  same form. The paper's own robust finding is that **efficacy varies by domain**. We should
  cite GEO for the *mechanism*, never for an expected effect size on an arbitrary site. I
  did not find a genuine independent replication of the 40% figure.
- **Selection vs. absorption is a live and useful split, but new.** P-01.10 (April 2026)
  proposes it with a large public dataset, but it is a measurement framework, not a causal
  intervention study. Its feature list is correlational. Our `suggested_action` phrasing must
  reflect that.
- **The sharpest disagreement: does breadth of citation mean opportunity or concentration?**
  P-01.07 reports LLM search cites with *greater domain diversity* than traditional search
  (37% unique domains) — an optimistic reading for small sites. P-01.08 and P-01.09 report
  heavy *concentration*, with a narrow repeatedly-cited core and a long minimally-cited tail.
  These are not strictly contradictory (a long tail can be both diverse and low-share), but
  they support opposite practical conclusions, and the field has not reconciled them. Our
  design should stay agnostic: audit retrievability and correctness, not citation share.
- **`llms.txt` has no supporting evidence and one strong negative measurement.** 97% of
  files never requested (P-01.14), from a vendor panel. I found **no peer-reviewed or arXiv
  evaluation** of llms.txt despite targeted searching. The null results reported by SE
  Ranking and Trakkr are `SEARCH-ONLY` — I did not open them — so the honest position is:
  no positive evidence exists, one credible negative measurement exists, therefore do not
  recommend it.
- **Brand-mention / off-site-authority claims are almost entirely vendor research.** The
  frequently-repeated claim that off-site brand mentions are the strongest predictor of LLM
  citation traces to agency and SEO-tool blog posts, not peer-reviewed work. I could not
  trace it to a primary peer-reviewed source and am therefore **not** repeating the numbers.
  P-01.15 is the only academic-format source I found on entity-level visibility, and it is a
  single-author preprint on 100 Hungarian B2B entities.
- **Chunking→page-authoring transfer is our extrapolation.** P-01.13 studies chunker design.
  No source I verified measures the effect of *heading quality* or *section coherence* on
  retrievability of a real website. Keep severity low.
- **Nothing verified here measures our actual target quantity** — the effect of a specific
  site-side fix on a specific brand's representation in a specific assistant. That
  experiment does not appear to exist in the public literature. Our audit is therefore
  built on mechanism-level evidence, and the report's language should reflect that
  honestly. (our inference)

### Design consequences to carry forward

- Audit **site properties**, never live assistant output. (P-01.11)
- Separate **retrieval-time** from **training-time** crawler policy in every access finding.
  (P-01.03, P-01.12)
- Score content checks **per page type**; a single pooled precision number will hide the
  dominant false-positive mode. (P-01.01, P-01.10)
- Every finding carries `evidence` that *entails* the finding — grade this explicitly.
  (P-01.02, P-01.05)
- Maintain an explicit **prohibited-recommendation list**: hidden/injected text and
  retriever-directed strings (P-01.04), bulk content generation (P-01.09), llms.txt as a
  substantive fix (P-01.14), and any promise of citation outcomes (P-01.08).
- Build negative controls for: intentional AI-bot blocking, pages that legitimately lack
  statistics/steps, sites with legitimate hidden UI text, and sites with no llms.txt.
