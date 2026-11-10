# 04 — Skill-by-skill Q&A

One section per skill in the marketplace. Frontmatter facts, inputs, outputs, tools,
failure modes.

---

## 1. `audit-orchestrator` — the entrypoint

### Q1. What is its job in one sentence?
**A.** Receive a URL or domain, run the full pipeline, and emit a single audit report.

### Q2. What tools does it declare?
**A.** `allowed-tools: ""` — none. It makes **no network requests**. It is a pure function
from analyser findings to a report.

### Q3. What are its inputs?
**A.** `target` (required — URL or bare domain) and `budget_s` (optional, default `300`,
passed straight to the collector).

### Q4. What are the seven procedure steps?
**A.**
1. **Collect** — invoke the collector once; inspect `bundle.budget.stages` immediately for
   abandoned stages.
2. **Analyse** — invoke the three analysers in parallel against the bundle; receive all 32
   envelopes.
3. **Cross-skill suppression** — none remains (D-025); kept empty in the numbering
   deliberately.
4. **Root-cause cluster dedup** — removed (D-016) as provably unreachable.
5. **Separate** findings / recommendations / limitations.
   **5b. Roll up** site-wide defects.
6. **Assemble** — sort, count, record archetype, conform to the schema.
7. **Meta-evaluate** — nine self-checks; emit warnings, never silent corrections.

### Q5. How are findings ordered?
**A.** Severity descending (`critical → high → medium → low`), then `check_id` ascending
lexicographically within each tier. This is what makes repeated runs comparable.

### Q6. What is "budget arbitration"?
**A.** Reading `bundle.budget.stages`, identifying which checks depended on any abandoned
stage, verifying those checks emitted `not_determinable` (overriding if not), and adding one
`limitations[]` entry per abandoned stage naming the affected checks — so
`not_determinable` reads as *"couldn't measure"*, not as a bug or a pass.

### Q7. What is its own false-positive surface?
**A.** Now small: Step 5b's site-wide rollup grouping findings that are not actually the same
defect, and Step 7's meta-evaluation producing a false warning. The O-1 suppression risk
belongs to `content-engagement-audit` now, not here.

### Q8. Which script implements it?
**A.** `scripts/compose_report.py` — `compose_report(site, audited_at, all_envelopes, bundle)
-> report`, implementing steps 3–6. `F-NNN` / `R-NNN` ID assignment is a deterministic
function of the sorted finding set.

---

## 2. `site-evidence-collector` — the only networked skill

### Q9. What tools does it declare?
**A.** `http_fetch headless_browser`. It is the **only** skill in the marketplace permitted
to make a network request. `headless_browser` is optional and is expected to be absent in
grading.

### Q10. What are its inputs?
**A.** `target` (required), `budget_s` (default 300), `max_static_pages` (default 20),
`max_rendered_pages` (default 3).

### Q11. What does it output?
**A.** One evidence bundle. **No findings, no severities, no recommendations** — this skill
observes and never judges.

### Q12. What are its eight procedure steps?
**A.**
1. Resolve the target — normalize to an origin, follow ≤3 redirects, record chain, TLS
   validity, final canonical host.
2. **Fetch and parse `robots.txt` before anything else**; classify every declared agent as
   `retrieval` / `training` / `hybrid` / `generic`. Every subsequent request obeys it.
3. Discover pages — sitemaps if declared, else breadth-first same-origin links from the
   homepage. Label `page_type` per URL and the site `archetype`.
4. Sample and fetch statically (≤20 pages), stratified across `page_type`. Extract main text
   with boilerplate removed, headings, landmarks, structured data, links, images, iframes,
   media, form controls, dates, contact signals, trigram hash.
5. Shared rendered-page pass (≤3 pages) **only if `headless_browser` exists**; one navigation
   per page, resize rather than re-navigate for the second viewport.
6. Internal links — HEAD, ≤20, skipping fragments, `mailto:`, and robots-disallowed paths.
7. Off-site identity anchors — HEAD, ≤8, one per host, only URLs the site itself declares.
8. Emit the bundle with per-stage timings.

### Q13. Why measure both 375 px and desktop viewports by resizing, not re-navigating?
**A.** One navigation per page is the budget rule. Re-navigating doubles the most expensive
operation in the pipeline for no additional evidence.

