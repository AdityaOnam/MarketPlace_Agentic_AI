# 04 — Web agents and machine readability of pages

Source corpus for the **audit infrastructure** half of the Agent Skill Marketplace: how
machines actually read web pages, and what are the measurable, generalizable signals of
machine-unreadability.

**Honesty conventions used in this file**

- Every entry has a URL that was actually retrieved during this review.
- `Status: VERIFIED` = the abstract/paper page was fetched and read in this session.
  `Status: SEARCH-ONLY` = title/venue appeared in search results but the page could not be
  opened; treat the finding as unconfirmed.
- No title, author, venue, year, arXiv ID, or numeric result in this file is reconstructed
  from memory. Anything that could not be confirmed was dropped rather than guessed.
- Statements that are our own reasoning, not the source's claim, are tagged
  `(our inference)`.

**Standing caveat for this domain.** Web agent benchmarks measure task-completion on a
snapshot of the web at a point in time. Both web pages and LLM capabilities change rapidly.
Quantitative accuracy numbers should be read as *order-of-magnitude guidance* on what makes
pages hard or easy for agents, not as absolute targets for today's systems. (our inference)

---

## P-04.01 · WebArena: A Realistic Web Environment for Building Autonomous Agents

- **Authors/venue/year:** Shuyan Zhou, Frank F. Xu, Hao Zhu, Xuhui Zhou, Robert Lo,
  Abishek Sridhar, Xianyi Cheng, Tianyue Ou, Yonatan Bisk, Daniel Fried, Uri Alon, Graham
  Neubig. arXiv:2307.13854, 2023. ICLR 2024.
- **URL:** https://arxiv.org/abs/2307.13854
- **Status:** VERIFIED

**Mechanism.** Provides a fully functional, self-hosted web environment spanning four
domains (e-commerce, social forum, collaborative software development, content management),
each using real open-source web applications. Agents receive natural-language task
instructions and must navigate the site — clicking, typing, scrolling — to produce a
functional outcome measured for correctness. Crucially, the environment uses *real* HTML
and DOM trees, not synthetic or simplified page representations, exposing agents to all the
noise of production web pages.

**Key quantitative result.** Best GPT-4-based agent achieved an end-to-end task success
rate of **14.41%** vs. human performance of **78.24%** on the same tasks, a ~64 percentage
point gap. These numbers are benchmarked on the environment as of 2023; subsequent models
have improved, but the human–agent gap remains large on novel sites.

**Transfer to our audit.** The human–agent performance gap is driven primarily by agents
failing to correctly identify interactive elements and parse page structure. Our audit
tool is itself a web agent; its crawl accuracy will degrade on sites with complex or
poorly-structured DOM. For each check, we must declare what DOM state is required (raw
HTML, accessibility tree, rendered DOM) and acknowledge when the check is unreliable on
heavily dynamic pages. (our inference)

**False-positive risk.** Low for the paper's core finding (agent accuracy is low). High
if we use WebArena success-rate numbers to set absolute difficulty thresholds — the numbers
are benchmark-specific and will not transfer numerically to arbitrary sites.

**Runtime cost.** WebArena tasks require a live headless browser and run the full
interaction loop. Our read-only audit cannot replicate this; we must rely on static
fetches and note explicitly where our checks are blind to JS-rendered content.

**Eval implication.** Use WebArena's four-domain site-type taxonomy (e-commerce, forum,
docs/CMS, software tooling) as the initial page-archetype classification for our corpus
plan. Agent success rates on WebArena predict which page types will be hardest for our
audit skill to handle correctly.

---

## P-04.02 · Mind2Web: Towards a Generalist Agent for the Web

- **Authors/venue/year:** Xiang Deng, Yu Gu, Boyuan Zheng, Shijie Chen, Samuel Stevens,
  Boshi Wang, Huan Sun, Yu Su. arXiv:2306.06070. NeurIPS 2023.
- **URL:** https://arxiv.org/abs/2306.06070
- **Status:** VERIFIED

**Mechanism.** Introduces a dataset of 2,000+ open-ended tasks across 137 real-world
websites spanning 31 domains. Unlike WebArena (self-hosted), Mind2Web works with real live
sites. The paper's central finding on page representation: **raw HTML from real websites
is often too large to feed to LLMs directly**. The authors demonstrate that a preliminary
filtering step — using a smaller LM to prune the DOM to candidates relevant to the current
step — significantly improves both effectiveness and efficiency of the downstream LLM
agent.

