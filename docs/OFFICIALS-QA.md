# Officials' Q&A session — 2026-09-03

Notes from the Adobe hackathon officials' Round 3 clarification call (Satya, Nikash,
Samarth). 416 teams through to this round.

**Status of this document.** These are paraphrases and quotes from a live call transcript,
not a written spec. Where this conflicts with `round3-handout.pdf`, the PDF still wins —
but on points the PDF is silent about, this is the best guidance available.

---

## 1. Constraints that break parts of the current design

### 1.1 No headless browser — `rendered[]` is dead

> "Don't assume a browser or a runtime. What we expect is Node.js, Python runtime you can
> assume. So anything that you can extract out of the DOM."

Asked directly about Playwright:

> "That part of the submission which uses playwright, because of the sandbox constraints
> which are there, it won't kick in, so it won't help with the analysis which gets
> generated. […] If you want to include it, feel free — it doesn't harm. Just keep in mind
> [the size limit] and that it won't actually contribute to the running execution."

**Impact.** The entire `rendered[]` section of `BUNDLE-SCHEMA.md` cannot be populated in the
grading sandbox. Every check that depends on it is affected:

| Check | Depends on | Status |
| --- | --- | --- |
| CHK-D-003 | render gap (static vs rendered text) | **Must be re-derived from static HTML only** |
| CHK-E-014 | `computed_styles.contrast_pairs` | Contrast is unmeasurable without rendering; the other five WCAG checks survive from static HTML |
| CHK-E-015 | `mobile_375.horizontal_overflow` | Only `meta viewport` / `user-scalable=no` survive |
| CHK-E-016 | tap-target geometry | **Unmeasurable.** Cut or demote |
| CHK-E-018 | overlay geometry | Re-derive as a static heuristic, or cut |
| CHK-E-019 | blank first paint | Re-derive from `<noscript>` + static text volume |
| CHK-E-023 | `ad_area_pct_total` | **Unmeasurable.** Was already the weakest check (Caveat 1) — cut it |

This is the single largest change. Roughly a third of the engagement half was specified
against rendered geometry that will not exist.

**Note:** static HTML is still available, and a JS-render *gap* can still be inferred
one-sidedly — if the static HTML has no meaningful content, that is a finding regardless of
what JS would have produced. What is lost is the ability to confirm the rendered version is
fine.

### 1.2 No disk, no database — the bundle must live in memory

> "Don't assume you would be having some database or some local disk access etcetera, where
> you would write the stuff and read it. Keep it in memory."

**Impact.** `ARCHITECTURE.md`'s collector→analyser handoff cannot be "collector writes
bundle.json, analysers read it." The bundle has to pass through the agent's context, or be
produced and consumed within a single script invocation. This also makes §1.5 (context cost)
sharper — a large bundle in context is a direct budget cost.

### 1.3 The 5 minutes is wall-clock, including LLM inference

> "It is everything actually. Five minutes is if I run a prompt it should complete in five
> minutes."

Mitigated by: they guarantee slow target sites won't penalise us, marking is relative, and
every submission gets the same sandbox, sites and prompts.

**Impact.** Model thinking time counts against the cap, so context bloat is not just a
composition-rubric issue — it directly consumes runtime budget.

### 1.4 No fixed entrypoint, and it is not a CLI

> "Don't assume fixed entry points. Your marketplace would be added to the agent harness we
> have in a sandbox environment, and we run an evaluation prompt against it. It would not
> just be 'here is the website, go identify the issues' — that is one of them, but we'll be
> doing other things, looking at the structure."

And, to a team that had built a CLI producing `report.json`:

> "Don't assume that you have to provide some sort of a CLI. Assume it's a marketplace which
> would be installed and then used for answering questions. Those questions could be
> anything related to brand visibility."

**Impact.** The skills must be *legible and self-describing*, not merely executable. A grader
may read the marketplace and ask what it does without ever running an audit. `SKILL.md`
prose quality is graded directly, not just as documentation for our own scripts.

### 1.5 Context efficiency is explicitly a scoring axis

> "I could have a marketplace which consumes a lot of tokens, takes in a lot of context, and
> which results in it not doing as well as it could have, even though the marketplace had all
> the nice things. What would help is you have decomposed the marketplace into skills and
> references so that it is precisely able to address the things it finds in an efficient
> manner without bloating the context."

**Impact.** Validates progressive disclosure (lean `SKILL.md`, detail in `references/`).
Confirms the decomposition rationale in `ARCHITECTURE.md` §3.

### 1.6 Explicit warning about AI-generated bloat

Nikash, unprompted:

> "The easiest thing in the world would be to give the document to Claude and ask it to
> generate the whole answer. You could do that. But it would hurt in two ways. One, you would
> not be able to stand out, because Claude is good at execution, not thinking. Second, there
> would be a lot of bloatware — it tends to overdo things, and it could end up adding a lot
> of extra skills which don't add value, and that would hurt your overall chances."

