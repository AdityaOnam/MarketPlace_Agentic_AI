# 02 — Keyword-specific Q&A

Every term of art used in this repo, defined the way *this project* uses it. Alphabetical
within each group.

---

## A. Marketplace & skill format

### `agentskills.io`
**Q. What is it and why does it matter here?**
**A.** The provider-neutral spec for a single agent skill: a `SKILL.md` with YAML
frontmatter (`name`, `description`, `license`, `allowed-tools`) plus instructions, optionally
bundled with `scripts/` and `references/`. Every skill folder in the marketplace must
independently satisfy it. It defines the *single-skill* format only.

### `marketplace.json`
**Q. Is this part of the agentskills.io spec?**
**A.** **No.** agentskills.io does not define a multi-skill marketplace format —
`marketplace.json` is *this contest's own lightweight convention*. Ours lists `name`,
`version`, `description`, and a `skills[]` array of `{id, path, entrypoint?}`.

### `entrypoint`
**Q. What is it?**
**A.** The one skill marked `"entrypoint": true` in the manifest — the skill the grader
invokes. It is responsible for composing every other skill's output into the single audit
report. Exactly one is allowed. Ours is `audit-orchestrator`.

### `allowed-tools`
**Q. What does this frontmatter field do here?**
**A.** It declares which tools a skill needs. `site-evidence-collector` declares
`http_fetch headless_browser`; **all four other skills declare `allowed-tools: ""`**. That
empty declaration is how the read-only guarantee is *enforced* rather than promised — an
analyser has no tool with which to make a request.

### Progressive disclosure
**Q. What does it mean in this repo?**
**A.** Keep each `SKILL.md` lean and push detail outward: exact check rules and thresholds go
to `references/checks.md`, executable logic goes to `scripts/`. The orchestrator's README has
a load-order table saying exactly which file to read at which step. The officials named
context efficiency as a scoring axis, which is what this serves.

### Marketplace root
**Q. Which directory is zipped?**
**A.** `brand-ai-readiness-audit/` — containing `marketplace.json`, `README.md`, `skills/`,
and a shipped copy of `docs/`.

---

## B. Pipeline objects

### Evidence bundle
**Q. What is it?**
**A.** The single in-memory JSON document the collector emits and every analyser consumes
read-only. Sections: `site`, `robots`, `discovery`, `pages[]`, `rendered[]`, `links`,
`anchors`, `budget`. Every section carries a status of `ok` / `partial` / `unavailable` with
a reason.

### Finding envelope
**Q. What shape does an analyser return?**
**A.** A flat list of envelopes:

```json
{
  "check_id": "CHK-D-003",
  "state": "present | absent | not_determinable | not_applicable",
  "locus": { "url": "...", "selector": "..." },
  "evidence": "...",
  "severity": "critical | high | medium | low",
  "evidence_strength": "HARD-MECHANICAL | CAUSAL | NORMATIVE | CORRELATIONAL | THEORETICAL",
  "suggested_action": { "summary": "...", "priority": "..." },
  "suppressed_by": ["CHK-D-001"]
}
```

### `state`
**Q. What do the four values mean, and why four?**
**A.**
- `present` — the defect exists.
- `absent` — the check ran and the site is clean.
- `not_determinable` — the evidence needed could not be observed.
- `not_applicable` — an exclusion took the check out of scope for this site.

`absent` and `not_applicable` are **emitted, not dropped**, because the negative-control
evaluation must distinguish "checked and clean" from "never ran". And `not_determinable`
must never be readable as "no defect found".

### `locus`
**Q. What is it?**
**A.** Where the defect lives: `{url, selector}`, plus `scope: "site"` on a rolled-up
finding. It exists so a fix can be located, and it is half of the evaluation matching rule.

### `evidence`
**Q. Is it a quotation from the page?**
**A.** No — and this caused a real measurement failure. Every check emits **constructed
prose describing** the defect (`"robots.txt line 120: Disallow: / applies to Applebot
(retrieval-time AI crawler)"`), never a copy-pasted excerpt. A first matching rule that
demanded verbatim grounding pinned all 26 checks at 0.00 precision; see D-028.

### `instances[]`
**Q. What is it for?**
**A.** Always present on a finding — one entry per origin envelope, carrying that page's
locus and per-page evidence text. Even a single-page finding gets a one-entry array so the
shape is consistent.

### `occurrences`
**Q. When does it appear?**
**A.** When one defect spans **2 or more** sampled pages (`ROLLUP_MIN_PAGES = 2` in
`compose_report.py`). It carries `{pages, examples[]}` and the group's **worst** severity —
never an average, because a defect is as serious as its worst instance.