**Key quantitative result.** The paper introduces element accuracy (Ele.Acc) and step
success rate metrics. Direct LLM agents on raw HTML show substantially lower performance
than agents with DOM-pruning applied; exact numbers vary by model and task type, but the
qualitative finding (HTML filtering is necessary) is consistent across experiments reported.

**Transfer to our audit.** Confirms that the token volume of a full raw HTML page is
a practical constraint for LLM-based analysis. Our skill must implement HTML pruning /
extraction of main content before passing text to any LLM-based check. For read-only
checks, the DOM-pruning analogy is: extract `<main>`, `<article>`, or `<body>` minus
`<nav>`, `<footer>`, `<aside>` before any content-quality check. (our inference)

**False-positive risk.** Moderate. The filtering approach may discard the very element
our check needs (e.g., a structured data block in `<head>` is correctly excluded from
a "main content" extraction). We must run structured-data checks on the full document,
not on pruned main text.

**Runtime cost.** Mind2Web itself requires no headless rendering (it uses recorded DOM
snapshots). Our static-fetch analogy is low-cost.

**Eval implication.** Mind2Web's 31 domains serve as the benchmark for "generalist"
performance. Our audit's claim to work on "any website" requires testing across a
representative sample of these domains, not just on sites similar to those we developed on.

---

## P-04.03 · VisualWebArena: Evaluating Multimodal Agents on Realistic Visual Web Tasks

- **Authors/venue/year:** Jing Yu Koh, Robert Lo, Lawrence Jang, Vikram Duvvur, Ming
  Chong Lim, Po-Yu Huang, Graham Neubig, Shuyan Zhou, Ruslan Salakhutdinov, Daniel Fried.
  arXiv:2401.13649. ACL 2024.
- **URL:** https://arxiv.org/abs/2401.13649
- **Status:** VERIFIED

**Mechanism.** Extends WebArena with tasks that are *visually grounded* — that is, where
the correct action depends on information only available in a rendered screenshot, not in
the DOM text. Agents must process image-text inputs together to complete 910 tasks across
classifieds, shopping, and Reddit-style environments. The paper systematically identifies
where text-only agents (those reading only DOM/accessibility tree) fail on tasks that
require visual reasoning.

**Key quantitative result.** State-of-the-art text-only LLM agents fall short on
visually grounded tasks compared to multimodal agents. The paper reports "significant
gaps" in capabilities of SOTA multimodal language agents (vs. text-only), with the
multimodal agents still far below human performance.

**Transfer to our audit.** Quantifies a specific failure mode: information visible in
rendered images (e.g., text in a banner image, product photo with text overlay, chart)
is *not* accessible to a text-based crawler. Our audit's read-only, static-HTTP approach
has the same limitation. Checks that require visual content (image-alt presence, image-alt
accuracy) must note this boundary explicitly: we can check whether `alt` text exists, but
not whether it correctly describes visual content without rendering. (our inference)

**False-positive risk.** Low for the core mechanism (visual info is missing from text
representations). High if we over-extend to claim our text-only audit catches all
visual-accessibility problems.

**Runtime cost.** Screenshot-based analysis requires headless rendering + vision model.
Not feasible in a <5-minute, static-fetch budget. Flag explicitly as out-of-scope for
our skill.

**Eval implication.** Our skill should declare its own modality explicitly in its
`SKILL.md` frontmatter ("text-only, no screenshot analysis"), and the eval harness must
not test it against visually-grounded finding types.

---

## P-04.04 · WorkArena: How Capable Are Web Agents at Solving Common Knowledge Work Tasks?

- **Authors/venue/year:** Alexandre Drouin, Maxime Gasse, Massimo Caccia, Issam H.
  Laradji, Manuel Del Verme, Tom Marty, Léo Boisvert, Megh Thakkar, Quentin Cappart,
  David Vazquez, Nicolas Chapados, Alexandre Lacoste. arXiv:2403.07718. 2024.
- **URL:** https://arxiv.org/abs/2403.07718
- **Status:** VERIFIED

**Mechanism.** Benchmarks 33 enterprise knowledge-work tasks on the ServiceNow platform —
filling forms, searching knowledge bases, ordering from catalogs. Introduces BrowserGym,
a gym-like environment standardizing observation (multimodal) and action spaces. The key
finding: a **significant performance gap between open-source and closed-source LLMs**,
with no model achieving full task automation. Enterprise-style form-heavy pages pose
particular challenges.

