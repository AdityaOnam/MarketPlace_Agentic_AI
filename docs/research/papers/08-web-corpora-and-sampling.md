# 08 — Web corpora and sampling methodology

Source review for the corpus that backs the Agent Skill Marketplace audit skill. Two jobs:
(1) find real, accessible lists/datasets of websites we can sample from, with honest access
terms; (2) settle the sampling and split methodology so the dev / held-out / negative-control /
adversarial sets are defensible rather than convenient.

**Status legend.** `VERIFIED` = the URL was fetched and read in this session.
`SEARCH-ONLY` = title/venue appeared plausibly in search results but the page could not be
opened. Anything unverifiable was dropped, not guessed. Our own reasoning is tagged
`(our inference)`. Access terms we could not confirm are written
"unclear — needs checking" rather than assumed.

**Standing project constraints this must respect:** read-only, robots.txt respected, no
authenticated areas, no rate abuse, <5 minutes per typical site, ≤50 MB submission zip,
graded on unseen sites with false positives penalised as heavily as misses.

---

## Part 1 — Corpora and site lists

### P-08.01 — Tranco: A Research-Oriented Top Sites Ranking Hardened Against Manipulation

- **Kind:** DATASET-DOC (+ TOOL; the underlying paper is Le Pochat, Van Goethem,
  Tajalizadehkhoob, Korczyński, Joosen — NDSS 2019, referenced from the site)
- **URL:** https://tranco-list.eu/
- **Status:** VERIFIED
- **What it gives us:** a daily-updated ranking of ~1M domains, built by averaging several
  independent popularity sources over a 30-day window (Cisco Umbrella, Majestic, Farsight,
  Chrome UX Report, Cloudflare Radar). It exposes permanent, citable list IDs, so a sample
  drawn today can be reproduced by anyone later — this is the property that matters for us,
  more than the ranking quality itself.
- **Access:** free, no credentials. CSV download via permanent URL, per-domain rank query, an
  API, BigQuery, and Python/Go packages. A custom-list configurator lets you choose which
  providers and what time window feed the list. **No blocker.**
- **Licence:** composite and not uniform — the site states the constituent sources carry
  different terms: Umbrella "free of charge", Majestic CC BY 3.0, CrUX CC BY-SA 4.0,
  Cloudflare Radar **CC BY-NC 4.0**. The NC clause on the Radar component is the thing to
  watch. Licence of the *combined* Tranco list as distributed: unclear — needs checking
  before any redistribution. We only need to redistribute a list of a few hundred domain
  names we selected, which is very likely fine, but we should not republish a Tranco slice
  wholesale. (our inference)
- **Transfer to our corpus plan:** Tranco is our **popularity-tier frame** and our
  reproducibility anchor. We record the exact Tranco list ID used, then draw stratified
  samples from rank bands (see plan §1). Using a pinned list ID means the dev/test split is
  re-derivable from the repo without shipping crawl data.
- **Limitation / bias:** a top-1M list is by construction a popularity sample, not a sample of
  the web. It over-represents large, well-resourced, English-language, US/EU sites — exactly
  the sites *least* likely to have the audit problems we detect. Sampling only from Tranco
  would bias our corpus toward clean sites and inflate apparent precision while hiding recall
  failures on the small-business long tail. Mitigation is in plan §1 (a deliberate long-tail
  stratum). Tranco is also a *domain* ranking: a rank is not evidence that the apex domain
  serves a meaningful page.

### P-08.02 — HTTP Archive

- **Kind:** DATASET-DOC / TOOL
- **URL:** https://httparchive.org/faq
- **Status:** VERIFIED
- **What it gives us:** a monthly crawl of millions of URLs on desktop and mobile, storing HAR
  records — bytes transferred, HTTP headers, load timings — plus Lighthouse runs. Crucially for
  us, its **URL list is drawn from the Chrome UX Report**, i.e. from real-user-visited origins,
  not from a link graph. It is the closest thing to a ground-truth reference for "what is
  normal on the web" for any header/markup/performance check we invent.
- **Access:** public via **BigQuery**. Query guidance lives at har.fyi. **Blocker to flag:**
  BigQuery is free to *read schema* but query execution is billed against a Google Cloud
  account; the free tier is limited (commonly cited as 1 TB of query processing per month, but
  the FAQ page itself does not state pricing — unclear, needs checking). HTTP Archive tables are
  large enough that a careless `SELECT *` can burn the free tier in one query. So: a Google
  account plus billing project is required, and query cost is a real, if small, risk.
- **Licence:** not stated on the FAQ page. **Unclear — needs checking** (the project has
  historically been described as open, but we should not assert a specific licence we did not
  read).
- **Transfer to our corpus plan:** two uses. (a) **Base rates.** Before we ship a check like
  "no `Organization` JSON-LD" we should know what fraction of the web has it; a check that
  fires on 85% of sites is not a finding, it is a description of the web. (b) **Stratum
  definition.** HTTP Archive carries technology detection (Wappalyzer-style) which lets us pick
  rendering-strategy and CMS strata rather than eyeballing them.
- **Limitation / bias:** HTTP Archive loads a **single page per origin** (the home page) in most
  historical configurations, from a fixed cloud location, with a specific Chrome build. It
  therefore under-represents deep pages, geo-varied serving, and anything behind an interaction.
  Do not treat it as a page-level sample of the web.

### P-08.03 — Chrome UX Report (CrUX)