### `suppressed_by`
**Q. What does it record?**
**A.** Which other check caused this one to stand down. E.g. `CHK-E-019` carries
`suppressed_by: ["CHK-D-003"]` when both would otherwise fire (rule O-1).

### `recommendation_only`
**Q. Which checks carry it and why?**
**A.** `CHK-D-010`, `CHK-D-011`, `CHK-D-013`, `CHK-E-021`, `CHK-E-024`. Each was demoted —
either because it fired too broadly to function as a confirmed-defect claim (D-022), or
because hand-verification found the cited sources don't support the claim (D-027), or under
the single-source rule (D-004). The flag is **enforced in code**, not just documented: they
can never appear in `findings[]` at any severity.

---

## C. Severity & evidence vocabulary

### Evidence strength
**Q. What are the tiers and what does each cap?**
**A.**

| Strength | Meaning | Severity ceiling |
| --- | --- | --- |
| `HARD-MECHANICAL` | Consequence is definitional, not statistical (a blocked crawler is blocked) | critical |
| `CAUSAL` | Controlled experiment | critical |
| `NORMATIVE` | Violates a published standard (WCAG SC, Better Ads) | high |
| `CORRELATIONAL` | Measured association at scale, replicated | high |
| `THEORETICAL` / `PRACTITIONER` | Mechanism plausible, outcome not measured | medium |
| Single-study or contested | One unreplicated source, or sources disagree | low, or recommendation-only |

### Single-source rule
**Q. What is it?**
**A.** A check whose support reduces to one unreplicated study may not be emitted as a
finding at any severity; it ships as a proactive recommendation until a second independent
source is verified. Applied to `CHK-E-024`. *(D-004)*

### Severity ceiling rule
**Q. In one line?**
**A.** *Evidence strength caps severity.* `critical` is reserved for causal/hard-mechanical
findings that directly block AI retrieval or user access; normative caps at `high`;
theoretical at `medium`.

### `evidence_strength` vs `severity`
**Q. What's the difference?**
**A.** `severity` is how bad the defect is; `evidence_strength` is how well we can defend
the claim. The second constrains the first. Both ship on every finding so a reader can audit
the reasoning.

---

## D. Crawler & web terms

### Retrieval-time crawler
**Q. Definition?**
**A.** An agent that fetches pages **at answer time** so an assistant can cite them right
now: `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`, `Perplexity-User`, `Claude-Web`,
`Claude-User`, `Claude-SearchBot`, `Meta-ExternalFetcher`. Blocking one is `critical`.

### Training-corpus crawler
**Q. Definition?**
**A.** An agent that collects content for a future model's parametric memory: `GPTBot`,
`ClaudeBot`, `CCBot`, `Google-Extended`, `Applebot-Extended`, `Bytespider`, `Amazonbot`,
`Meta-ExternalAgent`. Blocking one is `low` and informational — **frequently deliberate
policy, not a defect**.

### Hybrid crawler
**Q. What happens to these?**
**A.** `Googlebot`, `Bingbot`, `Applebot` — classic index crawlers that also feed AI
surfaces. **A hybrid blocked at root is reported as retrieval-class**, because index removal
also removes the site from the AI surfaces built on that index.

### `unknown` / `generic` agents
**Q. Do they raise findings?**
**A.** Never. They are recorded so the evidence is complete and so the classification table
can be extended without touching any analyser. The table is **data, not logic**.

### RFC 9309
**Q. Why does it appear in the decision log?**
**A.** It is the robots.txt standard, including `$` and `*` metacharacters. Our parser
originally did pure prefix matching, so `Allow: /$` — *permit the root and nothing else* —
was never even a candidate rule, and a `critical`-severity check reported bookshop.org as
blocking crawlers it explicitly allowed. Fixed in D-031; `CHK-D-001` precision went 0.67 → 1.00.

### `crawl-delay`
**Q. Is it honoured?**
**A.** Yes, by the one skill that fetches, alongside a 2-concurrent-requests-per-host cap and
a 250 ms minimum gap (or the declared delay if longer).

### JSON-LD
**Q. What is checked?**
**A.** `schema.org` structured data embedded in the page. `CHK-D-007` checks
Organization/Person completeness; `CHK-D-029`–`D-034` check vertical-specific types
(Product/Offer, SoftwareApplication, Event/ItemList/JobPosting, NewsArticle, Person,
SoftwareSourceCode/DataCatalog).

### `sameAs`
**Q. What is it?**
**A.** The JSON-LD array declaring a brand's authoritative external profiles (knowledge
base, official social accounts, registries). `CHK-D-025` checks that any exist;
`CHK-D-026` checks that the declared ones resolve.

### Identity anchor
**Q. Definition?**
**A.** A URL the site itself declares as pointing at its own external identity — `sameAs`
entries and footer profile links. The **only** off-site evidence the audit collects, bounded
to 8 HEAD requests, one per host.