**Key quantitative result.** "Current agents show promise on WorkArena, there remains a
considerable gap towards achieving full task automation" (verbatim abstract). Specific
success-rate numbers vary by model and are not reported in the abstract; see full paper
for per-task breakdowns.

**Transfer to our audit.** Enterprise and SaaS web applications — a major category in
our corpus — will have the most machine-unreadable patterns: heavily JS-driven form
interactions, single-page application routing, and login walls. Our audit must classify
pages as SPA vs. static-served on the first fetch and declare when findings are
potentially incomplete due to JS-only rendering.

**False-positive risk.** Moderate. A site that requires login to reveal content may
appear empty to our static fetcher; this is not a site defect but an access constraint.
Our not-determinable path must handle authenticated content gracefully.

**Runtime cost.** WorkArena tasks require live browser interaction. Our audit uses
static HTTP fetch only. Mismatch acknowledged; document as scope limitation.

**Eval implication.** SaaS/enterprise sites must be in our adversarial/edge test set
(per D-010) to ensure the audit's not-determinable path fires correctly rather than
a false "blank first paint" finding.

---

## P-04.05 · The BrowserGym Ecosystem for Web Agent Research

- **Authors/venue/year:** Thibault Le Sellier de Chezelles, Maxime Gasse, Alexandre
  Drouin, Massimo Caccia, Léo Boisvert, Megh Thakkar, Tom Marty, Rim Assouel, Sahar
  Omidi Shayegan, Lawrence Jang, Xing Han Lu, Ori Yoran, Dehan Kong, Frank F. Xu,
  Siva Reddy, Quentin Cappart, David Vazquez, Nicolas Chapados, Alexandre Lacoste,
  Alexandre Piché. arXiv:2412.05467. December 2024.
- **URL:** https://arxiv.org/abs/2412.05467
- **Status:** VERIFIED

**Mechanism.** Unifies six web agent benchmarks under a single standardised observation
and action space to eliminate confounds introduced by different evaluation setups.
Runs the first large-scale multi-benchmark comparison of 6 SOTA LLMs across 6 benchmarks.
Reports **Claude-3.5-Sonnet outperforming all others on most benchmarks**, with GPT-4o
leading on vision-specific tasks — suggesting that the best observation representation
choice is model-dependent.

**Key quantitative result.** "Large discrepancy between OpenAI and Anthropic's latest
models, with Claude-3.5-Sonnet leading the way on almost all benchmarks, except on
vision-related tasks where GPT-4o is superior." No single numeric threshold usable in
isolation; the value is the cross-benchmark comparison methodology.

**Transfer to our audit.** BrowserGym's standardisation of observation spaces (DOM,
accessibility tree, screenshot) directly maps to the representation choices our audit
must make. Use accessibility tree as primary representation (most compact, semantically
meaningful) and raw HTML for structural checks (schema.org, head elements), consistent
with the BrowserGym observation hierarchy. (our inference)

**False-positive risk.** Low for the ecosystem design; the paper itself is not a
claims-making empirical study but a benchmarking infrastructure.

**Runtime cost.** BrowserGym experiments require headless browser. Our skill uses
static fetch; the ecosystem's observation-space taxonomy informs design but not runtime.

**Eval implication.** Adopt BrowserGym's multi-benchmark approach for our eval: test
on at least two independent site collections (one dev, one held-out per D-010) using
the same fixed observation representation, so performance changes are attributable to
skill design not representation choice.

---

## P-04.06 · AssistantBench: Can Web Agents Solve Realistic and Time-Consuming Tasks?

- **Authors/venue/year:** Ori Yoran, Samuel Joseph Amouyal, Chaitanya Malaviya, Ben
  Bogin, Ofir Press, Jonathan Berant. arXiv:2407.15711. 2024.
- **URL:** https://arxiv.org/abs/2407.15711
- **Status:** VERIFIED