### Q14. What are its nine scripts and what do they do?
**A.** `robots_parser.py` (robots parsing + agent classification, RFC 9309 metacharacters),
`html_tree.py` + `extract_page.py` (the full `pages[]` extraction on a stdlib-only HTML
tree), `page_classifier.py` (`page_type` / `archetype` labelling), `sampling.py`
(deterministic seeded page selection), `render_geometry.py` (WCAG relative-luminance contrast
math, overlay / tap-target / ad-region classification from already-measured geometry),
`link_check.py` and `anchor_check.py` (the two link inventories, encoding the
401/403/429-is-not-broken rule structurally), `build_bundle.py` (final assembly).

### Q15. Do the scripts fetch?
**A.** **No.** They turn already-fetched raw content into bundle sections. Fetching is the
agent's `http_fetch` tool calls, driven by the procedure.

### Q16. What are its non-negotiable safety rules?
**A.** GET/HEAD only; never submit a form or click a control while rendering; never
authenticate, never carry cookies, never follow a login page or circumvent a paywall; obey
`robots.txt` including `crawl-delay`; ≤2 concurrent requests per host with a ≥250 ms gap;
**never evade bot detection** — no spoofing, no retrying around a 403, no identity rotation;
identify honestly with a descriptive User-Agent naming the audit and a contact URL; off-site
requests HEAD-only, ≤8, one per host, only to declared URLs.

### Q17. What eleven failure modes must it survive without crashing?
**A.** Robots-blocked root, JS-only SPA, single-page site, very large site, non-Latin script,
paywall, parked domain, cloaking/differential serving, bot-challenge pages, slow origin,
redirect loops. Each produces a **valid bundle** with the affected sections marked `partial`
or `unavailable` — never an exception, and never an inferred value.

### Q18. Why is "a blocked resource is evidence, not an obstacle" a design statement?
**A.** Because the alternative — retrying, spoofing, rotating identity — is exactly the
bright line the compliance posture stops at. A 403 is recorded and reported; it is not
something to get around.

---

## 3. `crawl-access-audit` — mechanism A

### Q19. What does it answer?
**A.** *Is the site's AI-crawler policy actually letting retrieval-time assistants in?* If
not, every other discoverability finding describes content nothing will reach.

### Q20. How many checks, and what does it read?
**A.** Two — `CHK-D-001` and `CHK-D-002`. It reads `robots.status`, `robots.agents[*]`, and
`robots.fetch_status`. **Nothing else.**

### Q21. What is its procedure?
**A.** (1) Gate on evidence — if `robots.status != "ok"`, both checks emit
`not_determinable`; **never infer permission from silence**. (2) Partition agents:
`retrieval` + `hybrid` in one set, `training` in the other. (3) Evaluate `CHK-D-001` — any
retrieval-set agent with `allowed_root: false` is `critical`. (4) Evaluate `CHK-D-002` *only
if D-001 did not fire* — `low`, informational. (5) Emit with `matched_line` quoted.

### Q22. Why does it have no `references/checks.md`?
**A.** Because two checks reading one bundle section do not need progressive disclosure — a
separate file would be **padding of exactly the kind the rubric penalises**. The part that
genuinely changes over time and is genuinely long (the agent classification table) lives in
`site-evidence-collector/references/ai-crawler-agents.md`, next to the code that applies it.

### Q23. What is its single largest false-positive risk?
**A.** Treating *"blocks an AI crawler"* as *"has a problem."* Many organisations block
training crawlers as considered policy. The retrieval/training split exists precisely so the
audit does not lecture them about a deliberate choice.

---

## 4. `content-engagement-audit` — mechanisms B, C, E, F

### Q24. Why does one skill cover four mechanisms?
**A.** It is the merger of two former skills — `render-extractability-audit` (B/C) and
`engagement-defect-audit` (E/F) — merged 2026-09-04 as **D-025**, after the ablation found
the one genuine cross-skill rule between them never changed an outcome on any of 36 real
sites. Keeping them separate bought nothing measurable.

### Q25. How many checks?
**A.** Seventeen: `CHK-D-003`, `D-004`, `D-005`, `D-009`, `D-010`, `D-011`, `D-013`, and
`CHK-E-014` through `E-022` plus `E-024`.

### Q26. What does it read, and what does it deliberately not read?
**A.** Reads `pages[]`, `rendered[]`, `links`. **Never `robots` or `anchors`.**

### Q27. Which of its checks never appear in `findings[]`?
**A.** Five, all `recommendation_only: true`: `CHK-D-010` and `CHK-E-021` (demoted D-022 —
fired too broadly), `CHK-D-011` and `CHK-D-013` (demoted D-027 — cited sources don't support
the claim), `CHK-E-024` (single-source rule, D-004).

### Q28. What is its check-order dependency chain?
**A.** `CHK-D-004` reads `CHK-D-003`'s result; `CHK-D-010` reads `CHK-D-004`'s;
`CHK-E-019`'s fate is decided **last**, against `CHK-D-003`'s (rule O-1).