### `rel=canonical`
**Q. What does `CHK-D-008` want?**
**A.** A self-referential, same-domain canonical. Cross-domain or missing canonicals create
duplicate-content attribution risk — assistants citing a syndicated copy instead of the
original. Valid pagination canonicals pass.

### `<noscript>`
**Q. Why does it matter?**
**A.** It is the false-positive guard on the JS-rendering checks. A JS-only site with a
`<noscript>` fallback carrying > 50 words is **not** blank, and `CHK-D-003` / `CHK-E-019`
must stay silent.

### WCAG success criteria referenced
**Q. Which ones?**
**A.** SC 1.4.2 (Audio Control — autoplay), SC 1.4.4 (Resize Text — zoom blocking),
SC 2.4.4 (Link Purpose — anchor text), SC 2.5.8 (Target Size Minimum — 24×24 CSS px),
SC 1.3.1 (Info and Relationships — landmarks/headings), plus lang/alt/label failures.

### Better Ads Standards
**Q. Where is it used?**
**A.** As a `NORMATIVE` authority in the severity vocabulary. The one check that leaned
hardest on ad measurement (`CHK-E-023`, mobile ad density) was **cut** in D-018.

---

## E. Classification terms

### `archetype`
**Q. What is it and what does it control?**
**A.** The site's vertical. Values: `ecommerce`, `saas_marketing`, `news_editorial`,
`documentation`, `local_business`, `brochure`, `reference`, `institutional`, `marketplace`,
`personal`, `unknown`. It **decides which checks run at all** (a personal site is exempt from
identity-anchor and Organization-markup checks) and **how every surviving action is worded**.
Reported in `preamble.archetype`.

### `unknown` archetype
**Q. What happens then?**
**A.** Every archetype-conditioned check is **suppressed rather than guessed**. Guessing a
vertical activates suppression rules written for a different kind of site — a worse failure
than declining to judge. The classifier is deliberately conservative and abstains often.

### `page_type`
**Q. How does it differ from archetype?**
**A.** `archetype` labels the *site*; `page_type` labels each *page* (home, about, contact,
product, article, documentation, faq, login, legal…). It drives per-check exclusions —
e.g. `CHK-D-004` (thin content) skips contact/login/home pages.

---

## F. Report-level terms

### `preamble.access_state`
**Q. Three values, what do they mean?**
**A.** `ok` (at least one page fetched), `partial_block` (robots.txt reachable, zero pages —
a WAF/bot-management layer), `full_block` (nothing reachable). On either block state the
report deliberately does **not** invent a critical finding about the block; the preamble
field is the entire signal.

### `checks_passed[]`
**Q. What goes in it?**
**A.** Check IDs that ran to a clean `absent` and produced no present finding — what the
audit *verified*, not just what it found broken. A check that only produced
`not_determinable` or `not_applicable` is **not** listed: it was not measured.

### `strengths[]`
**Q. How is this different from `checks_passed[]`?**
**A.** It records mechanically verified *positive* signals (fresh sitemap, RSS/Atom head
link, complete Organization JSON-LD, canonical consistency or majority, a well-formed
permissive robots.txt, an existing Markdown representation). It does not invert defect
checks and does not affect the score.

### `top_priorities[]`
**Q. What is it?**
**A.** Up to three items — drawn by ID from the existing findings/recommendations, adding
nothing new — that a reader should act on first. Three priority classes: (1) retrieval-access
and static-content availability failures; (2) directly evidenced identity/canonical/detail
defects; (3) page-local heuristics. **Only class 1 and 2 items lead the report**; if there
are none, the array is empty rather than promoting a heuristic to fill slots.

### `degraded_stages[]`
**Q. Purpose?**
**A.** Names which stages did not run and which checks lost their evidence because of it —
so a check that went `not_determinable` is *visible* rather than silently absent.

### `meta_evaluation`
**Q. What is it?**
**A.** The orchestrator's self-check over its own finished report: `checks_run`, `passed`,
`warnings`. Nine checks including `summary_reconciles`, `severity_counts_reconcile`,
`finding_complete`, `no_duplicate_findings`, `known_check_id`, `prohibited_recommendation`,
`limitations_present`. **It never re-judges a finding.**

### Hard-drop gate
**Q. What is it and why is it the exception?**
**A.** A small enumerated set of meta-evaluation checks that *remove* an offending item and
record the removal as a warning: `prohibited_recommendation`, `contradicted_by_strength`,
`empty_recommendation`, `checks_passed_reconcile`. Everything else is a warning only.
Quietly rewriting a report until its own self-check passes is the exact failure mode D-010
was written against — so each gate keeps an audit trail.