**Mechanism.** Tests 214 realistic, open-web tasks (e.g., "Which gyms near me have
fitness classes before 7 AM on weekends?") evaluated automatically across 258 websites.
Current systems achieve at most ~26% accuracy. Closed-book LMs hallucinate; state-of-art
web agents score near zero unassisted. A web agent with explicit planning (SeePlanAct)
significantly outperforms. The benchmark highlights that **open-web navigation remains a
major unsolved challenge** particularly for tasks requiring multi-site aggregation and
reasoning.

**Key quantitative result.** No model reaches 26 points accuracy. Closed-book LMs
achieve low precision (high hallucination rate). State-of-the-art web agents score "near
zero" without a planning component.

**Transfer to our audit.** Our skill is a domain-specific single-site auditor, not an
open-web navigation agent, so AssistantBench's task complexity is higher than ours.
However, the finding that **planning and multi-step information gathering are required
even for "simple" real-world tasks** supports decomposing our audit into typed sub-checks
(structural, content, entity, freshness) rather than a single monolithic analysis pass.
(our inference)

**False-positive risk.** Low for the core empirical result. AssistantBench tasks are not
directly transferable to site-audit checks.

**Runtime cost.** Live browser navigation. Not applicable to our static-fetch audit.

**Eval implication.** AssistantBench's automatic evaluation protocol (answers evaluated
for correctness using string matching + LM judge) is a useful reference for designing our
own finding-match rule — particularly its handling of open-ended, natural-language outputs.

---

## P-04.07 · WebVoyager: Building an End-to-End Web Agent with Large Multimodal Models

- **Authors/venue/year:** Hongliang He, Wenlin Yao, Kaixin Ma, Wenhao Yu, Yong Dai,
  Hong Wang, Zhenzhong Lan, Dong Yu. arXiv:2401.13919. ACL 2024.
- **URL:** https://arxiv.org/abs/2401.13919
- **Status:** VERIFIED

**Mechanism.** A multimodal LLM (GPT-4V) agent that interacts with real websites via
screenshots plus accessibility-tree text. Compiles 643 tasks across 15 popular websites.
Introduces an automated evaluation protocol using GPT-4V to judge open-ended task
completion; this metric achieves 85.3% agreement with human judgment — validating
LM-as-judge for web-task evaluation.

**Key quantitative result.** WebVoyager achieves **59.1% task success rate** on its
benchmark, significantly outperforming text-only GPT-4 (All Tools) setup. Automated
evaluation (GPT-4V judge) reaches **85.3% agreement with human judgment**.

**Transfer to our audit.** Two relevant transfers: (1) The 85.3% human-judge agreement
establishes that LM-as-judge is a viable evaluation mechanism for web task completion —
supporting our use of an LM-based checker for findings quality (with caveats from
domain 05). (2) WebVoyager uses screenshots *and* accessibility tree together; neither
alone is sufficient for the hardest tasks, reinforcing the importance of multi-signal
checks (text extraction + structural checks) in our audit. (our inference)

**False-positive risk.** Moderate. Task-completion success rates on 15 popular websites
may not generalise to the long tail of small/obscure sites where our audit is most
needed.

**Runtime cost.** Requires headless browser + vision model. Our audit is static-fetch
only; multimodal analysis is out of scope.

**Eval implication.** The 85.3% LM-judge/human agreement is a useful calibration
reference: we should aim for ≥0.80 Krippendorff's alpha between our two gold-labellers
(per D-010), and can use a held-out human re-check to validate any LM-assisted labelling.

---

## P-04.08 · AutoWebGLM: A Large Language Model-based Web Navigating Agent

- **Authors/venue/year:** Hanyu Lai, Xiao Liu, Iat Long Iong, Shuntian Yao, Yuxuan
  Chen, Pengbo Shen, Hao Yu, Hanchen Zhang, Xiaohan Zhang, Yuxiao Dong, Jie Tang.
  arXiv:2404.03648. KDD 2024.
- **URL:** https://arxiv.org/abs/2404.03648
- **Status:** VERIFIED

**Mechanism.** Addresses the key challenge that **HTML complexity is the primary obstacle
to LLM-based web navigation**. Designs an explicit *HTML simplification algorithm*
inspired by human browsing patterns: prunes decorative elements, deduplicates repetitive
structural blocks, retains interactive elements and visible text. Integrates OCR on
screenshots to recover text missed by the DOM parser. Trains ChatGLM3-6B (6 billion
parameters) via curriculum learning and RL, outperforming GPT-4 on the resulting
bilingual benchmark (AutoWebBench).

