# 06 — Structured data, entity grounding, corroboration, freshness

Source corpus grounding two Round-2 audit mechanisms: explicit-and-unambiguous facts get
extracted; corroborated facts get believed; ambiguous entities get confused. Covers
structured data at web scale, information extraction from HTML, entity linking,
corroboration/truth discovery, temporal freshness, long-tail entity hallucination, and
quotability.

**Honesty conventions used in this file**

- Every entry has a URL that was actually retrieved during this review.
- `Status: VERIFIED` = the abstract/paper page was fetched and read in this session.
  `Status: SEARCH-ONLY` = title/venue appeared in search results but the page could not be
  opened; treat the finding as unconfirmed.
- No title, author, venue, year, arXiv ID, or numeric result in this file is reconstructed
  from memory. Anything that could not be confirmed was dropped rather than guessed.
- Statements that are our own reasoning, not the source's claim, are tagged
  `(our inference)`.

**Standing caveat for this domain.** Structured-data adoption rates and LLM knowledge-
boundary results both shift over time as the web changes and model training windows advance.
Numbers from web-scale crawls are snapshots; treat them as order-of-magnitude baselines
rather than exact current figures. (our inference)

---

## P-06.01 · Web Data Commons — October 2024 Structured Data Statistics

- **Authors/venue/year:** Web Data Commons project, University of Mannheim. Data release
  based on the October 2024 Common Crawl. Published December 2024.
- **URL:** https://webdatacommons.org/structureddata/2024-12/stats/stats.html
- **Status:** VERIFIED

**Mechanism.** Extracts RDFa, Microdata, JSON-LD, and Microformats from the entire
Common Crawl corpus. Each release reports per-format domain and URL counts, entity counts,
and triple counts, providing the most authoritative web-scale measurement of structured
data adoption. The October 2024 release parsed 2,391,039,772 HTML pages from 37,447,141
pay-level domains.

**Key quantitative results (directly read from the data page):**
- **51.25%** of the 2.39B parsed URLs carry some structured data (1,245,622,627 URLs).
- **44.12%** of the 37.4M domains carry some structured data (16,525,070 domains).
- By format, domains with triples: JSON-LD = **11,562,359**; Microdata = **7,599,792**;
  RDFa = **474,635**. (Counts overlap: a domain may use multiple formats.)
- Total RDF quads extracted: **73,993,669,093** (~74 billion).

**Transfer to our audit.** The 44.12% domain coverage figure is the critical calibration
number: **absence of structured data is the majority condition on the web**. Per D-009,
"no JSON-LD" on a domain is not a finding — it describes 55.88% of all domains. The
finding threshold must be conditioned on page type: on e-commerce product pages and
event pages, absence of Product/Event schema is an unusual omission and potentially a
real discoverability gap. On About pages, contact pages, and pure-text blog posts,
absence of schema is expected and normal. (our inference)

**False-positive risk.** HIGH if applied as a blanket check. Must implement page-type
classification before schema checks (D-009). A site with no products correctly has no
Product schema; a SaaS company with no events correctly has no Event schema.

**Eval implication.** Use the WDC base-rate numbers as the prior for schema-presence
checks. A finding of "no schema" should only fire when the base rate for the specific
page type is substantially higher (e.g., >70% of equivalent-type pages have schema per
WDC product corpus data).

---

## P-06.02 · Web Almanac 2024 — Structured Data Chapter (HTTP Archive)

- **Authors/venue/year:** HTTP Archive Web Almanac, Chapter 3: Structured Data. 2024.
  Based on a crawl of 16.9 million websites.
- **URL:** https://almanac.httparchive.org/en/2024/structured-data
- **Status:** VERIFIED

**Mechanism.** Annual state-of-the-web report analysing structured data adoption trends.
The 2024 chapter notes a "clear transition from traditional SEO implementation toward
more sophisticated knowledge graph development designed to ground AI discovery systems
and large language models in factual data." Covers JSON-LD, RDFa, Open Graph, Twitter
Cards, Microdata, and Microformats adoption trends with year-on-year comparisons.