---

## G. Evaluation terms

### Gold label
**Q. What is it and who writes it?**
**A.** A human-authored verdict per (site, check) cell, written **before** seeing any audit
output, from frozen snapshots, in a closed taxonomy: `PRESENT` / `ABSENT` / `UNMEASURABLE` /
`N/A`. **A model never authors a label** — it may only queue a disagreement for human
adjudication.

### Frozen snapshot
**Q. Why grade against them?**
**A.** Reproducibility. Each corpus site is captured once (HTTP response, headers,
robots.txt) into a content-addressed fixture, and all grading, re-running and judging happens
against the fixture — so a live site changing doesn't silently move the numbers.

### Negative control
**Q. What is the negative-control set?**
**A.** 15 sites curated *clean on one named dimension*, chosen by fetching and reading their
markup rather than by reputation. It measures clean-site false-positive behaviour. It is
**a screen, not a measurement** — 1–3 observations per check-dimension cell, so it reports
**counts, never rates**.

### Adversarial set
**Q. What is it for?**
**A.** 6 sites (bot-blocked, unfetchable, malformed) scored **only on graceful degradation**,
not on accuracy. One of them exposed a false-positive mechanism affecting 10 checks — an
unfetchable page read at face value — which was fixed before any gold label was written (D-023).

### Ablation (leave-one-skill-out)
**Q. What does it prove?**
**A.** Less than it looks. `ARCHITECTURE.md` §7 states plainly that **any disjoint partition
passes it**, because removing a skill mechanically removes its checks. It is reported, never
gated.

### Merge test
**Q. What is it?**
**A.** The deciding composition test: merge an adjacent pair of skills and re-run the full
eval. If precision, stability and runtime are unchanged, the boundary bought nothing — merge
it for real. It ran, and it did: six skills became five.

### Bundle-sufficiency test
**Q. What is it?**
**A.** Each analyser must run to completion on the bundle alone, with the network disabled.
Any analyser needing a fetch has the wrong boundary. Verified mechanically by grep: zero
networking imports in any analyser script.

### Suppression-necessity test
**Q. What does it ask?**
**A.** How often the orchestrator's cross-skill suppression and dedup rules actually fire
across the corpus. If they never fire, the orchestrator is a concatenator and the
decomposition is decorative. *It was written down before it was run, and it embarrassed the
design twice.*

### Krippendorff's α
**Q. What is it used for here?**
**A.** The intra-rater test–retest reproducibility metric: re-label an 8-site subset ≥ 48 h
later, blind, and compute α over the 4-category label per check ID. A check that cannot
reach **α ≥ 0.67 against the labeller's own second pass is cut**. *This pass has not yet run.*

### Site-level cluster bootstrap
**Q. Why not ordinary confidence intervals?**
**A.** Because findings on one site are correlated. The unit of analysis is the **site**, and
intervals come from 10,000 resamples of sites with replacement — never from treating findings
as independent.

### `pass^k` stability
**Q. Is it a gate?**
**A.** No — it was, and was demoted. The officials said *"we are not looking for
deterministic standard output… it is the structure that you need."* **Schema conformance at
100% is the gate**; set stability is measured at k=3 on 5 sites and reported, never gated,
and may not drive an architecture decision.

### Asymmetric justification
**Q. What is the rule?**
**A.** Any change to the matcher, rubric, or composite that **raises** scores requires
written justification plus a negative-control re-run in the same commit. Score-lowering
changes do not. It exists because we author both the checks and the gold labels.

---

## H. Analysis primitives

### Jaccard similarity
**Q. Where is it used?**
**A.** Twice. In `CHK-D-013` (near-duplicate templated content) over word trigrams of
`main_text`, and in the evaluation matching rule as a ≥ 0.6 token-Jaccard fallback on
evidence when CSS selectors don't match.

### Trigram hash
**Q. Why isn't it used for `CHK-D-013`?**
**A.** Because a single hash can prove two pages identical or different, but cannot produce a
similarity *percentage* — which Jaccard needs. So D-013 runs directly on `pages[].main_text`.

### Boilerplate removal
**Q. What is "main text"?**
**A.** The page's content after navigation, header, footer and chrome are stripped — the
thing a machine reader would actually receive as substance. Word counts in `CHK-D-003`,
`CHK-D-004` and `CHK-E-019` are counts of *that*, not of `<body>`.

### One-sided re-derivation
**Q. What does it mean?**
**A.** When a check normally compares two signals but only one is available, re-deriving a
weaker signal from the half that exists — and **capping it one severity tier below** the
two-sided result. Used by `CHK-D-003` and `CHK-E-019` when no headless browser exists
(D-015): the static half proves the fetch is empty, not that a render gap specifically caused it.