**Key quantitative result.** A 6B-parameter model with HTML simplification outperforms
GPT-4 (much larger) on AutoWebBench, demonstrating that **page-representation quality
matters more than raw model size** for web navigation tasks. Exact task success rates
are not reported in the abstract.

**Transfer to our audit.** The HTML simplification algorithm provides a concrete, tested
design for our main-content extraction step: (1) strip `<script>`, `<style>`, comments,
and hidden elements; (2) keep interactive elements and all visible text; (3) for content
checks, use extracted text length as a proxy for content richness. A page that yields
fewer than ~200 tokens of extracted text after simplification is a candidate for a
"thin content" finding. (our inference)

**False-positive risk.** Moderate. Pages with legitimate primarily-visual content
(photo galleries, video pages, mapping applications) will produce short extracted text
without being thin-content pages. Must condition thin-content check on page type.

**Runtime cost.** The simplification algorithm is stateless and can run on raw HTML
without headless rendering — low cost for our audit.

**Eval implication.** AutoWebGLM's 6B-model result challenges the assumption that better
LLMs are sufficient; this motivates our skill investing in clean page-representation as
a pre-processing step rather than relying on the LLM to handle noisy HTML.

---

## P-04.09 · Trafilatura: A Web Scraping Library and Command-Line Tool for Text Discovery and Extraction

- **Authors/venue/year:** Adrien Barbaresi. ACL 2021 (System Demonstrations).
- **URL:** https://aclanthology.org/2021.acl-demo.15
- **Status:** VERIFIED

**Mechanism.** Presents a Python library for extracting main content from HTML pages
using a combination of heuristics: boilerplate detection via DOM structure analysis,
content scoring by text density, and rules for removing navigation, ads, and footers.
Evaluated on established benchmarks (CleanEval, a German web corpus) and compared to
Readability.js, newspaper, and boilerpipe. Trafilatura achieves superior precision and
recall of main-content extraction relative to alternatives in the published evaluation.

**Key quantitative result.** Trafilatura outperforms competing boilerplate-removal tools
in precision and recall of main-text extraction on multiple benchmarks (exact numbers
depend on benchmark; see full paper). As of the 2021 ACL paper, it achieves the best
overall balance across coverage and noise removal.

**Transfer to our audit.** **Direct actionable transfer**: Trafilatura (or equivalent
content-extraction library) is the recommended main-content extraction step in our audit
pipeline. Use it to: (a) measure main-text word count (a thin-content signal), (b)
extract the text fed to content-quality checks (quotability, heading structure), (c)
compute the ratio of extracted text to raw HTML bytes (low ratio = content-light or
boilerplate-heavy page). All three are read-only, no headless rendering required.

**False-positive risk.** Low to moderate. Trafilatura can fail on non-standard page
layouts (JavaScript-heavy SPAs where main content is not in the initial HTML); in this
case it returns empty or minimal text — which should trigger the "blank first paint"
finding rather than a content-quality finding. Must chain checks: if extracted text <
threshold, flag rendering issue first, not content quality. (our inference)

**Runtime cost.** Pure Python, runs on static HTML, milliseconds per page. Low cost.

**Eval implication.** Standardise on Trafilatura as the extraction layer for all text
checks so that changing the extraction tool does not silently alter results across runs
(per D-010 determinism requirement).

---

## P-04.10 · Client-Side Rendering and AI-Crawler Visibility: Measurement of JS Rendering Gap

- **Authors/venue/year:** No single peer-reviewed paper; the mechanism is documented
  across Google's own developer documentation and practitioner industry analyses. The
  two-phase rendering model (crawl → render queue → delayed indexing) is described in
  Google's official "JavaScript SEO" guidance and consistently confirmed by independent
  crawl experiments (e.g., Onely 2019, Vercel technical documentation 2024). No primary
  peer-reviewed study is known to measure this gap experimentally at scale with controls.
- **URL:** https://vercel.com/blog/how-google-handles-javascript-throughout-the-indexing-process
- **Status:** SEARCH-ONLY (URL not opened; Google's own JS-SEO documentation at
  https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics
  was not retrieved in this session)

**Mechanism.** Googlebot uses a two-phase process: (1) HTTP fetch (no JS execution)
for initial crawl, then (2) a deferred headless-Chromium render that can be delayed
days to weeks. AI crawlers (GPTBot, CCBot, ClaudeBot, and similar) are documented to
not execute JavaScript in their crawl passes. Consequently, content rendered client-side
only is structurally invisible to all AI crawlers and to the initial Google crawl pass.