### Q29. Why do `CHK-D-003` and `CHK-E-019` duplicate the same computation?
**A.** **The duplication is deliberate**, kept from before the merge: the two checks were
authored to measure the same mechanism from two angles — extractability vs engagement —
without reading each other's output. Step 10 reconciles them once, after both have run,
rather than one being rewritten to depend on the other's internals.

### Q30. What are its four named false-positive risks?
**A.**
1. Treating "different from how a human reads it" as a defect — hence every content check is
   conditioned on page type or archetype.
2. `CHK-E-014` flagging `alt=""` as missing alt text — empty alt on decorative images is
   correct; test `alt === null`.
3. `CHK-E-018` flagging cookie banners and age gates — legal compliance, not a defect.
4. `CHK-E-019` firing without checking the `<noscript>` fallback.

### Q31. Which check used to live here and was cut?
**A.** `CHK-E-023` (mobile ad density), cut 2026-09-04 as **D-018**. It read only
`rendered[].viewports.mobile_375.ad_area_pct_total`; with no headless browser its loop body
never executed, so it emitted nothing at all — not even a `not_determinable` envelope. It was
also already the ledger's most false-positive-prone row.

### Q32. Why keep `CHK-E-016` and `CHK-E-018` if they're equally render-dead?
**A.** Because they are dead *because a tool is absent*, not because the check is weak — and
`degraded_stages[].affected_checks` names them in every report, so the reader is told they
were not measured.

---

## 5. `entity-identity-audit` — mechanism D

### Q33. What does it answer?
**A.** Does the site state who it is unambiguously, mark it up machine-readably, stay
internally consistent, and anchor itself to external profiles?

### Q34. How many checks, and what does it read?
**A.** Thirteen: `CHK-D-006`, `D-007`, `D-008`, `D-012`, `D-025`, `D-026`, `D-027`, and the
vertical-schema family `D-029`–`D-034`. It reads `pages[]` and `anchors` — **nothing else**.
It is the only analyser that reads `anchors`, the sole off-site evidence in the bundle.

### Q35. How does it classify a page as time-sensitive?
**A.** The bundle carries no temporal-sensitivity label, so the skill derives one. A page is
time-sensitive if **any two** hold: (a) `page_type ∈ {article, documentation, faq}` *and*
the URL contains a year pattern; (b) `dates.meta_published` or `dates.visible_dates` is
non-empty; (c) the first 200 words contain ≥3 past-tense verbs or temporal adverbs. Otherwise
evergreen. **`CHK-D-012` must never fire on an evergreen page**, and when classification is
ambiguous it biases toward evergreen (stay silent).

### Q36. What is the vertical-schema family?
**A.** Six mutually archetype-gated checks — only the one matching the site's archetype
evaluates; the other five emit `not_applicable`. All six are **recommendation-only**; schema
absence never creates a scored finding.

| Check | Archetype | Passing evidence |
| --- | --- | --- |
| D-029 | `ecommerce` | Complete Product/Offer JSON-LD on product pages |
| D-030 | `saas_marketing` | SoftwareApplication or priced Offer on home/pricing |
| D-031 | `marketplace` | Complete Event / ItemList / JobPosting on a listing page |
| D-032 | `news_editorial` | NewsArticle headline + datePublished + author.name, plus RSS/Atom head link |
| D-033 | `personal` family | Named Person data, RSS/Atom link, consistent article authorship |
| D-034 | `reference` / `institutional` | SoftwareSourceCode or DataCatalog when a code/data archive is detected |

### Q37. What are its two declared limitations?
**A.** **LIM-01** — actual cross-web corroboration requires a search or web-scale index API;
no free, deterministic, rate-safe source exists. **LIM-02** — name-collision detection
requires a corpus of other entities. `CHK-D-025/026/027` audit only *the anchoring the site
itself provides*; they do not measure whether corroboration has occurred.

### Q38. What are its three highest false-positive risks?
**A.**
1. `CHK-D-012` firing on evergreen pages — the whole time-sensitivity classifier exists to
   prevent this.
2. `CHK-D-026` treating bot-blocks as broken anchors — 401/403/429 encode as `resolved: null`,
   distinct from `false`.
3. `CHK-D-027` flagging legitimate name variants — "Example Ltd" vs "Example Limited" is not
   a conflict. Suppress unless name roots diverge after stripping punctuation, case, and
   common legal-entity suffixes (Ltd / Limited / LLC / Inc / Corp / GmbH). **Implemented, not
   just described.**
