# 07 — On-site engagement: observable page properties

**Brief:** `docs/research/AGENT-BRIEFS.md` § 07 · **Target:** 13–15 sources

## Why this file exists, and the constraint that shapes it

Our audit is **read-only, unauthenticated, and pointed at an arbitrary site we have never
seen**. That means we can never observe the outcomes the engagement literature actually
measures: bounce rate, dwell time, scroll depth, conversion, task success, rage clicks,
funnel progression. Those all require analytics access, session recording, or user testing.

So the only honest thing this half of the audit can do is:

> observe a **page-side property**, and cite evidence that this property is linked to a
> **measured engagement outcome** somewhere in the literature — while being explicit about
> whether that link is causal or merely correlational, and about the fact that we are not
> measuring the outcome ourselves.

Every entry below therefore carries an **Observable proxy** field. Where the honest answer
is "not observable read-only," that is stated plainly. The final `## Domain synthesis`
section contains the list of engagement problems that are **real but not observable** —
that list is arguably the most useful output of this brief, because it defines what our
skill must refuse to claim.

### Conventions used in every entry

- `Status: VERIFIED` — I fetched the page/paper and read it. `SEARCH-ONLY` — title, venue
  and result appeared consistently in search results but the primary source returned
  HTTP 403 / paywall and I could not read it directly.
- `Type: PEER-REVIEWED | INDUSTRY (not peer-reviewed)`
- `Evidence strength: CAUSAL | CORRELATIONAL | THEORETICAL | PRACTITIONER OBSERVATION`
- **Observable proxy** — what a read-only crawler can actually measure, or "not observable."
- Anything marked `(our inference)` is my reasoning, not the source's claim.

### A standing warning about numbers in this domain

Web-performance and UX advice is saturated with statistics that cannot be traced to a
primary source. Where I could not trace a widely-repeated number to a document I could
actually read, I say so in `## Untraceable and misattributed statistics` near the end
rather than repeating it. That section is deliberately part of the deliverable.

---

## Sources

### P-07.01 · Defining the Core Web Vitals metrics thresholds

- **Authors/venue/year:** Bryan McQuade, Google / web.dev developer documentation (published
  2020, revised through the INP transition)
- **URL:** https://web.dev/articles/defining-core-web-vitals-thresholds
- **Status:** VERIFIED
- **Type:** INDUSTRY (not peer-reviewed)
- **Evidence strength:** THEORETICAL (perception research) + PRACTITIONER OBSERVATION
  (achievability statistics). **Not causal for engagement.**
- **Mechanism:** Google states three criteria for every threshold: (1) it should represent a
  high-quality experience grounded in human-perception research, (2) it must be *achievable*
  by real content — at least ~10% of origins must already pass, (3) it must be consistently
  attainable by well-optimised sites. Measurement is at the **75th percentile of page loads**,
  chosen to cover most visits while damping outliers.
- **Key quantitative result:**
  - LCP good ≤2.5 s / poor >4 s. The perception basis cited is Miller and Card's work on
    attention loss "roughly from ~0.3 s to ~3 s". April 2020 achievability: 42% of phone
    origins and 51% of desktop origins met 2.5 s; ~26% phone / ~21% desktop were "poor" at 4 s.
    Thresholds of 1.5–2 s were rejected as *not consistently achievable*.
  - INP good ≤200 ms / poor >500 ms. Basis: Michotte's causality-perception work (~100 ms for
    perceived direct causation) and Nielsen's 0.1 s "instantaneous" limit. May 2022
    achievability: 56% of phones, 96% of desktop met 200 ms.
  - CLS good ≤0.1 / poor >0.25. The article states plainly that **no existing research was
    available** for layout shift; the threshold came from internal testing where "shifts of
    0.15 and higher were consistently perceived as disruptive."
- **Observable proxy:** Field CWV data is *not* observable for an arbitrary site without the
  CrUX API/BigQuery. What **is** observable read-only is **lab/synthetic** LCP, CLS and TBT
  from our own headless render, plus the *page-side causes* of bad CWV: no `width`/`height`
  or `aspect-ratio` on images, web fonts without `font-display`, render-blocking `<script>`
  in `<head>`, `@import` chains, absent `preconnect`, unsized ad/embed slots, oversized hero
  images served without responsive `srcset`, total transferred bytes.
- **Correlation vs. causation:** The thresholds are **not** derived from engagement data at
  all. They are perception research plus a feasibility quota. Anyone citing "2.5 s LCP" as an
  engagement-derived cutoff is misreading the source. (our inference)
- **False-positive risk:** HIGH if we grade lab CWV as if it were field CWV. A single cold
  synthetic run from one location on one network profile is not the 75th percentile of real
  users. **We should report causes, not verdicts.**