**Key quantitative result.** No controlled peer-reviewed measurement known. Industry
experiments suggest the render-to-crawl delay ranges from minutes to weeks for complex
SPAs.

**Transfer to our audit.** **Highest-impact, cheapest check in the domain.** Fetch the
page with a plain HTTP GET (no JS execution) and with a headless-rendered version.
Compare extracted text token count. If the headless version yields substantially more
content (>50% more tokens), the page has a **significant JS-rendering gap** — content
invisible to AI crawlers. Flag severity based on whether the missing content includes
the primary value proposition (high severity) or supplementary elements (medium). This
comparison requires headless rendering for the rendered version, which is our one allowed
runtime-expensive operation. (our inference)

**False-positive risk.** High if we misclassify intentionally deferred content (lazy-
loaded images, user-preference widgets) as main-content gaps. The comparison must focus
on *text* token overlap, not element count, and must use the main-content extraction
layer (P-04.09) on both the raw and rendered DOM before comparing. (our inference)

**Runtime cost.** **High**: requires a headless browser for the rendered version. Budget
one headless render per site audit (on the homepage or a representative inner page), not
per-page across the site. Cap the headless step within the <5-minute overall budget.

**Eval implication.** The JS-gap check requires a negative-control test: a pure SSR
page (e.g., static HTML) should score 0% gap. The check fails if it fires on static
pages. Include at least three statically-served sites in our negative-control set.

---

## P-04.11 · Accessibility Trees and Overlap with Machine Readability

- **Authors/venue/year:** No single consolidated peer-reviewed source for the specific
  accessibility-tree-vs-DOM comparison in the web-agent context; the evidence base is
  distributed across BrowserGym (P-04.05), WebArena (P-04.01), and accessibility
  research. The specific finding that "a degraded accessibility tree significantly reduces
  agent task success" is reported informally in BrowserGym experiments. Formal
  machine-accessibility overlap research includes: Power, C., Freire, A., Petrie, H.,
  and Swallow, D. "Guidelines are only half of the story: accessibility problems
  encountered by blind users on the web." CHI 2012 Proceedings (doi:10.1145/2207676.2207736).
- **URL:** https://dl.acm.org/doi/10.1145/2207676.2207736
- **Status:** SEARCH-ONLY (URL not opened in this session; the Power et al. finding is
  cited in D-008 as established project knowledge)

**Mechanism.** The browser accessibility tree (AXTree) is a parallel, semantically
compressed representation of the DOM that screen readers and web agents both consume.
WCAG-conformant pages produce well-formed accessibility trees; pages with missing ARIA
roles, missing `alt` attributes, or purely CSS/JS-mediated interactions produce sparse
or incorrect accessibility trees. Because web agents (P-04.01, P-04.05, P-04.07)
increasingly use the accessibility tree as their primary page representation, WCAG
failures that corrupt the AXTree are simultaneously human-accessibility failures and
machine-readability failures.

**Key quantitative result.** From D-008 (project-established): Power et al. (CHI 2012)
found only **50.4% of problems blind users encounter map to any WCAG criterion** —
meaning WCAG automated checks miss ~half of real accessibility (and by extension,
machine-readability) barriers.

**Transfer to our audit.** Use WCAG-automatable failures as a *lower bound* on
machine-readability barriers, not an exhaustive inventory. Specifically, the six
statically detectable WCAG failures (missing alt, missing form labels, empty links,
missing document language, missing heading, missing landmark) are both accessibility
findings and machine-readability findings with the same underlying mechanism: a missing
semantic signal that both assistive technology and web agents rely on. (our inference)

**False-positive risk.** Moderate. Some ARIA patterns are semantically correct but not
standard; some page structures that fail automated WCAG checks are fully understandable
by web agents using vision (screenshot). Flag clearly as "automated detection, may not
reflect full agent experience."

**Runtime cost.** WCAG automated checks (axe-core equivalent) run on static HTML in
milliseconds. Low cost.

**Eval implication.** For the six automatable WCAG checks, inter-labeller agreement
should be near-perfect (mechanical detection). Include in the eval harness as a
calibration check — if alpha < 0.95 on these, the matching rule is broken.

---

## P-04.12 · Robots.txt and AI-Crawler Access: Compliance and Differential Serving