- **Kind:** DATASET-DOC
- **URL:** https://developer.chrome.com/docs/crux
- **Status:** VERIFIED
- **What it gives us:** field (real-user) data on how Chrome users actually experience popular
  destinations — the official dataset behind Core Web Vitals. Available via BigQuery, the CrUX
  API, the CrUX History API, PageSpeed Insights, and CrUX Vis.
- **Access:** BigQuery (billed as above), plus a free API key for the CrUX API. **Blocker to
  flag:** the CrUX API requires a Google API key (a credential, though free), and is
  rate-limited — the docs page we read does not state the quota, so: unclear — needs checking.
- **Licence:** the documentation page is CC BY 4.0 and code samples Apache 2.0; the **dataset**
  licence is stated elsewhere as CC BY-SA 4.0 (per Tranco's description of its CrUX input,
  P-08.01). Treat the dataset as CC BY-SA 4.0 pending direct confirmation.
- **Transfer to our corpus plan:** CrUX is the *only* honest way to attach a real engagement-
  adjacent outcome (LCP/INP/CLS field percentiles) to a site in our corpus. That makes it the
  natural **labelling aid for the performance dimension** of the negative-control set: a site in
  the "good" bucket on all three CWV in field data is a defensible negative control for our
  performance checks. It is *not* something the shipped skill can rely on (an audited site may
  have no CrUX entry at all).
- **Limitation / bias:** **eligibility is the killer limitation.** The docs are explicit that
  not all origins or pages are represented — an origin must be publicly discoverable and have
  enough visitors for statistical significance. So CrUX systematically omits exactly the small
  and long-tail sites we most need in the corpus. Any corpus built by "sites that have CrUX
  data" is a corpus of popular sites. Also Chrome-only, and opt-in-to-sync-dependent.

### P-08.04 — Common Crawl

- **Kind:** DATASET-DOC
- **URL:** https://commoncrawl.org/get-started
- **Status:** VERIFIED
- **What it gives us:** petabyte-scale periodic crawls in three formats — **WARC** (raw HTTP
  request/response + metadata), **WAT** (computed metadata as JSON: headers, links), **WET**
  (extracted plaintext) — plus a **CDXJ/URL index** for point lookups and **web graph**
  (host/domain link graph) releases.
- **Access:** free to anyone, no credentials. `s3://commoncrawl/` in `us-east-1` (AWS Open Data
  sponsorship, anonymous access with `--no-sign-request`) or HTTPS via
  `https://data.commoncrawl.org/`. **Blockers to flag:** the data itself is free but *egress and
  compute are not* if you process at scale outside us-east-1; and the volume makes naive use
  impractical. For our purposes only the **CDXJ index** and targeted WARC range-requests are
  realistic.
- **Licence:** the page links a Terms of Use and Privacy Policy but does not restate them.
  **Unclear — needs checking** before redistributing any extracted content. (Common Crawl's
  crawl is of third-party copyrighted pages; the terms govern use, not ownership.)
- **Transfer to our corpus plan:** two narrow, high-value uses rather than bulk processing.
  (a) **Long-tail sampling frame** — the domain-level graph gives us a pool of real registered
  domains far outside Tranco's top ranks, which is where our under-sampled small-business and
  portfolio archetypes live. (b) **Snapshot precedent** — the WARC format is the standard,
  tool-supported container for a frozen page capture, which is what our reproducibility rule in
  plan §5 needs.
- **Limitation / bias:** Common Crawl is a **crawl**, so it inherits crawler bias: it does not
  execute JavaScript, it honours robots.txt, and its seed/frontier policy over-represents
  well-linked pages. A JS-only SPA looks near-empty in Common Crawl for reasons that have
  nothing to do with that site's real content — which is a bias for corpus-building but is
  *itself* a useful analogue for how a non-rendering AI crawler sees the page. (our inference)

### P-08.05 — Web Data Commons: structured data extraction from Common Crawl

- **Kind:** DATASET-DOC
- **URL:** https://webdatacommons.org/structureddata/
- **Status:** VERIFIED
- **What it gives us:** large-scale extractions of embedded structured data (Microdata, JSON-LD,
  RDFa, Microformats such as hCard/hCalendar/hRecipe) from Common Crawl, plus schema.org
  class-specific subsets, released as N-Quads with per-format statistics, for crawls spanning
  2009–2024.
- **Key quantitative result:** the October 2024 extraction covers **2.39 billion HTML URLs
  across 37.4 million domains, yielding ~74 billion triples, with over 16.5 million domains
  containing structured data**. The site reports a continuous increase in structured-data
  deployment, with **JSON-LD growing faster than Microdata**.
- **Access:** free download, no credentials, no application. **No blocker.**
- **Licence:** the page states the *extraction framework* is under the Apache Software License.
  The licence of the *extracted data* is **unclear — needs checking** (the underlying content is
  third-party web content, so the same caveat as Common Crawl applies).
- **Transfer to our corpus plan:** this is our **base-rate oracle for every structured-data
  check**, and it directly addresses the brief's false-positive worry. ~16.5M of 37.4M domains
  having *any* structured data means roughly half do not — so "no JSON-LD present" cannot be a
  high-severity finding on its own; it is unremarkable. The class-specific subsets also let us
  set archetype-conditional expectations (Product markup is expected on e-commerce, not on a
  docs site), which is exactly the negative-control logic in plan §3.
- **Limitation / bias:** inherits Common Crawl's crawler bias (no JS execution), so structured
  data injected client-side is invisible to WDC and its adoption figures are a **lower bound**.
  Also domain-level counts are dominated by large template-driven hosts (a single CMS can put
  markup on millions of domains), so "% of domains" overstates how deliberate the markup is.