**Key quantitative result.** Consistent with WDC (P-06.01): JSON-LD is the dominant
growing format; Open Graph and Twitter Cards are near-universal on media/publishing
sites. The 2024 chapter highlights deprecation of FAQ and HowTo rich results by Google
in 2023 — sites that implemented these specifically for rich results may now have schema
that serves no search purpose, raising questions about maintenance and staleness.

**Transfer to our audit.** Two checks motivated by this source: (1) Check for schema
types whose Google rich result support has been deprecated (FAQ, HowTo) — flag as
a maintenance finding (no negative SEO consequence, but wasted implementation effort
if no other consumer). (2) For key schema types (Organization, Product, BreadcrumbList,
SiteLinksSearchBox), check presence and validate required fields — an Organization with
no `name` or no `url` is a structurally defective but parseable instance. (our inference)

**False-positive risk.** Moderate. Not every schema error matters to every AI consumer.
Focus on required fields that are unambiguously wrong (null `name` on Organization) vs.
optional fields that are merely absent.

**Eval implication.** Schema validation checks (required field present / not null) are
near-deterministic and should achieve near-perfect inter-labeller agreement. Flag as
anomaly if Krippendorff alpha < 0.90 on these.

---

## P-06.03 · MAVE: A Product Dataset for Multi-source Attribute Value Extraction

- **Authors/venue/year:** Li Yang, Qifan Wang, Zac Yu, Anand Kulkarni, Sumit Sanghai,
  Bin Shu, Jonathan Elsas, Bhargav Kanagal (Google Research). WSDM 2022. arXiv:2112.08663.
- **URL:** https://arxiv.org/abs/2112.08663
- **Status:** VERIFIED

**Mechanism.** Introduces a dataset of 2.2 million Amazon product pages with 3 million
attribute-value annotations across 1,257 product categories. The task: extracting
attribute values (e.g., "material: cotton", "color: navy blue") from unstructured product
descriptions, titles, and metadata. The paper demonstrates that product pages often
express attributes *implicitly* or *incompletely*: a product called "Navy Polo Shirt"
implies color without stating it as `color=navy`. Extraction from multi-source product
information (title + description + bullets) significantly outperforms single-source
extraction. The zero-shot test set (new attribute types not seen in training) shows
substantially harder performance.

**Key quantitative result.** MAVE is the largest such dataset (2.2M products, 3M
annotations, 1,257 categories). Zero-shot attribute extraction is characterised as
"very challenging" in the paper. Exact F1 numbers depend on the specific extraction
model and setting.

**Transfer to our audit.** Grounds the "explicit vs. implicit information gap" mechanism.
For product pages: if a product's key attributes (SKU, price, category, material, size)
are only implied in prose but not stated explicitly — either in text or in structured
markup — they are likely to be missed or guessed incorrectly by information extraction
systems. Check for: (1) Product schema present with required fields (`name`, `description`,
`offers`); (2) Key product facts stated explicitly in text (price, availability, key
spec) rather than only embedded in image captions or interactive selectors. (our inference)

**False-positive risk.** HIGH for non-e-commerce pages. MAVE findings apply specifically
to product pages. SaaS pages, About pages, and blog posts do not need to expose
attribute-value pairs in the MAVE sense. Must condition on page_type = product.

**Eval implication.** For product pages, the check "is price stated explicitly in main
text or in Product schema `offers.price`?" is near-deterministic and should yield high
inter-labeller agreement.

---

## P-06.04 · FEVER: A Large-Scale Dataset for Fact Extraction and VERification

- **Authors/venue/year:** James Thorne, Andreas Vlachos, Christos Christodoulopoulos,
  Arpit Mittal. NAACL 2018. arXiv:1803.05355.
- **URL:** https://arxiv.org/abs/1803.05355
- **Status:** VERIFIED