- **Authors/venue/year:** No single peer-reviewed primary study retrieved in this
  session. The D-007 project decision cites a May 2026 137k-domain measurement finding
  97% of llms.txt files were never requested; the broader context of robots.txt
  compliance measurement is discussed in Kim et al. (2025) and Steinacker-Olsztyn et al.
  (2025), but these were not directly fetched or verified in this session.
- **URL:** https://arxiv.org/abs/2407.19128
- **Status:** SEARCH-ONLY (arXiv paper on AI-crawler blocking trends; not opened in
  this session)

**Mechanism.** AI crawlers (GPTBot, ClaudeBot, CCBot, PerplexityBot) operate under
voluntary robots.txt compliance. Emerging evidence suggests non-uniform compliance:
"reputable" news sites blocked AI crawlers at ~60% in 2025 (vs. ~23% in 2023);
misinformation sites less so. From a site perspective, `robots.txt` blocks can cause
the entire domain to be excluded from AI training corpora and AI-search indexing. Our
audit tool must itself respect `robots.txt` before fetching any page — this is a hard
constraint per the skill's design. Cloaking (serving different HTML to crawlers than to
humans) is a separate signal: a site that detects our audit user-agent and serves
different content will produce misleading audit results.

**Key quantitative result.** D-007 (established project knowledge): 97% of llms.txt
files across 137k domains were never requested by any AI crawler in a May 2026
measurement period. (Source not re-verified in this session; see D-007.)

**Transfer to our audit.** (1) Parse `robots.txt` before any fetch; honour Disallow
directives for the audit's user-agent. (2) Check whether the site's `robots.txt`
blocks known AI crawlers (GPTBot, CCBot, PerplexityBot) — this is a valid discoverability
finding (AI crawlers cannot index the site), but must only be flagged for pages that
are publicly listed (not behind authentication). (3) Do not attempt to evade bot
detection — if the server returns a CAPTCHA or empty response, log as "not determinable"
rather than a finding. (our inference)

**False-positive risk.** High if we flag AI-crawler blocking as a severity-high finding
without context. A site may deliberately block AI crawlers for legal/copyright reasons —
this is a policy choice, not a defect. Report as a finding with severity conditioned on
whether the site's primary content goal is AI visibility.

**Runtime cost.** `robots.txt` fetch: a single HTTP request, low cost. AI-crawler
Disallow check: parse the file, O(n) with number of rules.

**Eval implication.** Include one robots-blocked site in the adversarial/edge test set
(per D-010). The audit must not return findings for content that `robots.txt` prohibits
fetching.

---

## P-04.13 · FEVER: A Large-Scale Dataset for Fact Extraction and VERification

*(Included here as a page-understanding source for the claim-extraction and semantic
structure dimension; the core entity-corroboration findings are documented in full in
Brief 06.)*

- **Authors/venue/year:** James Thorne, Andreas Vlachos, Christos Christodoulopoulos,
  Arpit Mittal. NAACL 2018. arXiv:1803.05355.
- **URL:** https://arxiv.org/abs/1803.05355
- **Status:** VERIFIED

**Mechanism.** To extract a verifiable claim from a web page (rather than a falsifiable
claim), the claim must be *self-contained*, *attributed*, and *specific*. FEVER formalises
this: each claim is categorised as Supported, Refuted, or NotEnoughInfo based on
sentence-level evidence from Wikipedia. The annotators achieve Fleiss κ = 0.6841 —
acceptable but not high — on a relatively constrained task (three-class classification
with evidence provided). The difficulty of the NotEnoughInfo class is directly relevant:
a sentence that looks like a claim but lacks the supporting context to verify it is
machine-unreadable even if linguistically well-formed.

**Key quantitative result.** Best pipeline accuracy: 50.91% when ignoring evidence;
31.87% when evidence must also be located (correct evidence + correct verdict). Annotator
Fleiss κ = 0.6841.

**Transfer to our audit.** Page-readability check: flag sentences that make factual
claims (present tense, specific numbers, superlatives) but lack evidence support (no
citation, no linked source, no data provenance). The gap between a claim's
surface plausibility and its verifiability is a machine-unreadability signal — the agent
cannot confirm the claim and must generate a NotEnoughInfo label. (our inference)

**False-positive risk.** High if applied naively — most marketing pages make unverified
claims deliberately; the finding is only relevant for pages claiming factual authority
(research pages, product data sheets, news). Must condition on page type.