### P-08.06 — A Long Way to the Top: Significance, Structure, and Stability of Internet Top Lists

- **Kind:** PAPER — Scheitle, Hohlfeld, Gamba, Jelten, Zimmermann, Strowes, Vallina-Rodriguez;
  IMC 2018, pp. 478–493 (DOI 10.1145/3278532.3278574)
- **URL:** https://arxiv.org/abs/1805.11506
- **Status:** VERIFIED
- **What it gives us:** the standard critique of using top-site lists as a sampling frame. It
  surveys how research communities use top lists, assesses their structure and temporal
  stability, shows rank manipulation is possible for some lists, and reproduces prior studies to
  measure how much the *choice of list* and the *date of list creation* change published results.
- **Key quantitative result:** list instability is large and regime-dependent — one list moved
  from roughly **21k daily changing domains to ~483k** after a January 2018 methodology change,
  becoming the most unstable of those studied; several lists show weekly fluctuation patterns.
  Instability is also a function of subset size (the top-N tail churns far more than the head).
- **Access:** free arXiv preprint; the ACM version is paywalled unless you have institutional
  access. **No blocker for the preprint.**
- **Licence:** arXiv posting terms; unclear — needs checking for redistribution of the PDF.
- **Transfer to our corpus plan:** this is the reason plan §1 **pins a specific Tranco list ID
  and a capture date** and stores the resolved domain list in the repo, rather than saying "top
  N sites". If we re-drew the sample later from a live list we would get a materially different
  corpus, and any before/after comparison of our checks would be confounded by corpus churn
  rather than by our changes. It also warns us that deep-tail ranks are noise: rank 800,000 is
  not meaningfully "less popular" than rank 600,000, so our popularity strata must be **coarse
  bands (orders of magnitude), not fine ranks**. (our inference from the stability result)
- **Limitation / bias:** the measurements predate the current Tranco/CrUX-era lists, so the
  specific churn numbers are historical. The structural argument (lists differ, drift, and are
  manipulable) is what transfers, not the exact figures.

### P-08.07 — WebArena: A Realistic Web Environment for Building Autonomous Agents

- **Kind:** PAPER + TOOL — Zhou, Xu, Zhu, Zhou, Lo, Sridhar, Cheng, Ou, Bisk, Fried, Alon,
  Neubig; 2023 (rev. 2024)
- **URL:** https://arxiv.org/abs/2307.13854
- **Status:** VERIFIED
- **What it gives us:** **fully functional, self-hosted website clones** across four domains —
  e-commerce, social forum, collaborative software development, content management — plus
  long-horizon tasks over them.
- **Key quantitative result:** the best GPT-4-based agent reached **14.41% end-to-end task
  success vs. 78.24% human**.
- **Access:** free; the environment is self-hosted (Docker images). **Blocker to flag:** it is
  *operationally* heavy — you must stand up the site containers locally, which costs disk and
  setup time. Licence of the code/images: unclear — needs checking.
- **Transfer to our corpus plan:** WebArena is attractive because a self-hosted clone is
  **perfectly reproducible and never changes under measurement** — the exact property our
  snapshot rule wants. But it is the *wrong content*: WebArena sites are functional app clones
  built for task-completion agents, not brand/marketing sites with discoverability and
  engagement properties. **Our recommendation: do not use WebArena sites as corpus members.**
  Use it, at most, as a zero-risk smoke-test target to prove the crawler runs end-to-end without
  touching a real site. (our inference)
- **Limitation / bias:** four domains only, synthetic content, no real-world SEO/structured-data
  surface, no real CrUX field data, no real robots.txt politics.

### P-08.08 — An Illusion of Progress? Assessing the Current State of Web Agents (Online-Mind2Web)

- **Kind:** PAPER + DATASET-DOC — Xue, Qi, Shi, Song, Gou, Song, Sun, Su; 2025
- **URL:** https://arxiv.org/abs/2504.01382
- **Status:** VERIFIED
- **What it gives us:** **Online-Mind2Web — 300 realistic tasks across 136 live websites** — and,
  more importantly for us, a methodological argument that earlier optimistic web-agent results
  were an artefact of flawed benchmarks. It also reports an LLM-as-a-Judge auto-evaluator
  reaching **~85% agreement with human judgment**, beating prior automatic evaluators.
- **Access:** free arXiv preprint; the site list is the reusable artefact. Dataset licence:
  unclear — needs checking.
- **Transfer to our corpus plan:** two things. (a) The **136-website list is a ready-made,
  citable, published list of live sites** with archetype variety, which we can use as a *frame*
  to sample from — it saves us hand-curation and it is defensible because someone else chose it.
  **Caution: it is public, so treat any site appearing in it as dev-eligible only, never
  held-out test** — a published list is exactly the kind of thing a model may have seen.
  (our inference) (b) The ~85% judge–human agreement figure is our realistic **ceiling
  expectation** for AI-assisted labelling of our own gold set; we should not design a protocol
  that assumes better.
- **Limitation / bias:** built for *task-completion* agents, so its site selection favours sites
  with completable transactional flows — under-representing docs, local business, portfolio, and
  small-brand sites. Live sites also drift, which is the paper's own reproducibility problem and
  becomes ours if we use the list without snapshotting.

### P-08.09 — Generalization in Adaptive Data Analysis and Holdout Reuse (the reusable holdout)