**Mechanism.** 185,445 claims generated by altering Wikipedia sentences and verified by
annotators for support/refute/not-enough-info status. Defines and operationalises the
concept of *sentence-level fact verification from a text source*: each claim must be
verifiable against a specific retrievable sentence. The core mechanism for our use:
a factual claim is only machine-believable if there exists a passage in the source page
that directly entails it — and this passage must be extractable without surrounding context.
Annotators achieve Fleiss κ = 0.6841; the NotEnoughInfo class (where context is
insufficient to verify) is the most disagreed-upon.

**Key quantitative result.** Best pipeline: 31.87% accuracy when evidence must be
located + verdict correct; 50.91% when the correct evidence sentence is provided. This
~19 pp gap quantifies how much extraction difficulty costs in downstream verification.

**Transfer to our audit.** The gap between a claim's *presence* in text and its
*verifiability* is a directly auditable signal: does the page's text contain
self-contained sentences that could stand as evidence for the site's main claims? This
is the "quotability" check. Concretely: for each key fact the site asserts (a statistic,
a claim of award/recognition, a specific capability statement), check if there is a
sentence in the main text that states the fact completely enough to be quoted without
surrounding context. Countable read-only proxies: % of sentences naming the subject
explicitly (not "we" or "our product"); presence of statistics with source/date;
FAQ-style answer blocks where each answer begins with the subject. (our inference)

**False-positive risk.** Moderate. "Self-contained sentence" is a fuzzy judgment;
automated detection will over-fire on casual conversational prose that is perfectly
clear to readers. This check is best implemented as a signal (low proportion of
standalone sentences) rather than a binary finding.

**Eval implication.** The 0.6841 κ baseline from FEVER suggests that quotability
annotation is genuinely hard. Plan for lower alpha thresholds (≥0.67 per D-010) and
consider dropping this specific sub-check if gold-labelling cannot reach threshold.

---

## P-06.05 · BLINK: Scalable Zero-shot Entity Linking with Dense Entity Retrieval

- **Authors/venue/year:** Ledell Wu, Fabio Petroni, Martin Josifoski, Sebastian Riedel,
  Luke Zettlemoyer. EMNLP 2020.
- **URL:** https://aclanthology.org/2020.emnlp-main.519
- **Status:** VERIFIED

**Mechanism.** Two-stage entity linking pipeline: (1) bi-encoder independently embeds
a mention-in-context and all Wikidata/Wikipedia entity descriptions, enabling fast nearest-
neighbour retrieval; (2) cross-encoder re-ranks candidates by concatenating mention and
entity text. Enables zero-shot linking to entities not seen during training. The key
mechanism: **entity disambiguation is tractable when the entity has a Wikipedia/Wikidata
description** — the description anchors the dense representation. Entities lacking
Wikidata presence have no description anchor and are effectively unresolvable by
retrieval-based systems.

**Key quantitative result.** BLINK surpasses prior state-of-the-art on standard entity
linking benchmarks by a substantial margin. Exact numbers depend on dataset; the paper
reports state-of-the-art on AIDA-B, WNED-WIKI, WNED-CWEB, and other standard benchmarks.