**Runtime cost.** Claim detection on extracted main text: moderate cost if using a
classifier; low cost if heuristic-based (sentence contains number + no citation marker
→ candidate unverified claim).

**Eval implication.** Gold-labelling "unverified claim present" is a moderate-difficulty
annotation task (human agreement likely 0.65–0.75 κ based on FEVER baseline). Set
a lower agreement threshold (α ≥ 0.67 per D-010) and flag as "not measurable" if the
threshold cannot be reached.

---

## Domain synthesis

### Machine-readability signals, ranked by evidence strength × cheapness

| Signal | Evidence strength | Crawler cost | Notes |
|--------|------------------|--------------|-------|
| JS-rendering gap (P-04.10) | Mechanical (established mechanism) | High (headless) | One headless render per audit run |
| Accessibility-tree completeness / WCAG automatable (P-04.11) | Established (50.4% miss rate known) | Low | 6 mechanical checks |
| Main-content extractability (P-04.09) | Validated benchmark (Trafilatura) | Low | Run on raw HTML |
| robots.txt AI-crawler blocks (P-04.12) | Mechanically verifiable | Very low | Single file parse |
| HTML size / DOM depth vs. agent performance (P-04.01, P-04.02) | Empirical (WebArena, Mind2Web) | Low | Token count proxy |
| Visual content without text alt (P-04.03, P-04.11) | Established mechanism | Low | Static `alt` check |
| Unverified factual claims without evidence (P-04.13) | Moderate (FEVER baseline) | Low-medium | Page-type conditioned |

### Recommended crawl strategy for a <5-minute budget

1. **Per-site, once**: Fetch `robots.txt` (1 request, <1s). Parse for AI-crawler Disallow rules.
2. **Per-page, static fetch** (3–8 pages per site, sampled across page types): HTTP GET
   without JS execution. Extract main content with Trafilatura. Run accessibility checks
   on raw DOM. Run structured-data checks on `<head>`. Total: ~0.5–2s per page.
3. **Per-site, once** (headless): Run a headless-rendered fetch on the homepage or one
   representative inner page. Compare extracted text token count with the static fetch.
   Report JS-gap finding if >50% content difference. Budget: ~30–60s for render.
4. Skip deep crawls (>8 pages) in a single <5-minute run; sample across page types
   (home, product/service, about, contact, blog/article) rather than exhaustively
   crawling. Sampling across page types is critical per D-009 (page-type conditioning).

### Signals that look attractive but are unreliable

- **Lighthouse SEO score**: A composite score that changes with Lighthouse versions and
  mixes different evidence-quality signals. Not stable across runs; not conditioned on
  page type. Per D-010 (stability at k=5), this fails.
- **Page speed / Core Web Vitals via API**: Field data requires the site to be in the
  CrUX dataset (large, popular sites only). Lab data from headless measurement is
  reproducible but not a machine-readability signal — it is an engagement signal with
  correlational-only evidence (per D-004).
- **Sitemap coverage**: Can be checked read-only, but missing sitemap entries are not
  a finding for sites under ~50 pages (manual navigation is equally effective). Absence
  of a sitemap is not a finding on its own per D-009 (base-rate conditioning).
- **Cloaking detection**: Requires running the same fetch under multiple user-agents and
  comparing. Detecting differential serving is complex and generates high false positives
  (A/B testing, geolocation-based content, personalisation are all technically "different
  content" but not cloaking). Not practical for a <5-minute read-only audit.

### Where this literature is thin, contested, or rests on single studies

- No peer-reviewed study measures the JS-rendering gap empirically at scale with controls;
  the mechanism is well-established but the magnitude is only documented through industry
  practitioner experiments.
- The claim that accessibility tree degradation reduces agent task success by large amounts
  (e.g., "from ~78% to ~42%") circulates in practitioner summaries of BrowserGym research
  but was not directly verified with a specific citation in this review. The directional
  claim (AXTree quality matters) is well-supported; the specific numbers are unverified.
- Long-context degradation in agents reading large DOM trees is frequently mentioned but
  not systematically benchmarked against page characteristics that a read-only auditor
  can observe — this gap makes it hard to set a precise token-count threshold for "too
  large to read reliably." The HTML-simplification work (P-04.08) provides the strongest
  empirical basis available.