- **Transfer to our audit:** Emit findings about *structural causes* ("N images lack explicit
  dimensions; this is a known CLS cause"), never "your CLS is failing." Severity capped at
  medium unless the cause is unambiguous and multiple.
- **Eval implication:** Negative control needed — a fast, well-built page that happens to
  render slowly in our sandbox must not produce a finding.

---

### P-07.02 · Vodafone: a 31% LCP improvement produced 8% more sales (A/B test)

- **Authors/venue/year:** Vodafone / Google, web.dev case study, 2021
- **URL:** https://web.dev/case-studies/vodafone
- **Status:** VERIFIED
- **Type:** INDUSTRY (not peer-reviewed)
- **Evidence strength:** CAUSAL — but **n = 1 site**, and the manipulation is a bundle.
- **Mechanism:** Two visually and functionally identical landing pages; 50/50 traffic split
  from paid media (display, iOS/Android, search, social), ~100K clicks and ~34K visits/day per
  arm. Version A moved widget rendering from client-side to server-side, server-rendered
  critical HTML, and resized/lazy-loaded/SVG-optimised images.
- **Key quantitative result:** LCP 5.7 s (A) vs 8.3 s (B), a 31% improvement. Sales +8%,
  lead-to-visit rate +15%, cart-to-visit rate +11%.
- **Observable proxy:** The *interventions* are all read-only observable: whether critical
  HTML is present in the raw (no-JS) response vs only after hydration; whether images carry
  `srcset`/`loading="lazy"`/modern formats; SVG byte weight. The **outcome** (sales) is not.
- **Correlation vs. causation:** This is a genuine randomised A/B test, so the causal claim is
  sound *for this page, this traffic mix, this baseline*. Note the baseline LCP was 8.3 s —
  deeply "poor." Evidence that improving an 8.3 s page helps says **nothing** about improving
  a 2.4 s page to 2.0 s. Diminishing returns are not measured here. (our inference)
- **False-positive risk:** MEDIUM — extrapolating this to already-fast sites would generate
  low-value findings that a grader penalises.
- **Transfer to our audit:** Justifies a **high-severity** performance finding only when the
  page is in the "poor" band by clear structural evidence (e.g. client-side-only rendering of
  main content plus multi-MB unoptimised hero imagery). Below that band, downgrade.
- **Eval implication:** Stratify the eval corpus by baseline performance band; measure whether
  our severity assignment tracks it.

---

### P-07.03 · Milliseconds Make Millions (Google / Deloitte / 55)

- **Authors/venue/year:** Google, commissioned research by 55 and Deloitte Digital, 2020
- **URL:** https://web.dev/case-studies/milliseconds-make-millions ·
  report PDF: https://www.thinkwithgoogle.com/_qs/documents/9757/Milliseconds_Make_Millions_report_hQYAbZJ.pdf
- **Status:** VERIFIED (web.dev summary read in full; the 51-page PDF downloaded but its text
  layer did not extract cleanly, so PDF-only details are not asserted here)
- **Type:** INDUSTRY (not peer-reviewed)
- **Evidence strength:** CORRELATIONAL. The source itself describes monitoring real
  performance data "without making design changes" — i.e. observational, not experimental.
- **Mechanism:** 37 European and American brand sites, ~30 million mobile user sessions,
  tracked hour-by-hour for 30 days at the end of 2019. Naturally-occurring speed variation was
  related to funnel progression. Four metrics were each improved by 0.1 s: First Meaningful
  Paint (now deprecated), Estimated Input Latency, Observed Load Time, and Max Server Latency
  (TTFB).
- **Key quantitative result (per 0.1 s, by vertical):** Retail conversion +8.4% and spend
  +9.2%; travel booking rate +10%, checkout completion +2.2%; luxury +40.1% progression from
  product detail to add-to-basket; lead generation +21.6% progression to form submission and
  +7% pageviews.
- **Observable proxy:** TTFB and server-response time **are** directly observable read-only.
  Input latency and load time are observable only as our own synthetic measurements.
  Conversion and spend are not observable.
- **Correlation vs. causation:** **This is the most misquoted study in the domain.** It is
  routinely cited as "0.1 s faster → 8.4% more conversions," which is a causal claim the
  design cannot support. Faster sessions systematically differ from slower ones: better
  networks, newer devices, closer CDN edges, and plausibly higher-intent returning users. The
  page's own framing is monitoring, not intervention. The luxury +40.1% figure additionally
  sits on a very small baseline progression rate, which the source itself flags.
- **False-positive risk:** N/A directly, but **high reputational risk** if we quote the causal
  version in a report. We must not.
- **Transfer to our audit:** Supports including a **server-response-time** check (TTFB from a
  cold fetch, median over a few pages) as a real signal, described as *associated with*
  engagement, never *causing* revenue.
- **Eval implication:** Add a rubric item to the suggested-action quality check: no finding
  text may assert a revenue delta.

---

### P-07.04 · Attention web designers: You have 50 milliseconds to make a good first impression!

- **Authors/venue/year:** Lindgaard, G., Fernandes, G., Dudek, C., & Brown, J. M. (2006).
  *Behaviour & Information Technology*, 25(2), 115–126. DOI 10.1080/01449290500330448
- **URL:** https://www.tandfonline.com/doi/abs/10.1080/01449290500330448
- **Status:** SEARCH-ONLY — the publisher page returned HTTP 403. Citation, venue, pagination,
  DOI and study structure were consistent across Semantic Scholar, SciSpace and multiple
  citation indexes; I did not read the full text.
- **Type:** PEER-REVIEWED
- **Evidence strength:** CAUSAL for the narrow claim (controlled exposure-duration experiment)
  — but the outcome measured is **rated visual appeal**, not engagement.
- **Mechanism:** Three studies. Homepages presented for 500 ms and rated for visual appeal;
  a replication adding ratings on seven design dimensions; a third adding a 50 ms condition to
  test a mere-exposure explanation. Appeal ratings correlated highly between phases and between
  the 50 ms and 500 ms conditions.
- **Key quantitative result:** Visual-appeal judgements formed at 50 ms correlate strongly with
  those formed at 500 ms. **No bounce, dwell, or conversion outcome is measured.**
- **Observable proxy:** Very weak. "Visual appeal" is not read-only measurable in any defensible
  way. What is weakly observable is a *screenshot-level* proxy set: does the above-the-fold
  viewport render meaningful content at all, is there a visible heading and primary image, is
  contrast adequate. Aesthetic quality itself is **not observable** and we should not score it.
- **Correlation vs. causation:** The experiment is causal about *when* an impression forms. The
  leap from "impression forms in 50 ms" to "therefore ugly pages lose visitors" is **not in the
  paper** and is the standard misuse. (our inference)
- **False-positive risk:** VERY HIGH if we let a model grade "design quality" from a screenshot.
  This is exactly the kind of subjective finding a false-positive-penalised rubric punishes.
- **Transfer to our audit:** Justifies checking that the **first viewport is not empty or
  content-free** (pure hero video, cookie wall, or unhydrated skeleton). Does **not** justify
  aesthetic critique.
- **Eval implication:** Explicit negative control — a deliberately plain but functional page
  must produce zero aesthetic findings.

---

### P-07.05 · The role of visual complexity and prototypicality regarding first impression of websites

- **Authors/venue/year:** Tuch, A. N., Presslaber, E. E., Stoecklin, M., Opwis, K., &
  Bargas-Avila, J. A. (2012). *International Journal of Human-Computer Studies*, 70(11), 794–811.
  DOI 10.1016/j.ijhcs.2012.06.003
- **URL:** https://research.google/pubs/the-role-of-visual-complexity-and-prototypicality-regarding-first-impression-of-websites-working-towards-understanding-aesthetic-judgments/
- **Status:** VERIFIED (abstract and study structure read on the publisher-adjacent Google
  Research record; full text not opened)
- **Type:** PEER-REVIEWED
- **Evidence strength:** CAUSAL for the perceptual claim; **not** for engagement.
- **Mechanism:** Two controlled experiments manipulating visual complexity (VC) and
  prototypicality (PT) of real website screenshots, with exposure time as a factor
  (50/500/1000 ms in study 1; 17/33/50 ms in study 2).
- **Key quantitative result:** VC and PT both affect aesthetic ratings within 50 ms, and VC
  even at 17 ms; PT's effect grows with longer exposure. Conclusion: "websites with low VC and
  high PT were perceived as highly appealing."
- **Observable proxy:** **Prototypicality is the interesting one and it is partially
  observable.** Whether a page follows the conventional archetype for its type is inspectable
  read-only via structural conventions: is there a `<header>` with a logo linking to `/`, a
  recognisable primary nav, a `<main>` landmark, a `<footer>` with contact/legal links; for
  e-commerce, do product pages carry price, availability and an add-to-cart control in the DOM.
  Visual complexity is only crudely observable (DOM node count, distinct colours, number of
  above-fold interactive elements) and I would not stake a finding on it.
- **Correlation vs. causation:** Causal for *perceived appeal under tachistoscopic exposure*.
  There is no measured link here to staying on the site.
- **False-positive risk:** MEDIUM for prototypicality checks (a deliberately unconventional
  portfolio or art site is not broken), HIGH for any complexity score.
- **Transfer to our audit:** Supports **convention-conformance checks** (missing landmark
  regions, logo not linking home, no identifiable primary navigation) as engagement findings
  with a research-grounded rationale — the strongest aesthetics-adjacent thing we can measure.
- **Eval implication:** Include intentionally unconventional sites (artist portfolio,
  experimental agency site) as negative controls for prototypicality checks.

---

### P-07.06 · The WebAIM Million (annual accessibility analysis of 1,000,000 home pages)

- **Authors/venue/year:** WebAIM, Utah State University — annual report; figures below are from
  the 2026 edition as published at time of retrieval
- **URL:** https://webaim.org/projects/million/
- **Status:** VERIFIED
- **Type:** INDUSTRY (not peer-reviewed; methodologically transparent and widely cited)
- **Evidence strength:** DESCRIPTIVE / CORRELATIONAL — a prevalence census, not an outcome study.
- **Mechanism:** Automated (WAVE engine) analysis of the home pages of the top one million
  domains, counting detectable WCAG 2 failures.
- **Key quantitative result:** 95.9% of home pages had detected WCAG 2 failures (up from 94.8%
  the prior year); 56.1 errors per home page on average (up 10.1%). Six error types account for
  96% of all detected errors: low-contrast text (83.9% of pages), missing image alt text (53.1%),
  missing form input labels (51%), empty links (46.3%), empty buttons (30.6%), missing document
  language (13.5%).
- **Observable proxy:** **Fully observable read-only** — this is the single most crawler-friendly
  evidence base in the whole brief. Contrast, `alt`, label association, empty interactive
  elements and `<html lang>` are all static-DOM properties.
- **Correlation vs. causation:** No engagement outcome is measured at all. This tells us these
  defects are *common*, not that they *cost visits*. The engagement link must come from P-07.07.
- **False-positive risk:** LOW for `lang`, empty links/buttons, and unlabelled inputs.
  MEDIUM-HIGH for contrast on pages using CSS variables, gradients, background images, or
  states our renderer computes differently. Decorative images correctly carry `alt=""`.
- **Transfer to our audit:** Adopt the same six checks as our accessibility core, because they
  are high-prevalence, cheap, and unambiguous. Crucially, WebAIM itself states that "absence of
  detected errors does not indicate that a page is accessible" — our report must carry the same
  caveat verbatim in spirit.
- **Eval implication:** These checks should hit near-100% precision on our dev corpus; if they
  do not, our DOM/CSS handling is wrong, not the rule.

---

### P-07.07 · Guidelines are only half of the story: accessibility problems encountered by blind users on the web

- **Authors/venue/year:** Power, C., Freire, A., Petrie, H., & Swallow, D. (2012). *Proceedings
  of CHI '12*, pp. 433–442. DOI 10.1145/2207676.2207736
- **URL:** https://dl.acm.org/doi/10.1145/2207676.2207736
- **Status:** SEARCH-ONLY — the ACM Digital Library returned HTTP 403. The citation, venue,
  DOI, and the headline 50.4% figure were consistent across multiple independent citing sources;
  I did not read the paper itself.
- **Type:** PEER-REVIEWED
- **Evidence strength:** CORRELATIONAL / observational task study (this is measured user
  behaviour, not a controlled manipulation).
- **Mechanism:** Task-based evaluation with 32 blind users across 16 websites, yielding 1,383
  recorded instances of user problems, each mapped against WCAG 2.0 success criteria.
- **Key quantitative result:** Only **50.4%** of the problems users actually encountered were
  covered by any WCAG 2.0 success criterion. Reported alongside this: on ~16.7% of sites, the
  recommended WCAG technique had been implemented and the problem still occurred.
- **Observable proxy:** The finding itself is about the **limits** of observability. It gives us
  the calibration number: guideline conformance addresses roughly half of real barriers, and
  automated tooling covers only a subset of guideline conformance — so our automated pass covers
  substantially less than half of real accessibility-driven engagement loss. (our inference)
- **Correlation vs. causation:** This *is* measured user difficulty, so the link from defects to
  user problems is real. But it is not a bounce/conversion measurement.
- **False-positive risk:** N/A — this source constrains our claims rather than generating checks.
- **Transfer to our audit:** Mandates a **scope disclaimer** in the report: automated
  accessibility findings are a lower bound and a clean result is not a pass. This is the honest
  handling that a false-positive-penalised rubric should reward.
- **Eval implication:** Our eval must not treat "no accessibility findings" as ground-truth
  accessible; gold labels need an "undetectable by automation" category.

---

### P-07.08 · F-Shaped Pattern For Reading Web Content

- **Authors/venue/year:** Jakob Nielsen / Nielsen Norman Group, 2006, with an 11-year follow-up
- **URL:** https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content-discovered/
- **Status:** VERIFIED
- **Type:** INDUSTRY (not peer-reviewed)
- **Evidence strength:** PRACTITIONER OBSERVATION — eye-tracking of 232 users over thousands of
  pages, conducted and reported in-house without peer review or published statistics.
- **Mechanism:** Users scan unfamiliar text-heavy pages in two horizontal sweeps plus a vertical
  scan down the left, prioritising the first words of headings, paragraphs and list items.
- **Key quantitative result:** None reported in a statistical sense. Sample: 232 users. The
  article itself hedges: it is "a rough, general shape rather than a uniform, pixel-perfect
  behavior," and E-shaped and inverted-L variants occur depending on images and content length.
- **Observable proxy:** The *design response* is observable even though the behaviour is not:
  presence of a heading hierarchy, whether headings are front-loaded with informative words
  rather than generic ("Overview", "Welcome"), paragraph and list density, whether long prose
  blocks are unbroken by any subheading, whether the page leads with an answer or with preamble.
- **Correlation vs. causation:** No causal claim is available. The F-pattern is a *description of
  scanning*, and the widely-repeated inference "therefore front-load your headings and
  engagement improves" is **not tested** in this source.
- **False-positive risk:** MEDIUM-HIGH if we flag "wall of text" naively — a legal page, an
  academic abstract, or a long-form essay is correctly prose-heavy. Gate the check by page type.
- **Transfer to our audit:** Supports a **content-scannability** check limited to unambiguous
  cases: a content page with zero `<h2>`/`<h3>` under a very large word count, or heading text
  that is purely generic. Severity low-to-medium.
- **Eval implication:** Long-form editorial and legal pages belong in the negative-control set.

---

### P-07.09 · The Better Ads Standards (Coalition for Better Ads research)

- **Authors/venue/year:** Coalition for Better Ads, initial standards 2017, expanded to
  short-form video and apps subsequently
- **URL:** https://www.betterads.org/research/
- **Status:** VERIFIED
- **Type:** INDUSTRY (not peer-reviewed; consortium-run, methodology described publicly)
- **Evidence strength:** CAUSAL for *stated preference* (participants were randomly exposed to
  ad experiences in a controlled simulation) but CORRELATIONAL for the ad-blocker link.
- **Mechanism:** Paid participants read articles on four simulated content pages, three carrying
  different ad experiences and one ad-free; they rated each on annoyance/distraction and ranked
  them comparatively. Ratings were merged into a stack ranking of dozens of ad experiences, then
  combined with survey data on propensity to install an ad blocker.
- **Key quantitative result:** Desktop and mobile web standards drew on over 66,000 consumers in
  countries representing ~70% of global online ad spend (later phases: ~45,000 for short-form
  video, 45,000+ for apps). Experiences falling below the acceptability threshold include
  pop-ups, prestitials (with and without countdown), auto-playing video with sound, flashing
  animated ads, large sticky ads, and **ad density above 30% on mobile web / above 50% on
  desktop** (or above 30% on desktop when combined with sticky video).
- **Observable proxy:** **Strongly observable read-only.** Auto-playing `<video autoplay>`
  without `muted`; modal/interstitial overlays present in the initial DOM with high z-index
  covering the viewport; `position: fixed`/`sticky` elements and their share of viewport height;
  ad-slot area as a fraction of the first viewport; count of third-party ad/tracker origins.
  The 30%/50% density thresholds are directly computable from rendered element geometry.
- **Correlation vs. causation:** Preference and annoyance are measured; **abandonment is not**.
  The bridge to abandonment is the ad-blocker-propensity correlation, which is weaker.
- **False-positive risk:** MEDIUM. Cookie-consent banners are legally required and must not be
  scored as "intrusive interstitial" — but a consent wall that blocks all content *and* is
  non-dismissible on mobile is a legitimate finding. Newsletter modals that appear on scroll or
  timer are **not** in the initial DOM and may be missed entirely (a miss, not a false positive).
- **Transfer to our audit:** This is one of the few engagement checks with a **published
  numeric threshold** we can apply mechanically. Adopt the 30% mobile ad-density threshold and
  the auto-play-with-sound and prestitial checks verbatim.
- **Eval implication:** Needs a corpus of ad-supported publisher sites; also needs cookie-banner
  negative controls in several jurisdictions.

---

### P-07.10 · A study on tolerable waiting time: how long are Web users willing to wait?

- **Authors/venue/year:** Nah, F. F.-H. (2004). *Behaviour & Information Technology*, 23(3),
  153–163. DOI 10.1080/01449290410001669914
- **URL:** https://www.tandfonline.com/doi/abs/10.1080/01449290410001669914
- **Status:** SEARCH-ONLY — publisher page paywalled/403. Citation, pagination and headline
  result were consistent across CityU Scholars, Semantic Scholar and multiple citation indexes.
- **Type:** PEER-REVIEWED
- **Evidence strength:** CAUSAL (laboratory experiment manipulating delay and feedback), but
  small-scale and from 2004 on then-current connection speeds.
- **Mechanism:** Users abandon a page download past a tolerance threshold; **progress feedback
  extends that tolerance**. Two manipulations: presence/absence of feedback, and wait duration.
- **Key quantitative result:** Tolerable waiting time for information retrieval is approximately
  **2 seconds**; feedback measurably prolongs it.
- **Observable proxy:** Time-to-first-byte and time-to-first-contentful-paint from our own
  fetch **are** observable. More usefully, the *feedback* half is observable: does a
  client-rendered page show a skeleton/spinner/server-rendered shell, or a blank white screen
  until hydration? A blank first paint is the condition Nah shows is least tolerated.
- **Correlation vs. causation:** Causal for lab abandonment. But this predates broadband norms
  and mobile, and the widely-cited "2 seconds" is often quoted as if it were a modern field
  measurement of bounce. It is not.
- **False-positive risk:** MEDIUM — we cannot measure the user's actual network. Report the
  *structural* cause (no server-rendered shell, no loading state) rather than a time verdict.
- **Transfer to our audit:** Supports a check for **blank-first-paint on JS-only pages**:
  compare the no-JS HTML response body's visible text against the rendered DOM's; near-zero
  text without JS plus no loading affordance is a defensible finding. This check doubles as a
  discoverability check, which is a genuine argument for it earning its place.
- **Eval implication:** Pair with an SPA that *does* server-render as a negative control.

---

### P-07.11 · Interstitials and dialogs (Google Search Central documentation)

- **Authors/venue/year:** Google Search Central developer documentation; the underlying ranking
  signal shipped January 2017
- **URL:** https://developers.google.com/search/docs/appearance/avoid-intrusive-interstitials
- **Status:** VERIFIED
- **Type:** INDUSTRY (not peer-reviewed) — it is a **policy document**, not a study.
- **Evidence strength:** PRACTITIONER OBSERVATION. Google presents no public data behind it.
- **Mechanism:** Google defines the harm as "page elements that obstruct users' view of the
  content, usually for promotional purposes." Interstitials are full-page overlays; dialogs
  obstruct part of the page. Problem patterns: full-page interstitials blocking content;
  redirecting to a separate page for consent or input; overlays obscuring the whole page;
  interrupting app-install prompts.
- **Key quantitative result:** None reported. **This is important** — the interstitial policy is
  frequently cited as though it were backed by measured abandonment data. It is not; the
  measured evidence for interstitial harm is P-07.09, not this.
- **Observable proxy:** Highly observable. Fixed/absolute-positioned elements covering a large
  fraction of the initial viewport with high z-index; `<dialog open>`; body scroll-lock
  (`overflow: hidden` on `body`) present at load; app-install banners; whether the landing URL
  redirects to a consent page rather than overlaying.
- **Correlation vs. causation:** Neither — it is a stated rule. Its *practical* force for a
  brand is real (search visibility), which is a different mechanism from user abandonment.
- **False-positive risk:** MEDIUM-HIGH. Google explicitly exempts **legally mandated**
  interstitials: age gates for restricted content and consent screens. Our audit must whitelist
  cookie-consent and age-gate patterns, or it will fire on most EU sites — the archetypal
  false positive for this domain.
- **Transfer to our audit:** Check the *redirect* variant (consent served as a separate page
  rather than an overlay), which Google flags and which is also genuinely bad for crawlers.
  Check non-dismissible overlays with no visible close control in the accessibility tree.
- **Eval implication:** A dedicated EU-cookie-banner negative-control slice is mandatory.

---

### P-07.12 · Information Foraging (information scent)

- **Authors/venue/year:** Pirolli, P., & Card, S. K. (1999). *Psychological Review*, 106(4),
  643–675. DOI 10.1037/0033-295X.106.4.643
- **URL:** https://psycnet.apa.org/doi/10.1037/0033-295X.106.4.643 (publisher, paywalled);
  practitioner explainer: https://www.nngroup.com/articles/information-foraging/
- **Status:** SEARCH-ONLY — the publisher record is paywalled. Citation, volume, pages and the
  scent construct were consistent across PhilPapers, ScienceDirect topic pages and NN/g.
- **Type:** PEER-REVIEWED
- **Evidence strength:** THEORETICAL (a formal theory with a process model, ACT-IF, adapted from
  optimal foraging theory and Charnov's marginal value theorem).
- **Mechanism:** Users navigate using **proximal cues** — link text, headings, snippets,
  labels — to estimate the value, cost and location of **distal content** they cannot yet see.
  This estimate is the *information scent*. Weak or misleading scent causes users to abandon a
  patch (page/site) sooner, because expected gain per unit effort falls.
- **Key quantitative result:** None applicable — it is a theory paper, not an effect-size study.
  **This is exactly the kind of source that gets cited as if it produced a statistic.** It did
  not.
- **Observable proxy:** **The best-transferring construct in this brief.** Scent is carried by
  properties we can read directly: link anchor text (is it "click here" / "read more" / a bare
  URL, versus descriptive), navigation label specificity, page `<title>` and `<h1>` alignment
  with the content, whether headings describe content or are decorative, whether internal links
  have `title`/context, and whether the page's primary call to action is textually explicit.
- **Correlation vs. causation:** The theory is causal in structure but this paper measures no
  web engagement outcome. Treat as a **rationale** for checks, not as evidence of effect size.
- **False-positive risk:** LOW-MEDIUM for non-descriptive anchor text (also a WCAG 2.4.4 issue,
  so it is doubly grounded). HIGHER if we try to judge whether a label "matches user intent" —
  we do not know user intent for an arbitrary site.
- **Transfer to our audit:** Implement **scent checks that are lexical, not semantic**: count of
  non-descriptive link texts; `<title>`/`<h1>` presence and divergence; navigation items whose
  labels are single generic words ("Solutions", "Resources") with no supporting description;
  orphan pages reachable only from the sitemap.
- **Eval implication:** Non-descriptive-anchor detection should be measured for precision
  against a hand-labelled slice; "generic nav label" should probably be advisory-only.

---

### P-07.13 · How do users evaluate the credibility of Web sites? (Stanford Web Credibility)

- **Authors/venue/year:** Fogg, B. J., Soohoo, C., Danielson, D. R., Marable, L., Stanford, J.,
  & Tauber, E. R. (2003). *Proceedings of DUX '03*, pp. 1–15. DOI 10.1145/997078.997097
- **URL:** https://dl.acm.org/doi/10.1145/997078.997097
- **Status:** SEARCH-ONLY — ACM DL returned 403 on an adjacent request; citation, sample size
  and the headline percentage were consistent across the ACM record, Semantic Scholar and CiNii.
- **Type:** PEER-REVIEWED (conference proceedings, peer-reviewed venue)
- **Evidence strength:** CORRELATIONAL / descriptive content analysis of free-text comments.
- **Mechanism:** Prominence–Interpretation: a credibility judgement requires the user to
  *notice* an element and then *interpret* it. Whatever is most noticed dominates the judgement.
- **Key quantitative result:** 2,684 participants evaluated two live sites each. "Design look"
  was mentioned in **46.1%** of comments — the most frequent category — followed by information
  design/structure (28.5%), information focus (25.1%), company motive (15.5%), information
  usefulness (14.8%), accuracy (14.3%), name recognition/reputation (14.1%), advertising
  (13.8%), bias (11.6%), writing tone (9.0%).
- **Observable proxy:** "Design look" is **not** observable read-only in a defensible way.
  Several of the *lower-ranked* categories are: presence and completeness of an About page,
  physical address and contact details, author bylines and dates, an identifiable publisher
  entity, privacy policy and terms links, HTTPS with a valid certificate, and ad density
  (13.8% "advertising"). These are the credibility signals we can actually check.
- **Correlation vs. causation:** Frequency of mention in a comment is not a measure of effect on
  behaviour. High mention frequency for design look does **not** establish that redesigning
  raises trust, let alone engagement.
- **False-positive risk:** LOW for missing-contact/missing-About checks on commercial sites;
  HIGH if applied to personal or single-purpose pages where an About page is not expected.
- **Transfer to our audit:** A **trust-signal presence** check gated by site archetype: contact
  information reachable, organisation identifiable, content dated and attributed, HTTPS valid.
  These overlap usefully with the off-site/entity-grounding half of the audit (brief 06).
- **Eval implication:** Requires archetype classification to be reliable first; if archetype
  detection is noisy, this check inherits the noise.

---

### P-07.14 · Modeling dwell time to predict click-level satisfaction

- **Authors/venue/year:** Kim, Y., Hassan Awadallah, A., White, R. W., & Zitouni, I. (2014).
  *Proceedings of WSDM '14*, pp. 193–202. DOI 10.1145/2556195.2556220
- **URL:** https://www.microsoft.com/en-us/research/publication/modeling-dwell-time-to-predict-click-level-satsifaction/
  (PDF: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/KimWSDM2014.pdf)
- **Status:** SEARCH-ONLY — I retrieved the PDF but its text layer did not extract; the MSR
  record, ACM listing and Semantic Scholar agree on title, authors, venue and the core claim.
- **Type:** PEER-REVIEWED
- **Evidence strength:** CORRELATIONAL / predictive modelling on large-scale search logs.
- **Mechanism:** The industry-standard heuristic treats a click with **≥30 s dwell** as a
  satisfied click. The paper's central argument is that a single global threshold is wrong,
  because the dwell time required to indicate satisfaction depends on the **page's topic,
  length and readability level**. They model SAT/DSAT dwell distributions per click segment and
  show a satisfaction classifier using those features beats dwell-threshold baselines.
- **Key quantitative result:** Reported as significant improvements over dwell-time and
  search-performance-predictor baselines; I could not read the exact deltas, so I do not quote
  a number.
- **Observable proxy:** **Dwell time itself is categorically not observable read-only.** What
  this paper gives us instead is a warning about the *inverse* inference. Page length and
  readability — both fully observable (word count, sentence/word statistics, heading density) —
  **change what dwell time means**, they do not by themselves indicate dissatisfaction.
- **Correlation vs. causation:** Purely associational. Nothing here says shortening a page
  causes satisfaction.
- **False-positive risk:** This source's value is in *preventing* a false positive: a long,
  dense page is not evidence of an engagement problem. It is evidence that engagement on that
  page cannot be judged by generic thresholds.
- **Transfer to our audit:** Forbid any finding of the form "this page is too long" or "reading
  level too high" as a standalone defect. Allow only *relative* observations gated by archetype
  (e.g. a product listing page with a 4,000-word unstructured prose block).
- **Eval implication:** Add explicit negative controls: long-form documentation and legal pages
  must produce zero length/readability findings.

---

### P-07.15 · Target size study for one-handed thumb use on small touchscreen devices

- **Authors/venue/year:** Parhi, P., Karlson, A. K., & Bederson, B. B. (2006). *Proceedings of
  MobileHCI '06*, pp. 203–210. DOI 10.1145/1152215.1152260
- **URL:** https://www.microsoft.com/en-us/research/publication/target-size-study-for-one-handed-thumb-use-on-small-touchscreen-devices/
- **Status:** SEARCH-ONLY — citation, venue, pagination, DOI and two-phase design confirmed via
  the MSR record, dblp and ACM listings; I did not read the full text.
- **Type:** PEER-REVIEWED
- **Evidence strength:** CAUSAL (controlled experiment varying target size, measuring speed and
  error rate).
- **Mechanism:** Below a size threshold, thumb-driven tap accuracy degrades — errors and
  correction cost rise. Two phases: discrete single-target tapping, and serial tapping (text
  entry). Button location had no effect on completion time or error rate in their design.
- **Key quantitative result:** ⚠️ **Traceability caveat.** The widely-repeated figures from this
  paper are 9.2 mm for discrete targets and 9.6 mm for serial targets. My verification pass
  surfaced the paper's design and its status as the source of these recommendations, but did
  **not** surface the exact millimetre values in a primary-source text I read. I therefore do
  not assert them as verified; treat "roughly 1 cm minimum" as the safely-supported summary.
- **Observable proxy:** **Directly observable.** Rendered bounding-box dimensions of interactive
  elements (`a`, `button`, `input`, `[role=button]`) under a mobile viewport emulation, plus
  spacing between adjacent targets. Also: presence and correctness of
  `<meta name="viewport" content="width=device-width...">`; whether the page requires horizontal
  scrolling at 375 px; whether `user-scalable=no` / `maximum-scale=1` blocks pinch-zoom (also a
  WCAG 1.4.4 failure).
- **Correlation vs. causation:** Causal for tap error rate in a lab. The step from tap errors to
  site abandonment is an inference, not a measured finding. (our inference)
- **False-positive risk:** MEDIUM. Inline links inside a paragraph of body text are legitimately
  small and should be excluded; only standalone controls should be measured. Elements hidden
  behind menus may report zero-size boxes and must be excluded, not flagged.
- **Transfer to our audit:** Three concrete mobile checks: (1) viewport meta present and
  device-width; (2) zoom not disabled; (3) standalone tap targets below ~24–44 CSS px with
  insufficient spacing — using the **WCAG 2.2 SC 2.5.8 Target Size (Minimum) 24×24 CSS px**
  bar as the citable normative threshold rather than a lab millimetre figure. `(our inference:
  citing the normative WCAG threshold is safer than a lab number I could not verify)`
- **Eval implication:** Measure on mobile-emulated renders only; desktop-only measurement will
  produce systematic false negatives.

---

### P-07.16 · "What is beautiful is usable" — and why it is contested

- **Authors/venue/year:** Tractinsky, N., Katz, A. S., & Ikar, D. (2000). *Interacting with
  Computers*, 13(2), 127–145. DOI 10.1016/S0953-5438(00)00031-X. Counter-evidence:
  Sonderegger & Sauer (2010), *Applied Ergonomics* 41(3), "The influence of design aesthetics in
  usability testing." Meta-analysis: "Attractive Things Do Work Better: A Meta-Analysis on Visual
  Aesthetics and User Performance," *International Journal of Human–Computer Interaction* (2026).
- **URL:** https://www.ise.bgu.ac.il/faculty/noam/papers/00_nt_ask_di_iwc.pdf ·
  https://www.sciencedirect.com/science/article/abs/pii/S0003687009001148 ·
  https://www.tandfonline.com/doi/full/10.1080/10447318.2026.2664081
- **Status:** SEARCH-ONLY for all three (author-hosted PDF and publisher pages not opened).
- **Type:** PEER-REVIEWED
- **Evidence strength:** CORRELATIONAL in the original (aesthetics was **not** experimentally
  manipulated), with **failed causal replications**.
- **Mechanism:** Claimed: perceived beauty raises perceived usability. The original used an ATM
  surrogate, replicating Kurosu & Kashimura; MANCOVA indicated aesthetics affected post-use
  perceptions of usability while actual usability did not.
- **Key quantitative result:** The original reports strong pre- and post-use correlations. The
  counter-literature is the important part: experiments that *manipulate* aesthetics find
  aesthetics did **not** affect perceived usability, while usability **did** affect post-use
  perceived aesthetics — i.e. the arrow may run the other way. The 2026 meta-analysis addresses
  the aesthetics→*performance* link separately and stresses that subjective usability ratings
  and objective performance can diverge or contradict.
- **Observable proxy:** None. Aesthetic quality is not measurable read-only, and the underlying
  effect is contested even in the lab.
- **Correlation vs. causation:** This entry exists precisely to mark the gap. The
  aesthetic-usability effect is a **correlational finding widely narrated as causal**, with
  reversed-direction replications.
- **False-positive risk:** N/A — this is a prohibition, not a check.
- **Transfer to our audit:** **Do not emit aesthetic findings.** No "your design looks dated,"
  no "improve visual hierarchy," no screenshot-based style critique. Under a rubric that
  penalises false positives as heavily as misses, subjective design commentary is pure downside.
- **Eval implication:** Add a rule-level assertion to the harness: zero findings whose evidence
  field is a subjective visual judgement.

---

## Untraceable and misattributed statistics

These are numbers I encountered repeatedly while researching this brief and either could not
trace to a readable primary source, or traced to a source that does not support the claim as
usually stated. **None of them may appear in our skill's output or our submission narrative.**

| Claim as usually stated | What I could actually establish |
| --- | --- |
| "53% of mobile site visits are abandoned if a page takes longer than 3 seconds." | Traceable to a real September 2016 Google/DoubleClick report (attributed to Alex Shellhammer), based on >10,000 mobile web domains. But: it is vendor research published while Google was promoting AMP; it has never been independently replicated; "abandoned" is not defined as bounce; and there is a measurement-circularity problem — pages that never finish loading may never fire the analytics beacon used to count them. **Directionally plausible, not a citable precise figure, and a decade stale.** |
| "A 1-second delay costs 7% of conversions." | I did not locate a readable primary source in this pass. Commonly attributed to a 2008 Aberdeen Group report that is not publicly available. **Do not use.** |
| "Every 100 ms of latency costs Amazon 1% in sales." | Widely repeated, attributed to unpublished internal Amazon work circa 2006–2009. No primary document. **Do not use.** |
| "0.1 s faster loading causes an 8.4% conversion increase." | The underlying study (P-07.03) exists and is real, but it is **observational**, and its own framing is monitoring without design changes. The causal phrasing is a misstatement of the source. |
| "You have 50 ms to make a first impression, so bad design loses visitors." | The first clause is supported (P-07.04, P-07.05). The second clause is **not in either paper** — neither measures leaving. |
| "Users read in an F-pattern, therefore front-loading headings improves engagement." | The F-pattern observation is real practitioner eye-tracking (P-07.08) and the article itself hedges heavily. The engagement consequence is untested. |
| "Users only read ~20–28% of the words on a page." | Derives from a 2008 NN/g re-analysis of academic browsing data. I did not verify the primary dataset in this pass. **Do not quote a percentage.** |
| "Tap targets must be at least 9.2 mm / 48 px." | The lab origin (P-07.15) is real but I could not verify the millimetre values in primary text. Use the **normative WCAG 2.2 SC 2.5.8 threshold of 24×24 CSS px** instead, which is citable and unambiguous. |
| "Accessible sites convert better / accessibility has an X% revenue impact." | I found no traceable primary evidence for any such figure. The defensible claim is P-07.07: guidelines cover ~half of real barriers experienced by blind users. **Do not make revenue claims.** |

---

## Domain synthesis

### A. Signals ranked by (evidence strength × crawler observability)

Ranked for a read-only, unauthenticated, <5-minute audit. "Observability" means: measurable
from a fetched HTML response plus one headless render, with no analytics, no API key, no
user testing.

**Tier 1 — stake the design on these.** Unambiguous, cheap, high precision, defensible source.

1. **Machine-detectable WCAG failures, restricted to the WebAIM six** — low-contrast text,
   missing `alt`, unlabelled form inputs, empty links, empty buttons, missing `<html lang>`
   (P-07.06). Highest prevalence, lowest ambiguity, purely static-DOM.
2. **Zoom/viewport blocking and mobile layout integrity** — missing or fixed-width
   `<meta viewport>`, `user-scalable=no`, horizontal overflow at 375 px, standalone tap targets
   under 24×24 CSS px with inadequate spacing (P-07.15 + WCAG 2.2 SC 2.5.8).
3. **Non-descriptive link text and title/heading integrity** — "click here", bare URLs, missing
   `<title>`, missing or duplicated `<h1>`, heading-level skips (P-07.12 grounds the mechanism;
   WCAG 2.4.4 grounds the rule). Doubles as a discoverability signal.
4. **Content-blocking overlays and the consent-redirect pattern** — full-viewport fixed overlays
   with body scroll-lock present at load; consent served as a redirect to a separate URL rather
   than an overlay (P-07.09 for the measured user-annoyance evidence, P-07.11 for the policy).
   Must whitelist dismissible cookie/age gates.
5. **Blank first paint / client-side-only content** — no-JS response contains near-zero visible
   text and no loading affordance, while the rendered DOM contains the real content (P-07.10).
6. **Auto-playing media with sound** (P-07.09). Trivially observable, measured as among the
   least-tolerated experiences.

**Tier 2 — worth emitting, at reduced severity.**

7. **Structural CLS/LCP causes** — images and iframes without intrinsic dimensions, fonts
   without `font-display`, render-blocking head scripts, absent `preconnect` to critical
   third-party origins, very large hero images without `srcset` (P-07.01 for why these
   matter mechanically; P-07.02 for the one A/B result showing the bundle pays off).
8. **Server response time (TTFB)** on a cold fetch, median across a few pages (P-07.03).
9. **Ad/promo density in the first viewport** against the published 30% mobile / 50% desktop
   thresholds (P-07.09).
10. **Prototypicality / convention conformance** — no `<main>`, no identifiable primary nav,
    logo not linking home, e-commerce product pages lacking price/availability in the DOM
    (P-07.05). Gate by detected archetype.
11. **Trust-signal presence** — contact route, identifiable organisation, dates and bylines on
    content, valid HTTPS (P-07.13, lower-ranked categories only). Gate by archetype.

**Tier 3 — advisory only, never high severity.**

12. Content scannability on very long unstructured pages (P-07.08), gated by archetype.
13. Internal-link orphaning / navigation depth (P-07.12 rationale, no effect size available).

**Do not emit at all:** aesthetic quality, "visual hierarchy", perceived trustworthiness of the
design, readability-grade verdicts, "page is too long" (P-07.14, P-07.16).

### B. Engagement problems that are REAL but NOT observable read-only

This is the honest core of the brief. Each of these is a genuine cause of visitors not staying,
and **none of them can be detected by our audit**. Attempting to detect them is how a
false-positive-penalised submission loses points.

| Not observable | Why |
| --- | --- |
| Bounce rate, exit rate, dwell time, scroll depth, session duration | Requires analytics access. P-07.14 additionally shows dwell has no universal threshold. |
| Conversion rate, funnel drop-off, cart abandonment | Requires analytics and business context. |
| Task success and time-on-task | Requires user testing with real intent. |
| Whether the content answers the visitor's actual question | Requires knowing the visitor's intent; we do not have queries. |
| Whether navigation labels match users' mental models | Information scent (P-07.12) is relative to a goal we cannot observe. |
| Real accessibility barriers for assistive-technology users | P-07.07: only ~50.4% of experienced problems map to WCAG at all, and automation covers a subset of that. |
| Field Core Web Vitals at the 75th percentile | Requires CrUX; our single synthetic run is not the same construct (P-07.01). |
| Scroll-triggered, timer-triggered or exit-intent modals | Not in the initial DOM; would need behavioural simulation we should not do. |
| Perceived credibility and aesthetic response | P-07.13, P-07.16 — subjective, contested, unmeasurable from markup. |
| Content quality, accuracy, and usefulness | No ground truth available read-only. |
| Whether slow performance is caused by our vantage point or the site | Single-location, single-network measurement. |
| Personalised/logged-in experience quality | Explicitly out of scope: no authenticated areas. |
| A/B-tested variants and feature flags | We see one arm and cannot know it is representative. |

**How to handle them honestly.** Three-way policy `(our inference)`:

- **Omit silently** anything for which we have neither a signal nor a useful caveat (e.g.
  conversion rate). Padding the report with "we cannot measure X" for everything is noise.
- **Emit as `severity: info` with a `not_determinable` marker** for the small set where the
  *absence of measurement is itself actionable for the site owner* — specifically: field CWV
  (recommend they check CrUX/Search Console), real accessibility barriers (recommend manual
  AT testing, citing that guidelines cover roughly half), and behavioural modals (recommend
  they self-audit scroll/timer popups). This makes our scope limits a feature, not a hole.
- **Never** convert an unmeasurable outcome into a measurable-sounding finding. No "high bounce
  risk" scores, no synthetic "engagement score", no predicted conversion impact.

### C. Assigning severity when almost all evidence is correlational

Only two entries in this file are genuinely causal *and* about engagement: P-07.02 (one A/B
test, one site, an 8.3 s baseline) and P-07.10 (a 2004 lab abandonment experiment). Everything
else is correlational, theoretical, or measures a non-engagement outcome. A severity scheme
that pretends otherwise will be wrong.

Proposed rule `(our inference)` — severity is a function of **confidence in the observation**,
not of predicted business impact, which we cannot estimate:

- **`high`** requires all three: (i) the defect is deterministic to detect from the DOM,
  (ii) it blocks or materially degrades access to content for some population, and (iii) it has
  a normative or measured basis (a WCAG success criterion, a Better Ads threshold, or a
  documented Google policy). Examples: content-blocking non-dismissible overlay; `user-scalable=no`;
  form inputs with no accessible label; main content absent without JS.
- **`medium`** — deterministic detection plus a mechanism-level link to engagement, but no
  normative threshold. Examples: images without intrinsic dimensions on a page with many of
  them; render-blocking scripts; ad density above the published threshold; missing `<main>` and
  primary nav on a commercial site.
- **`low`** — deterministic detection, weak or purely theoretical link. Examples: generic
  navigation labels; a long content page with no subheadings; missing publication date.
- **`info` / not determinable** — as in section B.

Two hard constraints on evidence text: every finding's `evidence` field must quote or point at
a **concrete artifact on the page** (selector, attribute, measured value, URL), and no
`suggested_action` may assert a quantitative outcome ("this will increase conversions by…").

### D. Popular engagement "best practices" we should NOT recommend

Each of these is common consulting advice with weak or absent support in what I verified:

1. **"Keep everything above the fold."** No source in this review supports a fold rule. The
   scanning literature (P-07.08) is explicitly hedged and describes variants.
2. **"Get your page under 3 seconds / 2 seconds."** The 3 s figure is vendor research from 2016
   (see untraceable table); the 2 s figure is a 2004 lab study on then-current connections
   (P-07.10). Recommend removing specific *causes* of slowness, not hitting a folk threshold.
3. **"Improve your visual design to build trust."** P-07.13 shows design look is *mentioned*
   most; it does not show redesign changes behaviour. P-07.16 shows the aesthetics→usability
   arrow has failed causal replication and may run backwards.
4. **"Write at a 7th–8th grade reading level."** Readability formulas have documented construct
   and criterion validity problems, disagree with one another by up to several grade levels on
   the same text, and are trivially gamed by punctuation changes. P-07.14 further shows text
   complexity changes what dwell time *means* rather than indicating a defect.
5. **"Shorten your pages — users don't read."** Directly contradicted by P-07.14's finding that
   the dwell needed to indicate satisfaction depends on page length and topic.
6. **"Remove all popups."** Over-broad. The measured evidence (P-07.09) and the policy
   (P-07.11) both target *promotional*, content-blocking, non-dismissible experiences, and both
   explicitly exempt legally mandated consent and age gates.
7. **"Add social proof / testimonials / trust badges."** No source in this review measures their
   effect. Not recommendable on this evidence base.
8. **"Chase a Lighthouse score of 100."** P-07.01 makes clear the thresholds are perception
   research plus a feasibility quota, measured in the field at p75. A lab score is a different
   construct, and no source links score-chasing to engagement.
9. **"Accessible sites convert better."** No traceable evidence. Recommend accessibility fixes
   on their own merits and on the normative basis, not on a revenue promise.

### E. Where this literature is thin or contested

- **The single weakest link in the whole chain** is between an observable page property and an
  actual engagement outcome on an *arbitrary* site. Every quantified engagement result I found
  is either a single-site vendor A/B test, an observational vendor study, or a lab experiment
  measuring perception rather than staying. There is no general, peer-reviewed, effect-size
  literature mapping crawlable page properties to bounce across a diverse site population.
- **CLS has no perception research behind it at all** — Google says so explicitly (P-07.01).
- **The aesthetic-usability effect is actively contested**, with reversed-direction replications.
- **The accessibility→engagement link is asserted far more often than measured.** P-07.07 is
  about barrier coverage, not about traffic.
- **Almost nothing in this domain is replicated by an independent party without a commercial
  interest in the answer.** Google authored or commissioned P-07.01, P-07.02, P-07.03 and
  P-07.11; the ad-density thresholds come from an industry consortium.

**Consequence for our submission `(our inference)`:** we should position the on-site half as
*detecting defects that are known to obstruct access and comprehension*, not as *predicting
engagement*. That framing is fully supported by what is above, survives scrutiny, and avoids
every false positive in section D.

---

## Provenance note

16 sources: 8 `VERIFIED` (P-07.01, .02, .03, .05, .06, .08, .09, .11) and 8 `SEARCH-ONLY`
(P-07.04, .07, .10, .12, .13, .14, .15, .16). The verified ones were fetched and read
directly; the search-only ones are so marked because
the publisher returned HTTP 403 or a paywall (Taylor & Francis, ACM DL, ScienceDirect,
APA PsycNet) — for those, citation details and headline results were corroborated across at
least two independent indexes, and any figure I could not corroborate is flagged in place
rather than asserted. No source in this file was written from memory.