- **Kind:** PAPER — Dwork, Feldman, Hardt, Pitassi, Reingold, Roth; 2015
- **URL:** https://arxiv.org/abs/1506.02629
- **Status:** VERIFIED
- **What it gives us:** the formal statement of *why a holdout set decays with use*. Repeatedly
  validating adaptively-chosen hypotheses against a holdout overfits the holdout itself. The
  paper gives a practical method for reusing a holdout while provably avoiding this, with the
  validity guarantee grounded in differential privacy / description length, unified via
  "approximate max-information".
- **Key quantitative result:** the abstract claims validity for "a large number" of adaptively
  chosen hypotheses but states no specific bound; the concrete constants are in the body, which
  we did not read. **Reported here as "no specific number verified"** rather than a guessed figure.
- **Access:** free arXiv. **No blocker.**
- **Transfer to our corpus plan:** this is the theoretical justification for the **held-out
  hygiene rule** in plan §2. The practical form we can actually implement is not the
  noise-addition mechanism (we have too few sites for it to be meaningful) but its policy
  corollary: **pre-declare the number of held-out runs, and treat each look as a spent budget.**
  Every time we tune a check after seeing held-out results, the held-out set has partially become
  a dev set.
- **Limitation / bias:** the guarantees are asymptotic and assume a formal query model; a
  30-site held-out set run three times is nowhere near that regime. We take the *discipline*,
  not the theorem. (our inference)

### P-08.10 — Do ImageNet Classifiers Generalize to ImageNet?

- **Kind:** PAPER — Recht, Roelofs, Schmidt, Shankar; 2019
- **URL:** https://arxiv.org/abs/1902.10811
- **Status:** VERIFIED
- **What it gives us:** the empirical counterpart to P-08.09. New test sets were built by
  replicating the *original construction process* for CIFAR-10 and ImageNet, then existing models
  were re-scored.
- **Key quantitative result:** accuracy dropped **3–15% on CIFAR-10 and 11–14% on ImageNet**.
  The authors concluded the drop was **not caused by adaptivity** but by the models' inability to
  generalize to slightly harder images — i.e. **distribution shift**, since ranking was largely
  preserved and gains on the original set did transfer.
- **Access:** free arXiv. **No blocker.**
- **Transfer to our corpus plan:** the finding cuts both ways and we should report it honestly.
  It says (a) expect a **double-digit relative drop** when our checks move from dev sites to
  fresh sites, and budget for it rather than treating it as failure; and (b) the drop will
  probably be driven by the *new sites being different*, not by us having peeked — which means
  **stratification matching between dev and held-out is more important than holdout secrecy**.
  If our held-out set is drawn by the same procedure from the same strata as dev, a large drop is
  a real generalization failure and not a sampling artefact. That is precisely why plan §2
  specifies "same procedure, same strata, disjoint draw". (our inference)
- **Limitation / bias:** image classification with fixed labels is a much cleaner setting than
  "findings about an arbitrary website", where the label itself is partly a judgment call. The
  magnitude of the drop does not transfer; the mechanism does.

### P-08.11 — ClueWeb22: 10 Billion Web Documents with Visual and Semantic Information

- **Kind:** PAPER + DATASET-DOC — Overwijk, Xiong, Liu, VandenBerg, Callan; 2022
- **URL:** https://arxiv.org/abs/2211.15848
- **Status:** VERIFIED (paper); dataset distribution page could not be fetched (TLS certificate
  error on lemurproject.org in this session)
- **What it gives us:** a research web corpus of **10 billion web pages** carrying, per document:
  raw HTML, a **visual representation of the page as rendered by a web browser**, parsed HTML
  structure from a neural parser, and pre-processed cleaned document text. The rendered-visual
  layer is the distinguishing feature versus Common Crawl.
- **Access:** **BLOCKER — likely requires a signed licence agreement and possibly a fee.**
  ClueWeb corpora have historically been distributed under an organisational licence agreement
  through CMU/Lemur. We could not open the distribution page to confirm the current terms, so:
  **unclear — needs checking, and must be assumed to be an application/signature process, not a
  free download.** The paper itself is CC BY 4.0; that licence covers the paper, not the data.
  The number of languages is not stated in the abstract and we do not assert one.
- **Transfer to our corpus plan:** **not usable for us as a primary corpus** given the access
  friction and our timeline. Its real value is as a design precedent: it is the strongest public
  evidence that serious web corpora now store *rendered* representations alongside raw HTML,
  which validates plan §5's decision to snapshot **both** the raw HTTP response and the rendered
  DOM for every corpus page — the raw/rendered delta is itself one of our measurements.
- **Limitation / bias:** access gating; static snapshot from 2022, so increasingly stale for
  anything about current AI-crawler-era markup practice.

### P-08.12 — Interval Estimation for a Binomial Proportion

- **Kind:** PAPER — Brown, Cai, DasGupta; *Statistical Science* 16(2), 2001
- **URL:** https://projecteuclid.org/journals/statistical-science/volume-16/issue-2/Interval-Estimation-for-a-Binomial-Proportion/10.1214/ss/1009213286.full
- **Status:** VERIFIED
- **What it gives us:** the definitive treatment of confidence intervals for a proportion —
  which is exactly what our detection precision and recall are.
- **Key quantitative result / conclusion:** the standard **Wald interval has chaotic coverage
  properties**, worse than generally appreciated, and "common textbook prescriptions regarding
  its safety are misleading and defective." Recommended instead: the **Wilson** interval or the
  equal-tailed **Jeffreys** interval for small n, and **Agresti–Coull** for larger n.