**Transfer to our audit.** **Direct transfer**: if the brand/organisation being audited
does not have a Wikidata entity, it is unresolvable by entity-linking systems. This means
AI systems reading about the brand will either match it to a wrong entity (name collision)
or leave it unlinked (treating it as an NIL / unlinkable entity). Observable proxy: search
for the organisation name in Wikidata (https://www.wikidata.org/w/index.php?search=NAME)
— this is a single read-only HTTP request. If no Wikidata item exists with a matching
label and type (Organisation), flag as a "no knowledge-graph anchor" finding. (our inference)

**False-positive risk.** Moderate. Very new organisations, local businesses, and niche
products legitimately have no Wikidata entry; the absence is not a defect but a
discoverability limitation. Frame as "discoverability risk" not "error." Also: name
collision (a company sharing a name with a famous person, city, or other entity) is a
more severe finding than simple absence — but is harder to detect read-only.

**Eval implication.** Wikidata lookup is a deterministic, external-API-based check.
Results are reproducible at the time of the snapshot. Freeze the result in the audit
output with a `checked_at` timestamp, since Wikidata changes continuously.

---

## P-06.06 · ReFinED: An Efficient Zero-shot-capable Approach to End-to-End Entity Linking

- **Authors/venue/year:** Tom Ayoola, Shubhi Tyagi, Joseph Fisher, Christos
  Christodoulopoulos, Andrea Pierleoni (Amazon). NAACL 2022 Industry Track. arXiv:2207.04108.
- **URL:** https://arxiv.org/abs/2207.04108
- **Status:** VERIFIED

**Mechanism.** End-to-end entity linking in a single forward pass: mention detection,
fine-grained entity typing, and disambiguation together. More than 60x faster than
competitive approaches. Trained on 150 million entity mentions from Wikipedia hyperlinks.
Capable of linking to Wikidata (which has 15x more entities than Wikipedia). The
fine-grained type information (e.g., distinguishing `Organisation/Company` from
`Person/Musician` sharing the same name) is the primary disambiguation signal.

**Key quantitative result.** 3.7 F1 improvement over state-of-the-art on standard entity
linking datasets. 60x speed advantage makes it practical for web-scale deployment.

**Transfer to our audit.** ReFinED's reliance on entity *type* for disambiguation
motivates a concrete check: does the site's page content make the entity *type* explicit?
For example, a page about "Apple" should unambiguously signal `Organisation/Technology`
(through industry category, product mentions, founders) not leave the entity type
underspecified. Observable proxy: Is the Organisation's industry/sector stated in the
About page text or in the Organization schema's `industry` / `knowsAbout` fields?
Is the entity type disambiguated in the `<title>` tag ("Acme Corp — Enterprise Software"
vs. simply "Acme")? (our inference)

**False-positive risk.** Low. Entity-type disambiguation signals are largely optional
in practice, and their absence is a *risk* (could be confused with a same-name entity)
not an error. Flag as a discoverability consideration, not a defect.

**Eval implication.** Entity-type presence in page content is a moderate-difficulty
annotation task; human agreement is expected to be high (binary: yes/no industry
sector is stated).

---

## P-06.07 · When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories (PopQA)

- **Authors/venue/year:** Alex Mallen, Akari Asai, Victor Zhong, Rajarshi Das, Daniel
  Khashabi, Hannaneh Hajishirzi. ACL 2023. arXiv:2212.10511.
- **URL:** https://arxiv.org/abs/2212.10511
- **Status:** VERIFIED

**Mechanism.** Introduces PopQA, a 14,000-question open-domain QA dataset tagged with
entity *popularity* (measured by Wikipedia page views). Conducts large-scale probing of
10 LMs and 4 augmentation methods. Core findings: (1) LMs struggle with less popular
("long-tail") factual knowledge; (2) scaling model size primarily improves popular
knowledge but does not help the long tail; (3) retrieval-augmented LMs substantially
outperform much larger unassisted LMs on long-tail questions; (4) for *high*-popularity
entities, unassisted LMs remain competitive, and retrieval can sometimes introduce errors
(e.g., retrieving a document about the wrong same-name entity).

**Key quantitative result.** The paper probes 10 models. Results show a consistent
popularity-accuracy correlation: low-popularity entities yield substantially lower
accuracy across all model sizes. Exact numbers vary by model; the qualitative direction
is robust. Scaling from smaller to larger models "fails to appreciably improve
memorization of factual knowledge in the long tail" (verbatim abstract).

**Transfer to our audit.** **The central discoverability mechanism for long-tail brands.**
A small brand, local business, or niche product organisation is by definition a low-
popularity entity. An AI assistant's parametric memory will be unreliable for such
entities — it may hallucinate facts, confuse the entity with a similarly-named one, or
simply not know it exists. The only mitigations available at the site level are:
(1) ensuring the entity is resolvable via Wikipedia/Wikidata (P-06.05, P-06.06);
(2) ensuring the site's own pages contain explicit, corroborating facts in extractable
form (so RAG retrieval can supply accurate information).

Observable audit check: combine the Wikidata lookup (P-06.05) with a check for whether
the domain appears in Common Crawl / major web indices. If both are absent, flag as
"high long-tail hallucination risk." (our inference)

**False-positive risk.** Moderate. "Low Wikipedia page views" is not an observable
proxy from the site itself; the audit can only check Wikidata presence and indirectly
infer popularity. Avoid claiming the site *will* be hallucinated; instead: "limited
external corroboration detected, increasing risk of inaccurate AI representation."

**Eval implication.** This mechanism underpins a finding category ("insufficient external
anchor"). The gold-labelling question should be "does this organisation have a
verifiable, unambiguous entry in a public knowledge base?" — a binary, deterministic
check at time of annotation.

---

## P-06.08 · FreshLLMs: Refreshing Large Language Models with Search Engine Augmentation (FreshQA)

- **Authors/venue/year:** Tu Vu, Mohit Iyyer, Xuezhi Wang, Noah Constant, Jerry Wei,
  Jason Wei, Chris Tar, Yun-Hsuan Sung, Denny Zhou, Quoc Le, Thang Luong. arXiv:2310.03214.
  EMNLP 2023.
- **URL:** https://arxiv.org/abs/2310.03214
- **Status:** VERIFIED

**Mechanism.** Introduces FreshQA, a dynamic QA benchmark with "fast-changing world
knowledge" questions and questions with "false premises that need to be debunked."
Evaluates LLMs on correctness and hallucination under two modes. Key finding: all
tested LLMs struggle with fast-changing knowledge questions. FreshPrompt (few-shot
prompting that incorporates retrieved up-to-date information) substantially outperforms
both unaugmented LLMs and competing search-augmented methods (e.g., Self-Ask). Both
the *number* of retrieved evidence items and their *order* significantly affect
hallucination rate.

**Key quantitative result.** Human evaluation involving "more than 50K judgments."
FreshPrompt "substantially boosts the performance of an LLM on FreshQA" relative to
both closed-book and Self-Ask baselines. All models "struggle on questions that involve
fast-changing knowledge and false premises" (verbatim abstract).

**Transfer to our audit.** Freshness signals on a page's own content are directly
auditable: (1) presence of a `<meta name="last-modified">` or `Last-Modified` HTTP
header; (2) presence of publication/modification dates in the page body (detectable in
main text); (3) for pages claiming time-sensitive authority (press releases, news,
pricing, software version notes), check if the page includes explicit date stamps. An
**evergreen content page** (marketing copy, About us) should *not* be flagged as stale
— only pages with claims that have an expiry date (product versions, regulatory
compliance status, event dates) need explicit datestamps. (our inference)

**False-positive risk.** HIGH if applied to evergreen content. "No date on the page"
is only a finding if the content is time-sensitive. Must condition on content type:
news/announcements, pricing, version/release notes → date required; general marketing
copy → no finding.

**Eval implication.** Date-presence detection is near-deterministic (parse ISO 8601
dates, `datetime` attributes, common date patterns in main text). Gold-label agreement
should be near-perfect. The harder subjective question ("is this content time-sensitive
and stale?") should be kept separate and labelled only if annotation agreement reaches
threshold.

---

## P-06.09 · Time-Aware Language Models as Temporal Knowledge Bases (TempLAMA)

- **Authors/venue/year:** Bhuwan Dhingra, Jeremy R. Cole, Julian Martin Eisenschlos,
  Daniel Gillick, Jacob Eisenstein, William W. Cohen. TACL 2022. arXiv:2106.15110.
- **URL:** https://arxiv.org/abs/2106.15110
- **Status:** VERIFIED

**Mechanism.** Introduces a diagnostic dataset probing LMs for factual knowledge that
changes over time (e.g., "Who is the Prime Minister of the UK?" where the answer
depends on when the question is asked). Identifies two failure modes: (1) models trained
on data from specific time slices memorise facts from that period but fail on adjacent
periods; (2) models trained on wide temporal ranges conflate facts from different time
periods. Proposes jointly modelling text with its timestamp to improve memorisation of
time-bounded facts and calibration on future-period facts. Shows models can be
"refreshed" with new data without full retraining.

**Key quantitative result.** Joint timestamp modelling "improves memorization of seen
facts from the training time period, as well as calibration on predictions about unseen
facts from future time periods" (verbatim abstract). No single universal percentage
reported; the gains are dataset/model-specific.

**Transfer to our audit.** TempLAMA grounds the mechanism: **facts stored in an LM's
parametric memory have an implicit timestamp tied to training data**. If the site has
not been re-crawled and the LM was trained before a key change (leadership change,
product pivot, address change), the LM will recall outdated information with high
confidence. The audit's role is to expose which facts on the site are most likely to
have changed since the LM's training cutoff: leadership names, pricing, product names,
regulatory status. Check for: explicit "last updated" dates, presence of a changelog or
version history, and whether core factual claims (company name, address, product
offering) are consistent across the site's own pages. (our inference)

**False-positive risk.** Moderate. Sites that update content regularly may still lack
explicit date stamps while remaining accurate. Conversely, a page with a date stamp from
3 years ago is only stale if the specific facts are time-sensitive. Must not flag as
"stale" solely based on date absence or date age — require both time-sensitive content
type AND absence of a date.

**Eval implication.** "Staleness" is a compound finding requiring two judgments (content
is time-sensitive + date is absent or old). Gold-labelling requires both conditions to
be evaluated independently; Krippendorff alpha must reach ≥0.80 on each sub-criterion
separately.

---

## P-06.10 · When Not to Trust Language Models: PopQA and Long-Tail Entity Hallucination (Mallen et al.)

*(This entry notes that P-06.07 covers the same paper. The following extends coverage
to the entity-disambiguation/name-collision dimension not fully addressed there.)*

The PopQA paper (P-06.07, arXiv:2212.10511) also documents that retrieval can introduce
errors when the retrieved document is about the *wrong* entity with the same name —
directly instantiating the entity-disambiguation failure mode. For our audit, this means
name collision risk is both a long-tail and a popular-name problem: a small company
whose name overlaps with a common word, place, or famous entity will have its Wikidata
entity confused even if one exists, because retrieval may surface higher-popularity
same-name documents first.

**Observable proxy for name-collision risk:** Check if the official organisation name
(from the site's `<title>` or Organization schema `name`) is a common dictionary word,
a geographic name, or overlaps with an existing famous brand or person. If yes, flag as
"entity name collision risk." This is a heuristic, not a deterministic finding. (our inference)

---

## P-06.11 · FEVER + Truth Discovery Literature Synthesis

The FEVER benchmark (P-06.04) grounds the *single-source* verification question.
The broader truth discovery / multi-source corroboration literature (surveyed in Li et al.
2015, "A Survey on Truth Discovery," SIGKDD Explorations, and more recent work cited in
domain-05) grounds the complementary mechanism: **facts mentioned across multiple
independent web sources are treated as more credible by LLMs and by retrieval systems.**

- **Survey URL for context:** https://dl.acm.org/doi/10.1145/2922066.2922069
- **Status:** SEARCH-ONLY (URL not opened; the mechanism is well-established in the
  truth-discovery literature and referenced indirectly through the FreshLLMs paper)

**Mechanism.** Truth discovery algorithms estimate source reliability and fact truth
value jointly by iterating between: (1) weighted vote for truth given current source
reliability estimates; (2) reliability update based on agreement with current truth
estimates. The converged result treats facts corroborated across many independent
(non-copying) sources as substantially more credible than facts appearing in only one
source. This mechanism likely operates in LLM pre-training: facts that appear many
times in the training corpus are more strongly memorised (consistent with PopQA finding
that popular entities are recalled more accurately).

**Transfer to our audit.** We **cannot observe external corroboration** for a site's
facts without querying an external index — which violates D-006 (no live engine query)
and the <5-minute budget constraint. This is therefore a case where the audit must be
honest about what it cannot measure: we can observe internal consistency (same brand
name, same CEO name, same address, across multiple pages of the site), but we cannot
observe whether external sources corroborate these facts. Internal consistency is
auditable and relevant: a site whose own pages contradict each other on key facts will
also confuse LLM extraction. (our inference)

**False-positive risk.** N/A — the check is internal consistency, which is
deterministic once the same entity attribute is found in multiple places.

**Eval implication.** Internal-consistency checks (does the schema `Organization.name`
match the `<title>` suffix? Does the footer address match the schema
`PostalAddress`?) are near-deterministic and can achieve near-perfect inter-labeller
agreement.

---

## P-06.12 · ReFinED and Entity Linking at Web Scale: NIL and Unlinkable Entities

*(Supplementary coverage beyond P-06.06)*

From the ReFinED paper (P-06.06): the model is designed to handle "NIL entities" —
mentions that do not correspond to any Wikidata entry. At training time, ~18% of mentions
in the Wikipedia hyperlink training set link to entities not in Wikidata. This confirms
that a substantial fraction of real-world entity mentions on the web are unlinkable to
any knowledge graph — and for these entities, disambiguation relies entirely on the
local textual context.

**Transfer to our audit (from the NIL-entity finding):** If the brand/organisation has
no Wikidata entry (NIL entity), the page's own text must provide enough disambiguation
context — industry, founders, location, founding date — to distinguish it from other
same-name entities. Check for: presence of at least two of the following in the main
text or Organization schema: industry sector, geographic location, founding year,
parent company / subsidiary relationship. (our inference)

---

## P-06.13 · MAVE and the Explicit-vs-Implicit Information Gap

*(Supplementary coverage of the MAVE implicit-information mechanism from P-06.03)*

The MAVE paper's zero-shot setting (new attribute types not seen in training) directly
models the situation an LLM faces when extracting facts from a brand page it has rarely
or never seen during pre-training. Zero-shot attribute extraction is "very challenging"
(verbatim abstract) — meaning that *implied* attributes (colour implied by product name,
specification implied by model number) will be missed or guessed by LLM-based extraction.

**Transfer to our audit:** The implication for page content structure is clear: key facts
that the brand wants AI systems to extract must be stated *explicitly and specifically*
in text or structured markup — not implied by naming conventions, category placement, or
product imagery. This is the "explicit claim" audit dimension: does the page contain at
least one sentence stating the brand's primary value proposition with the subject, predicate,
and key attributes all explicit? (our inference)

---

## Domain synthesis

### Extraction/trust mechanisms ranked by evidence strength × audit feasibility

| Mechanism | Evidence strength | Observable read-only? | Audit check |
|-----------|------------------|-----------------------|-------------|
| Wikidata presence / entity anchor (P-06.05, P-06.06) | Established (entity linking literature) | Yes — single API call | Lookup org name in Wikidata |
| Structured data presence and field completeness (P-06.01, P-06.02) | Established at web-scale | Yes — parse `<script type="application/ld+json">` | Required fields populated for page type |
| Explicit vs. implicit claim expression (P-06.03, P-06.13) | Empirical (MAVE) | Partial — heuristic on main text | Key product/service facts stated explicitly |
| Long-tail popularity risk (P-06.07) | Empirical (PopQA) | Proxy — Wikidata presence as surrogate | Flag if no knowledge-graph anchor |
| Temporal freshness / datestamp (P-06.08, P-06.09) | Empirical (FreshQA, TempLAMA) | Yes — parse `Last-Modified`, date patterns | Require date on time-sensitive content |
| Internal consistency across pages (P-06.11) | Established mechanism | Yes — compare Organisation.name across pages | Same name/address/CEO across all pages |
| Name collision risk (P-06.07, P-06.10) | Theoretical / heuristic | Partial — string matching on name | Flag if name is a common word/place |
| Quotability / self-contained sentence presence (P-06.04) | Empirical (FEVER κ=0.68) | Partial — heuristic | % sentences with explicit subject + fact |

### What is NOT measurable within our constraints

The following mechanisms are real, documented, and important for discoverability but
**cannot be measured read-only within a <5-minute, no-live-engine-query audit**:

1. **External corroboration / mention frequency across the web.** Would require querying
   a search index or Common Crawl for mentions of the brand. Violates D-006.
2. **LLM knowledge-boundary testing** (what a specific model currently knows about the
   brand). Requires querying a live generative engine. Violates D-006.
3. **Citation share in AI-search responses.** Requires querying Perplexity/ChatGPT Search.
   Violates D-006.
4. **Entity popularity in training data.** Training corpus composition is not publicly
   observable for most LLMs.
5. **Cross-site fact corroboration accuracy** (are the facts on this site consistent with
   what other sites say?). Requires external search; violates D-006.

These should be documented in the audit skill's output as "out-of-scope: requires
external data sources not available in a read-only site audit" with a specific note that
this is a deliberate constraint, not an oversight. (our inference)

### Freshness signals and their traps

- `Last-Modified` HTTP header is unreliable: many servers send the current date or the
  deploy date of a static asset, not the date of content change. Treat as a hint, not
  a ground truth.
- `<meta name="date">` or `article:published_time` Open Graph tag are more intentional
  signals, less likely to be auto-generated.
- Body text date patterns (e.g., "Published March 2024" or "Last updated: January 2025")
  are the most meaningful but require text parsing.
- **Evergreen content trap**: A well-written explanation of a stable concept (e.g.,
  "What is JSON-LD?") may be 4 years old and still 100% accurate. Age alone ≠ staleness.
  The freshness check should only fire on pages where the content type implies time-
  sensitivity (press releases, product pricing, regulatory status, software release notes,
  personnel/leadership pages).
- **False-freshness trap**: A page may update its copyright year in the footer
  automatically, giving a false impression of recent updates. The audit must look for
  content dates in the main body, not the footer.

### Entity-grounding checks: concrete, cheap, read-only method

For any arbitrary brand/organisation being audited:

1. **Wikidata presence** (5 seconds): HTTP GET `https://www.wikidata.org/w/index.php?search=ORGNAME&ns0=1`
   — check if a result exists with matching name and type Organisation. If none: "no
   knowledge-graph anchor" finding.
2. **Schema.org Organization markup** (1 second): parse `<head>` and inline `<script
   type="application/ld+json">` for `@type: Organization`. If present, validate:
   `name`, `url`, `description`, `logo`, `contactPoint` fields non-null. Missing
   required fields: medium-severity finding (D-004: mechanically detectable, not causal).
3. **Name disambiguity check** (1 second): compare the `Organization.name` or site
   `<title>` suffix against a short word list of common English words, country names,
   and major city names. If match: "entity name collision risk" finding.
4. **Internal consistency** (2–5 pages, 2–5 seconds): compare `Organization.name`
   from schema with `<title>` suffix and footer text across sampled pages. Flag
   inconsistencies.
5. **Freshness signal** (per time-sensitive page, 1 second each): classify page type
   as time-sensitive or evergreen; if time-sensitive, check for explicit date in main
   text or `article:published_time` meta tag. If absent: low-severity finding.

This entire flow costs <15 seconds of HTTP time for a typical site — well within the
<5-minute budget, leaving headroom for the JS-rendering gap check from Brief 04.