**Impact.** Directly relevant to a 6-skill marketplace. `ARCHITECTURE.md` §6 ("why not
fewer, why not more") and §7's suppression-necessity test are exactly the right defence —
but they now need to be *demonstrably* true, not merely argued. Any skill that cannot be
shown to earn its boundary should be merged before submission.

---

## 2. Questions we had, now answered

### 2.1 Model variance — out of scope

> "We are not looking for deterministic standard output as in what output you produce. It is
> the structure that you need — so as long as you are adhering to the output structure, it's
> fine."

**Impact.** D-010's `pass^k`-at-k=5 all-runs-agree stability metric is over-engineered
against the actual grading criteria. Schema conformance is what is required. Run-to-run
stability remains a *quality* signal worth some effort, but it is not the gate we treated it
as, and it should not drive architecture decisions any more.

### 2.2 Bot-blocked sites — do not worry about them

> "Certain sites do not allow bots to crawl. Don't worry about them, because we have our own
> evaluation criteria which is not just limited to sites — we also assess the marketplace in
> its own right. And we will take care that the sites we evaluate against are sites which
> actually allow the agent to do its work, doesn't block."

**Impact.** The graceful-degradation work in `FETCH-STRATEGY.md` and `COMPLIANCE.md` is still
correct and still worth keeping (it is cheap, and robustness reads well when the marketplace
is reviewed statically), but it is **not a scoring risk**. It should not consume more build
time. Priority drops from "must handle" to "handle cleanly, move on."

### 2.3 Engagement without analytics — D-008 confirmed correct

A student asked directly whether, with no visitor analytics, engagement problems must be
inferred from site structure and content alone:

> "That's right. […] Don't assume that you have analytics. It's purely on the site content
> and structure that you have to infer the problems."

**Impact.** Open question 3 in `PLAN.md` is **closed**. D-008's conservative framing
("detect defects, don't predict engagement") is the officially expected interpretation, not
an under-answer.

### 2.4 Off-site corroboration by fetching other sites — permitted

> "It is okay that it reaches out to some other websites which may be used for cross
> corroboration of facts — let's say you reach out to Reddit or Quora to check the
> visibility of the brand. That is fine. But don't assume that you would be using some
> externally hosted server for doing computation out of band."

**Impact.** Confirms `FETCH-STRATEGY.md` §6 (Wikidata / Wayback / Common Crawl as keyless
public sources) is allowed — these are public sites we fetch, not out-of-band compute. Open
question 4 in `PLAN.md` is **closed**, and the approach is blessed. What is banned is
standing up our own server or depending on a private API.

### 2.5 Scripts are optional

> "Totally optional. If you can manage without, if your skill and references can carry it
> well enough, why not? It's not a mandate to include scripts — but if you feel scripts will
> make the marketplace more effective, they definitely will."

### 2.6 Crawl depth and page count — our call, but hygiene is mandatory

> "I'll not be prescriptive. Would you start from the sitemap? Would you start with the
> homepage and follow links? It's totally up to you."

But:

> "If your solution doesn't respect robots.txt, it doesn't go good. It should. It should not
> bombard the site with requests. It should be mindful of the sitemap, what's allowed and
> disallowed by robots, what meta tags are set — if I don't want a page crawled, it should
> respect all that."

**Impact.** Our collection procedure already does all of this. Worth making it *visible* in
`SKILL.md` prose since the marketplace is reviewed statically.

### 2.7 False positives — they have in-house validation sets

> "We have our own in-house expertise around what is actually a false positive versus what
> really makes sense. We have our own validation sets — sites where we know this site has
> these problems."

But also, on precision-vs-recall calibration:

> "I would intentionally avoid giving very specific guidelines because we want you to think
> broadly. A poor outcome is very simple boilerplate architecture with no novelty. A good
> outcome is someone who's solved the problem and also gone beyond what's in the brief."

**Impact.** False positives are detectable by them and do matter, but there is no published
calibration set and no stated precision/recall trade rate. Our FP-guard discipline is
well-aimed; the eval harness does not need to be as heavy as D-010 specifies.

### 2.8 `llms.txt` — officials consider it an acceptable recommendation

> "Typically llms.txt, it could be a suggestion. Let's say you are evaluating a website and
> it doesn't have llms.txt — your audit report could say, hey, this site doesn't have it, so
> one recommendation is to add it."

**This conflicts with D-007**, which bans recommending `llms.txt` on the evidence that 97% of
existing files were never requested in a 137k-domain measurement.

**Assessment.** The official phrasing is permissive ("could be"), not mandatory. Our
evidence-based refusal is defensible and is precisely the "beyond the common denominator"
reasoning they say differentiates submissions. **But silently omitting it looks
indistinguishable from missing it.** Recommended resolution: keep the refusal, and make it
*visible* — surface `llms.txt` in `recommendations[]` or `limitations[]` with the measured
reason we rank it low, rather than saying nothing. That converts a possible perceived miss
into a demonstrated piece of judgement. **Needs a D-014 decision.**

### 2.9 Other logistics

- **Runtimes:** Python and Node.js only. Avoid Go and other niche runtimes. Keep packages
  lightweight; stdlib preferred. Fetching via standard bash/curl is assumed available.
- **No front end.** "Don't make a front end for now. Focus on what is asked."
- **Size:** under 50 MB — implies not bundling runtimes or heavy assets.
- **Machine:** assume ~16 GB RAM, CPU only, no GPU.
- **Marking is relative.** Same sandbox, same sites, same prompts for every submission.
- **One submission per team.** No deadline extension. Submitting early is encouraged.
- **AI assistance encouraged**, but the value-add on top of it is what differentiates.

---

## 3. What they said they are actually looking for

Repeated across the call, in different words each time:

1. **Prioritisation is the differentiator.**
   > "Not just a laundry list of items. […] The real ingenuity lies in how you order them —
   > what moves the needle the most. Assigning the right priority to the problems and
   > suggestions is what differentiates across submissions."

   This strongly validates D-004 (evidence strength caps severity) as a *scoring* asset, not
   just an internal discipline.

2. **Beat the frontier-model baseline.**
   > "The common denominator becomes what the frontier models produce when you give them
   > this problem. The differentiating factor becomes how you interpret them and what is
   > your net addition on top of that."

3. **Vertical-specific insight is rewarded.**
   > "You would observe certain common denominators which are the 101 basics of brand
   > visibility. And then there would be something you uncover by looking at specific
   > verticals — what works for them, what are the common defects over there."

   Our collector already computes a site `archetype` (ecommerce / documentation /
   saas_marketing / news_editorial / local_business / brochure). Currently it only drives
   suppression. **Using it to drive vertical-specific checks and recommendations is an
   identified, officially-endorsed differentiator we are not yet exploiting.**

4. **Fixes must map to the findings.**
   > "Do the fixes that you produce actually map to the problems you identified? Let's say
   > they are disconnected — you identified a set of problems, but the fixes are not in line
   > with them."

5. **Recommendations, not fixes.**
   > "You won't be generating fixes. What you'd be generating is a set of recommendations —
   > I found this problem, and this is the recommendation of how to go about it."

---

## 4. A dimension we are currently missing: context carry-over

Satya raised this twice, unprompted, with a worked example — an airline site reached from a
"Delhi to Mumbai" query:

> "I was looking from Delhi to Mumbai, but then on the web page it's just generic things.
> Versus an experience where something I see on the page is related to what I already
> searched."

And again, framing the whole problem as three sequential stages:

> "Step one: I search — does my site appear? Step two: does it get cited? Step three: I use
> that citation to take an action […] Is that contextual? Does it relate to where I started,
> what my starting point was?"

**Our engagement half is entirely stage-agnostic defect detection** — WCAG failures, layout
integrity, overlays. We have nothing on whether the landing experience relates to the intent
that brought the visitor there. This is the "why don't they stay" question as the officials
actually frame it.

Read-only, static-HTML-observable proxies worth considering:
- Do deep links from search land on a page that answers a specific query, or bounce to a
  generic homepage? (redirect behaviour on deep URLs)
- Do product//category pages carry enough self-contained context to make sense as a
  *landing* page rather than as a page reached by navigating from home?
- Does the site preserve query parameters / support deep-linked state?
- Is there a mismatch between what a page's title and meta description promise and what its
  main content delivers?

This is unproven and needs mechanism work before anything ships, but it is the clearest
"beyond the common denominator" opening the officials handed us.

---

## 5. Action list

| # | Action | Priority |
| --- | --- | --- |
| 1 | Re-derive or cut the 7 render-dependent checks; rewrite `BUNDLE-SCHEMA.md` §`rendered[]` | **Critical** |
| 2 | Change the collector→analyser handoff to in-memory; no disk assumptions | **Critical** |
| 3 | Decide D-014 on `llms.txt` — recommend visibly with caveats, or refuse visibly | High |
| 4 | Downgrade the D-010 eval harness to the honest minimum; `pass^k` is no longer a gate | High |
| 5 | Audit all six skills for context cost; merge any boundary that can't be shown to earn itself | High |
| 6 | Exploit `archetype` for vertical-specific checks and recommendations | High — differentiator |
| 7 | Investigate context-carry-over / landing-intent checks (§4) | Medium — differentiator |
| 8 | Make robots.txt/politeness compliance visible in `SKILL.md` prose, not just in code | Medium |
| 9 | Verify every `SKILL.md` reads well to a human reviewer who never runs it | Medium |
| 10 | Stop further investment in blocked-site handling — keep what exists, move on | Low |