- **Access:** free full text on Project Euclid. **No blocker.**
- **Transfer to our corpus plan:** this determines *how we report* our headline numbers. Our
  sample sizes are small (tens of sites, low-hundreds of findings) and our proportions will
  often be near 1 (we want precision ~0.9+), which is precisely the regime where Wald intervals
  collapse or run past 1.0. **We report precision and recall as Wilson score intervals, always,
  and never as a bare point estimate.** It also drives the sample-size arithmetic in plan §6.
- **Limitation / bias:** it assumes independent Bernoulli trials. Our findings are **not
  independent** — several findings come from the same site and share its idiosyncrasies. So the
  Wilson interval on a per-finding basis is optimistically narrow; the honest unit of
  independence is the *site*, not the *finding*. (our inference — this is the single most
  important caveat on our reported numbers.)

### P-08.13 — The Menlo Report: Ethical Principles Guiding Information and Communication Technology Research

- **Kind:** PAPER (policy/ethics framework) — U.S. Department of Homeland Security, August 2012
- **URL:** https://www-old.caida.org/publications/papers/2012/menlo_report_actual_formatted/
- **Status:** VERIFIED
- **What it gives us:** the standard ethics framework for network/ICT measurement research. Four
  principles: **Respect for Persons** (stakeholder identification, informed consent),
  **Beneficence** (balance risks and benefits), **Justice** (fairness and equity), and the
  ICT-specific fourth, **Respect for Law and Public Interest** (compliance, transparency and
  accountability). It explicitly frames the challenges of ubiquitous connectivity, conflicting
  legal regimes, and infrastructure sensitivity.
- **Access:** free HTML. **No blocker.**
- **Transfer to our corpus plan:** this is the citable justification for our crawl conduct rules,
  and it maps almost line-for-line onto constraints the hackathon already imposes.
  **Beneficence** → rate limiting and a hard page cap: the cost we impose on a third-party site
  must be trivially small relative to the benefit. **Respect for Law and Public Interest** →
  robots.txt compliance, honest and stable user-agent identification (no spoofing a browser to
  evade bot detection), no authenticated areas, no ToS circumvention. **Justice** → do not
  concentrate crawl load on small sites that can least afford it. The operational rules in plan
  §5 are written to satisfy these.
- **Limitation / bias:** it is a framework, not a rule set; it gives no numeric thresholds
  (requests per second, pages per site). Those remain our judgment call. (our inference)

### P-08.14 — Only One Out of Five Archived Web Pages Existed as Presented

- **Kind:** PAPER — Ainsworth, Nelson, Van de Sompel; ACM Hypertext & Social Media 2015,
  pp. 257–266 (DOI 10.1145/2700171.2791044)
- **URL:** https://dl.acm.org/doi/10.1145/2700171.2791044 (open PDF at
  https://www.cs.odu.edu/~mln/pubs/ht-2015/hypertext-2015-temporal-violations.pdf)
- **Status:** **SEARCH-ONLY** — the bibliographic record and reported figures were returned
  consistently by search, but both the ACM page and the ODU PDF failed to parse when fetched in
  this session (the PDF returned unreadable binary). Treat the numbers below as *reported by
  search results, not read by us.*
- **What it gives us:** the reason a web archive is a **flawed fixture source**. An archived page
  is labelled with the acquisition datetime of the root HTML resource, but its embedded
  resources (images, CSS, JS) were captured at different times — so the replayed page can be
  "temporally violative": a composite that never existed on the live web at any instant.
- **Key quantitative result (as reported by search, not verified by us):** at most **38.7%** of
  composite mementos are temporally coherent, and at most **17.9%** (~1 in 5) are both coherent
  and 100% complete. Using multiple archives raises mean completeness by 3.1–4.1% but *reduces*
  temporal coherence.
- **Access:** ACM DL page is paywalled for the formatted version; an author-hosted PDF is free.
- **Transfer to our corpus plan:** **do not use the Wayback Machine as our snapshot mechanism.**
  It is tempting (free, no crawling, permanent URLs) but a temporally-incoherent replay would
  make our audit produce findings about a page that never existed — poisoning both gold labels
  and measurements, in ways that look like random noise rather than a bug. We therefore take our
  **own** captures (plan §5), where root and subresources are fetched in one session, and we
  restrict Wayback to a *historical-context lookup* role (e.g. "did this page have this markup
  last year?"), never as the artefact under audit.
- **Limitation / bias:** the study is from 2015 and predates most modern JS-heavy sites; the
  coherence problem is very likely *worse* now, not better, since more of a page's content
  arrives via separately-archived subresources. (our inference)

---

## Coverage gaps — stated plainly

Things the brief asked for that we did **not** find and verify, and are therefore not claiming:

- **A public dataset of AI-assistant citations.** Nothing verified. If one exists we did not
  confirm it, so our off-site discoverability checks cannot be validated against a citation
  ground truth. This is a real hole in the eval story for the discoverability half.
- **Curated corpora of accessibility or site-quality labels.** Not verified. We therefore have no
  external gold labels for the on-site half and must generate our own (plan §1, labelling).
- **VisualWebArena / WorkArena / Mind2Web (original)** were not separately verified; only
  WebArena (P-08.07) and Online-Mind2Web (P-08.08) were. Our conclusion — that self-hosted
  task-agent environments are the wrong content for a brand-audit corpus — rests on WebArena.
- **HTTP Archive's licence** and **Common Crawl's / WDC's data terms** are unconfirmed. Before
  we redistribute anything derived from them, this must be checked.
- **A source specifically on stratified-sampling design for web measurement.** We did not find
  one; the stratification design in plan §1 is therefore **our own construction**, justified by
  P-08.06 (list bias) and P-08.10 (distribution shift), not by a paper that did it for websites.

---

# Proposed corpus & split plan

Everything below is executable. Where a number is a judgment call rather than a derivation, it
is marked `(our inference)`. This section is written to replace the placeholder content of
`docs/CORPUS.md`.

## 0. Design commitments (read these first)

1. **The unit of analysis is the site, not the finding.** Findings within a site are correlated
   (P-08.12 limitation). All confidence intervals are computed with a site-level clustering
   correction, and no headline number is ever reported without one.
2. **Sampling frames are pinned, never live.** A frame is a file of domains committed to the
   repo with the date and list ID it came from (P-08.06).
3. **Every eval run is against a frozen local snapshot we captured ourselves**, never against
   the live site and never against a web archive (P-08.14).
4. **Dev and held-out are drawn by the *same* procedure from the *same* strata**, disjoint at
   the registrable-domain level and at the parent-organisation level where we can tell. This is
   what makes a performance drop interpretable (P-08.10).
5. **No site name, brand, domain, or CSS selector from any set may appear in a shipped
   `SKILL.md` or script.** Enforced by a pre-submission grep of every corpus domain against the
   shipped bundle. A hit is a release blocker.

## 1. Dev corpus

**Size: 60 sites.** Rationale: large enough that each of the 6 archetype strata gets 10 sites,
which is the minimum at which "this check fires on most docs sites but no e-commerce sites" is a
visible pattern rather than an anecdote; small enough that 60 × <5 min of crawl is about
5 hours of machine time and one working pass of human review. (our inference)

**Stratification — a 6 × 3 design, primary by archetype, secondary by popularity tier:**

| Archetype (primary stratum) | n | Why it must be its own stratum |
| --- | --- | --- |
| E-commerce / product catalogue | 10 | Only stratum where `Product`/`Offer` markup is expected |
| Documentation / knowledge base | 10 | Deep, text-dense, low-conversion; kills "no CTA" style checks |
| SaaS / product marketing | 10 | Heavy JS, marketing copy, thin factual content |
| News / editorial / blog | 10 | Freshness signals genuinely apply here and nowhere else |
| Local business / services | 10 | `LocalBusiness`, NAP consistency, tiny teams, long tail |
| Portfolio / brochure / one-pager | 10 | Structurally minimal; the classic false-positive trap |

Within each archetype, the 10 are split by **popularity tier: 3 head / 3 mid / 4 tail.**
Tiers are coarse Tranco rank bands — head ≤ 10k, mid 10k–200k, tail > 200k or absent from
Tranco — because fine ranks are noise (P-08.06). The tail is deliberately over-weighted: it is
where audit findings actually live, and it is exactly what CrUX and Tranco under-cover
(P-08.01, P-08.03 limitations).

**Secondary balance constraints (enforced across the whole 60, not per stratum):**
- ≥ 15 sites whose primary content requires JavaScript to render (checked by comparing raw
  HTTP body text length to rendered DOM text length).
- ≥ 12 non-English primary-language sites, spanning ≥ 4 languages and ≥ 2 non-Latin scripts.
- ≥ 10 sites outside US/UK/EU registration or hosting.
- ≥ 20 mobile-first / responsive-only sites (no desktop-specific host).
- No more than 3 sites on any single CMS/platform signature, to stop us tuning on one theme.

**Procedure (executable):**
1. Pin the frame. Download a Tranco list by permanent ID; record the ID and date in
   `corpus/frames/tranco-<id>.csv`. Separately record the Online-Mind2Web 136-site list
   (P-08.08) as `corpus/frames/onlinemind2web.csv`, **flagged dev-eligible-only** because it is
   published and possibly model-visible.
2. Build the tail pool. Draw candidate registrable domains from the Common Crawl domain graph
   (P-08.04) filtered to those absent from the top 200k. Store as
   `corpus/frames/longtail-<crawl-id>.csv`.
3. Randomise, then classify. Shuffle each frame with a **recorded seed**. Walk the shuffled list;
   for each candidate, fetch only the home page (respecting robots.txt), and assign an archetype
   label. Labelling is AI-assisted with a human confirming each label; the LLM proposes,
   the human accepts or rejects. Do **not** let the LLM both propose and confirm.
4. Fill quotas. Accept a candidate only if its (archetype, tier) cell is unfilled. Reject and log
   a reason for: parked/for-sale pages, HTTP errors, robots.txt disallowing our path, sites
   requiring login to see any content, and anything adult/illegal. **Keep the rejection log** —
   the rejection rate per stratum is itself a finding and it is what sizes the adversarial set.
5. Freeze. Snapshot per §5. Commit `corpus/dev.csv` = `domain, archetype, tier, language, render_mode, seed_position`.

**Labelling the dev gold set.** Dev needs gold labels only on the subset used for recall
(see §6): **20 of the 60**, chosen 3–4 per archetype, exhaustively audited by hand against our
check catalogue. The other 40 are for *derivation and eyeballing*, not for metrics.

## 2. Held-out test corpus

**Size: 30 sites.** Same 6 archetypes (5 each), same tier proportions, same secondary balance
constraints at proportional scale. Drawn in the **same pass** as dev, from the same shuffled
frames, by continuing to walk the list after the dev quotas fill — this guarantees identical
procedure and no selection drift, which is what makes a dev→test drop interpretable (P-08.10).

**Disjointness:** no shared registrable domain, and no two sites from the same parent
organisation across the split where we can determine it. Online-Mind2Web sites are **excluded
from held-out entirely** (P-08.08).

**Hygiene rule — the part that is easy to violate:**
- Held-out domains are stored in a **separate file, `corpus/heldout.enc.csv`**, and the *labels*
  are not read by anyone during development. The domain list may be crawled and snapshotted
  early (so we're not blocked at the end), but the snapshots live in a directory that is not
  opened.
- **Total run budget: 3 runs.** Pre-declared, logged in `docs/DECISIONS.md` with the date, the
  git SHA of the skill bundle, and the reason for the run. Run 1 mid-build, run 2 after the last
  substantive change, run 3 reserved for a genuine emergency.
- **What happens if we look:** any inspection of a held-out site's pages or per-finding results
  beyond the aggregate metric **converts that site to dev**. It is removed from held-out,
  recorded as burnt in `DECISIONS.md`, and the reported test n drops. We do not replace it, so
  the cost of peeking shows up as a widening confidence interval. This is the practical form of
  the reusable-holdout discipline (P-08.09); we take the policy, not the theorem.
- Reported test numbers always carry the run index and n.

## 3. Negative-control set

**Purpose: measure false positives, which are penalised as heavily as misses.** A check firing
here is a defect, full stop. Construction is **per dimension**, not per site — a site is a
negative control *for a specific check family*, never globally.

**Size: 24 sites, 3 per dimension across 8 dimensions.** (our inference on the count: 3 is the
minimum at which a single fire is distinguishable from a fluke, and 8 × 3 fits one review pass.)

| Dimension | Negative control is a site that… | Verified by |
| --- | --- | --- |
| Structured data | has correct, validating `Organization` + type-appropriate schema.org | Manual read of the JSON-LD against schema.org |
| Crawler access | serves identical content to our UA and to a browser UA, robots.txt permissive | Byte/text diff of the two fetches |
| Performance | sits in the "good" bucket on all three CWV in CrUX field data | CrUX API (P-08.03) |
| Content structure | has a single H1, ordered heading hierarchy, answer-first intro | Manual outline check |
| Freshness | is genuinely **evergreen** — correct, undated, not stale | Manual read; this is the classic FP trap |
| Entity clarity | has an unambiguous brand name with a Wikidata entry and consistent NAP | Manual |
| Accessibility basics | passes an automated axe-style scan with zero violations | Automated tool, then manual spot-check |
| Minimal-by-design | is a legitimate one-page portfolio with no products, no blog, no team page | Manual — must NOT trigger "missing X" checks |

The last row is the most important and the most commonly botched: **absence is not a defect.**
Roughly half of all domains carry no structured data at all (P-08.05), so "no JSON-LD" is a
description of the web, not a finding.

**Metric:** false-positive rate per dimension = (controls where the check fired) / 3, reported
with a Wilson interval. **Target: 0 fires. Any fire is triaged before submission.** Negative
controls are **dev-side** — we look at them freely; that is their job.

## 4. Adversarial / edge set

**Size: 12 sites, one per condition.** Not scored for precision/recall — scored **only** for
graceful degradation. The pass criterion for every row is the same: the skill terminates inside
the time budget, emits valid JSON, and either reports the limitation as an explicit
"not determinable" finding or omits the affected checks — and **never** emits a substantive
finding it could not have evidenced.

| # | Condition | What it tests |
| --- | --- | --- |
| 1 | JS-only SPA (empty raw HTML body) | Do we detect non-rendering and say so, rather than reporting "no content"? |
| 2 | robots.txt disallowing `/` | Do we stop and report, rather than crawling anyway? |
| 3 | robots.txt allowing but with `Crawl-delay` | Do we honour it inside the 5-min budget? |
| 4 | Single-page site, no internal links | Does page-sampling logic survive n=1? |
| 5 | Very large site (>100k URLs, huge sitemap) | Page cap, sitemap streaming, no OOM, no overrun |
| 6 | Non-English, non-Latin script | Do readability/text checks abstain rather than misfire? |
| 7 | Paywalled / metered content | Do we avoid reporting "thin content" on a paywall? |
| 8 | Parked / for-sale domain | Do we recognise "this is not a site" and stop? |
| 9 | Differential serving to bots (cloaking) | Do we *detect and report* the discrepancy, without spoofing a browser UA to defeat it? |
| 10 | Aggressive bot protection (challenge page) | Do we fail cleanly, not retry-storm? |
| 11 | Very slow / intermittently timing-out origin | Timeout handling; the 5-min budget holds |
| 12 | Redirect chain / apex→www→locale | Canonicalisation without loops |

Rows 9 and 10 carry an explicit ethical rule from P-08.13: we identify ourselves honestly and do
not evade bot detection. Detecting cloaking is legitimate; defeating it is not.

## 5. Snapshotting and reproducibility

Live sites change under measurement, so metrics computed against live sites are not comparable
run-to-run. **Every corpus site is captured once and every eval runs against the capture.**

Per site, per page, we store:
1. The **raw HTTP response** (status, headers, unmodified body) — WARC or WARC-equivalent
   (P-08.04 gives the format precedent).
2. The **rendered DOM** after JS execution, plus the rendered text.
3. Fetch metadata: UTC timestamp, our user-agent, resolved IP, redirect chain, robots.txt as
   fetched at capture time.

Storing **both** raw and rendered is not optional: the delta between them *is* one of our
measurements, and it is the reason a rendered-corpus precedent like ClueWeb22 (P-08.11) matters.

**We do not use the Wayback Machine as the artefact under audit** (P-08.14): at most ~17.9% of
composite mementos are both temporally coherent and complete, so a replayed page may never have
existed, and the resulting label noise would be invisible.

**Re-capture policy:** the whole corpus is re-captured at most twice — once at corpus creation,
once before the final held-out run — and each capture is a versioned directory. Metrics are never
compared across capture versions without re-running both.

**Crawl conduct (from P-08.13):** honest fixed user-agent with a contact URL; robots.txt fetched
and obeyed for every host; ≥ 1 s between requests to the same host and max 2 concurrent
connections per host; hard cap of 100 pages per site; no authenticated areas; no form
submission; no ToS circumvention; abort on 429/503 and do not retry aggressively.

## 6. Sample size and confidence intervals — with the calculation

We report **precision** and **recall** as proportions, using **Wilson score intervals**, never
Wald (P-08.12).

**Step 1 — naive per-finding requirement.** For a target precision around p = 0.90 and a desired
half-width e, the normal-approximation sizing is `n = z²·p(1−p)/e²` with z = 1.96:

| Desired half-width | n (findings) |
| --- | --- |
| ±0.10 | 35 |
| ±0.075 | 62 |
| ±0.05 | 139 |

**Step 2 — correct for site-level clustering.** Findings from one site are not independent.
With m findings per site and intra-site correlation ICC, the design effect is
`DEFF = 1 + (m − 1)·ICC`. Assuming **m ≈ 10** findings per site and **ICC ≈ 0.20**
(our inference — no measured ICC for this setting exists; we will estimate it from dev and
revise), `DEFF = 1 + 9(0.20) = 2.8`.

**Step 3 — required sites.** To reach an *effective* n of 139:
`raw findings = 139 × 2.8 ≈ 389` → `389 / 10 ≈ 39 sites`. To reach effective n = 107
(half-width ≈ ±0.057): `107 × 2.8 = 300 findings` → **30 sites**.

**Conclusion: 30 held-out sites yields roughly ±6 percentage points on precision at p = 0.90.**
That is the honest resolution of our headline number, and it is what §2 sizes to. It is enough
to distinguish 0.90 from 0.75; it is **not** enough to distinguish 0.90 from 0.86, and we will
not claim otherwise. Reaching ±5 pp would require ~39 sites and ~390 hand-labelled findings —
rejected on labelling cost, not on principle. (our inference)

**Recall is sized separately and smaller.** Recall needs a denominator of "everything that
*should* have been found", which requires an exhaustive manual audit of each site — perhaps an
hour per site. We therefore compute recall on a **deep-labelled subset: 20 dev sites and 12
held-out sites**, and report it with a visibly wider interval. At 12 sites × ~12 true issues
= ~144 gold items, DEFF ≈ 3.2 → effective n ≈ 45 → half-width at p = 0.8 ≈ ±0.12. **Recall is
our weakest number and must be presented as such.**

**Reporting rule.** Every reported proportion carries: point estimate, Wilson interval, n
(both findings and sites), the capture version, and the held-out run index.

## 7. What ships in the ≤50 MB zip vs. what stays in the dev repo

**Ships (submission zip) — the skill bundle only:**
- `marketplace.json`, the entrypoint `SKILL.md`, the other skills' `SKILL.md` files, their
  `scripts/` and `references/`.
- Generic, site-agnostic reference material only: schema.org type expectations, threshold
  tables, severity rubric, the output JSON schema.
- **Nothing derived from a specific corpus site.** No domain names, no brand names, no
  site-specific selectors, no snapshots, no gold labels. Enforced by the §0.5 grep gate.

**Stays in the dev repo (tracked, small):**
- `corpus/frames/*.csv` (pinned frames with list IDs and dates), `corpus/dev.csv`,
  `corpus/heldout.enc.csv`, `corpus/negative-controls.csv`, `corpus/adversarial.csv`.
- The rejection log, the shuffle seeds, the labelling rubric, gold-label files.
- The eval harness code and the results tables.

**Stays local, git-ignored, never shipped:**
- All snapshots (raw WARC + rendered DOM). This is the bulk — tens of GB — and it is also the
  material whose redistribution licence is unresolved for Common-Crawl-derived content
  (P-08.04, P-08.05). Not shipping it sidesteps the question entirely.

## 8. What would falsify this plan

- **Dev→held-out precision drops by more than ~15 points.** Given identical sampling procedure
  and strata, that is a genuine generalization failure, not sampling drift (P-08.10) — the
  checks are tuned to dev sites and must be rewritten more abstractly.
- **Any negative control fires.** One fire on a hand-verified clean site means the check's
  precondition is wrong, and given the FP penalty it is cheaper to delete the check than to
  patch it.
- **Estimated ICC comes out far above 0.2** (say > 0.4). Then 30 sites is too few, the
  confidence intervals we planned are fiction, and we must either add sites or downgrade the
  claim to a qualitative one.
- **The rejection rate during frame-walking exceeds ~50% in any archetype.** That means the
  frame does not contain that archetype and the stratum is being filled by convenience sampling
  — the stratification would then be decorative.
- **More than one held-out site gets burnt by peeking.** That is a process failure, and the
  remaining test set is no longer a clean measurement of generalization.



