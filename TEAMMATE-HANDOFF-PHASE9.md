# Phase 9 Handoff — Brand AI-Readiness Audit Marketplace

**Where this stops**: Phase 8 (judge-driven fixes) is fully committed on `main`. Items 0–8 of the Phase-8 patch list all landed in commits `5ff0dfd` and `2ce5c0c`. Left for you: **audit more websites, do the AI-judge pass on them, write D-035 in `docs/DECISIONS.md`, and push.**

---

## 1. What this project actually is

We're building the Adobe University Hackathon 2026 Round 3 submission — a marketplace of `agentskills.io` skills that audit a website for **brand AI-readiness** (how well AI assistants like ChatGPT / Claude / Perplexity can find, cite, and answer questions about the brand). The submission is 5 skills, 26 checks:

| Skill | Role | Owned checks |
|---|---|---|
| `audit-orchestrator` | entrypoint; runs the other four and composes the report | rollup, meta-eval, strengths, degraded-stages honesty |
| `site-evidence-collector` | fetches robots/sitemap, samples pages, extracts main content, classifies archetype | bundle producer (no checks) |
| `crawl-access-audit` | robots.txt / crawler agent analysis | CHK-D-001, D-002 |
| `content-engagement-audit` | thin content, duplicates, freshness, layout | CHK-D-003, D-004, D-005, D-009, D-010, D-013 + E-014, E-015 (a11y, headings) |
| `entity-identity-audit` | who is this brand? sameAs / Organization JSON-LD / identity signals | CHK-D-006, D-007, D-008, D-012, D-025-27 |

Output is a JSON report per site with `findings[]`, `recommendations[]`, `strengths[]`, `preamble`, `degraded_stages`, `checks_passed`, `summary`, `meta_evaluation`.

---

## 2. How we audit a website (the pipeline)

```
run_audit.py --site <domain>            harness/run_audit.py drives it
    ↓
site-evidence-collector
    ├─ robots.txt parse (crawl-access classifier)
    ├─ sitemap fetch + URL inventory
    ├─ sampling.is_page_url()           excludes auth/legal/assets/download/listing URLs
    ├─ up to ~13 page fetches (offline cache when snapshot exists)
    ├─ extract_page.py                  main-content selector fallback chain:
    │                                   <main> → role="main" → dominant <article> → body → best container
    │                                   emits js_render_suspected / js_payload_heavy / main_content_source
    ├─ page_classifier.py               archetype (ecommerce/saas/news/documentation/local_business/personal/brochure/unknown)
    └─ produces <site>.bundle.json      (~50 KB per site)
    ↓
content-engagement-audit  +  entity-identity-audit  +  crawl-access-audit
    ├─ 26 checks run against the bundle
    ├─ each check returns {check_id, state, evidence, severity, evidence_strength,
    │                       suggested_action, locus, recommendation_only?}
    ├─ archetype guards: D-006/D-007/D-010 return not_applicable on unknown/brochure
    └─ _content_unmeasurable() routes to not_determinable on JS shells (extraction_ok=False
      or js_render_suspected)
    ↓
audit-orchestrator/compose_report.py
    ├─ severity floor and per-subcheck rollup (E-014's per-element enumeration
    │  collapses to one bucket per (check_id, subcheck), severity from evidence volume)
    ├─ meta_evaluation gates: no_duplicate_findings, prohibited_recommendation,
    │  known_check_id, evidence-action coherence
    ├─ strengths[] computed from positive signals (robots ok, sitemap fresh, RSS
    │  discovery link, Organization JSON-LD, canonical consistent, ...)
    ├─ degraded_stages → preamble.access_blocked_for + limitations
    └─ writes <site>.report.json
```

Two invariants worth internalizing:
- **Offline-first for the corpus** — snapshots live in `harness/snapshots/`, replays are hermetic and free. The harness / snapshots dir is gitignored; only the source skills ship in the submission.
- **Nothing writes to disk from inside a skill**. All I/O is by the harness or the collector. Skills are pure functions of the bundle.

---

## 3. How we evaluate the audit (the AI-judge study)

This is what caught most of Phase 8's bugs. The workflow:

1. Pick a corpus of sites (**see §5 for the current list — start there for reproducibility**).
2. Run `python harness/run_audit.py --set dev --offline`. This writes `harness/out/dev/<site>.report.json` + `.bundle.json`.
3. **Feed each report + the site's raw HTML (or a fresh live snapshot) to two independent AI judges** — we used Claude Opus and Gemini 2.5 Pro. For each finding the judge scores:
   - **TP** — real, actionable, evidence checks out on the live site
   - **FP** — hallucinated (evidence doesn't hold up, or the site doesn't actually have the defect)
   - **wrong severity** — right defect, wrong urgency
   - **prohibited recommendation** — imperative fix language ("Add `<h1>`", "Wrap in `<main>`") that violates OFFICIALS-QA §3.4
   - **overlooked** — a real defect the audit missed that a human would catch on that page
4. Take the union of both judges' findings, log each into a scratch file (`judge-findings-log.md`) with columns *site / finding / judge / verdict / evidence quote / suggested fix*.
5. Cluster by root cause. In Phase 8 the 25-site study collapsed to 8 root-cause bug classes:

| Bug class | Symptom | Fix |
|---|---|---|
| Extractor selector too narrow | Only used `<main>`, so kernel.org (nested `<aside><article>`), brianlovin (React blog), notion (SPA shell) all produced "thin content" hallucinations | Selector fallback chain + `js_render_suspected` / `js_payload_heavy` flags |
| Same → D-004 / D-005 / D-010 firing on script shells | 100% trigram overlap flagged on identical-looking JS pages that had different data payloads underneath | `_content_unmeasurable()` → `not_determinable` |
| Sampler picking utility URLs | `/legal`, `/terms`, `/download/*.zip`, `/dp/<asin>`, `/en/` locale roots all showed up as "content pages" and dominated the sample | `sampling.is_page_url()` excludes auth/legal/utility/listing patterns; same-locale preference |
| Not honest about blocked sites | Sites that returned 403 on robots got 0 findings and no explanation | `preamble.access_blocked_for` + `degraded_stages` limitation |
| Archetype-blind checks | D-006 "no explicit entity definition" fired on personal blogs (jvns, sive.rs, danluu) | `unknown` / `brochure` / `personal` archetypes → `not_applicable` |
| D-006 too strict on real orgs | Missed identity that lived in h1 + first `<p>`, meta description, JSON-LD instead of one big paragraph | Widened detection to score signals across all four surfaces |
| E-014 evidence enumeration | Same accessibility violation reported as 30 findings (one per element) | Rollup by `(check_id, subcheck)`, severity from evidence volume floor |
| No positive signals | Reports only listed defects — no way to see what the site did right | `strengths[]` block with structured `{id, detector, evidence}` |

**Every one of these came from an AI judge disagreeing with the audit and being right.** The pattern is: judge flags a specific finding as FP or missing → we trace back through `compose_report → checks → bundle → extractor` → find the layer where reality left the pipeline → fix that layer.

---

## 4. Latest audit results (after Phase 8, on 2026-09-13)

Full offline replay of the 24-site dev corpus. Numbers are what the fixed pipeline currently produces:

| Site | Archetype (declared) | Findings | Severity mix (C/H/M/L) | Recs | Strengths |
|---|---|---:|---|---:|---:|
| bookshop.org | ecommerce | 1 | 0/0/0/1 | 0 | 1 |
| www.adafruit.com | ecommerce | 4 | 0/1/2/1 | 9 | 1 |
| shop.fsf.org | ecommerce | 0 | 0/0/0/0 | 0 | 0 |
| www.thalia.de | ecommerce | 1 | 0/0/1/0 | 0 | 0 |
| docs.python.org | documentation | 3 | 0/0/3/0 | 5 | 0 |
| docs.djangoproject.com | documentation | 1 | 0/0/1/0 | 3 | 0 |
| gohugo.io | documentation | 3 | 0/1/2/0 | 12 | 1 |
| vitejs.dev | documentation | 5 | 0/0/5/0 | 3 | 2 |
| plausible.io | saas_marketing | 2 | 0/1/1/0 | 3 | 2 |
| tailscale.com | saas_marketing | 1 | 0/0/1/0 | 0 | 0 |
| qonto.com | saas_marketing | 3 | 0/1/2/0 | 3 | 1 |
| www.fastmail.com | saas_marketing | 2 | 0/0/2/0 | 3 | 1 |
| www.smashingmagazine.com | news_editorial | 2 | 0/0/2/0 | 1 | 1 |
| lwn.net | news_editorial | 4 | 0/0/3/1 | 15 | 1 |
| www.heise.de | news_editorial | 6 | 1/2/3/0 | 5 | 1 |
| www.asahi.com | news_editorial | 4 | 1/1/2/0 | 6 | 2 |
| www.tartinebakery.com | local_business | 0 | 0/0/0/0 | 0 | 0 |
| franklinbbq.com | local_business | 4 | 0/1/3/0 | 4 | 0 |
| www.pizzeriabianco.com | local_business | 4 | 0/1/2/1 | 2 | 1 |
| www.sacher.com | local_business | 4 | 0/0/4/0 | 2 | 1 |
| jvns.ca | brochure | 5 | 0/0/4/1 | 2 | 2 |
| danluu.com | brochure | 2 | 0/2/0/0 | 11 | 0 |
| overreacted.io | brochure | 1 | 0/1/0/0 | 9 | 1 |
| sive.rs | brochure | 0 | 0/0/0/0 | 2 | 2 |

**Totals**: 65 findings across 24 sites, 100 recommendations, 23 strengths. Zero crashes. Compare with any of the reports at `harness/out/dev/<site>.report.json` for the full evidence.

The 15-site **negative corpus** (`harness/corpus/negative.csv`) is the "clean" set — sites known to be well-configured for AI retrieval. It's the guardrail against false positives: an audit that fires many findings on `www.mozilla.org` or `www.gov.uk` is misbehaving.

---

## 5. Old websites already audited (start here for repro)

**Dev corpus — 24 sites, balanced across archetypes (`harness/corpus/dev.csv`):**

```
Ecommerce           bookshop.org, www.adafruit.com, shop.fsf.org, www.thalia.de
Documentation       docs.python.org, docs.djangoproject.com, gohugo.io, vitejs.dev
SaaS marketing      plausible.io, tailscale.com, qonto.com, www.fastmail.com
News/editorial      www.smashingmagazine.com, lwn.net, www.heise.de, www.asahi.com
Local business      www.tartinebakery.com, franklinbbq.com, www.pizzeriabianco.com, www.sacher.com
Brochure/personal   jvns.ca, danluu.com, overreacted.io, sive.rs
```

**Negative corpus — 15 known-clean sites (`harness/corpus/negative.csv`):**

```
Crawl access        www.python.org, developer.mozilla.org
Render extract.     docs.python.org, gohugo.io
Entity identity     www.mozilla.org, creativecommons.org
Accessibility       www.w3.org, www.gov.uk
Mobile layout       web.dev, www.11ty.dev
Freshness/trust     www.nngroup.com, blog.cloudflare.com
Offsite identity    stripe.com, about.gitlab.com, www.docker.com
```

**Extra sites the Phase 8 judge study also hit** (not in the corpus files but with snapshots on disk under `harness/snapshots/`): `kernel.org`, `brianlovin.com`, `notion.com`, `unstop.com`, `linkedin.com`, `amazon.in`, `devpost.com`, `ghost.org`, `fasterthanli.me`, `www.rei.com`, `theverge.com`, `mdn.io`, `www.arxiv.org`, and a handful more (see `harness/out/phase8-step*` directories).

---

## 6. What we need you to do

### 6a. Pick more websites to audit — this is the main ask

Diverse coverage is what surfaces the next bug class. **Please add 15–25 new sites** across at least these dimensions we're currently thin on:

- **Regional / non-English**: Latin America (`.mx`, `.br`, `.ar`), Southeast Asia (Indonesia, Vietnam, Thailand), Middle East (`.ae`, RTL Arabic), Nordics — check the audit handles UTF-8 titles, non-Latin robots.txt paths, RTL text extraction
- **Financial services** — banks, brokerages (bot-blocked, heavy WAF)
- **Government / .gov / .edu** — expected to be well-configured; good negative-corpus candidates
- **Marketplaces** — Etsy, Discogs, Bandcamp, itch.io (long-tail listing pages that our new `is_page_url()` exclusion should be filtering out — please verify it does)
- **Very small / brochure sites** — the "unknown" archetype path is our weakest; more `.itch.io` game pages, single-page portfolios, `linktree`-style landing pages
- **Enterprise SaaS with logged-out marketing sites** — Salesforce, ServiceNow, Databricks (heavy JS, should trip `js_render_suspected`)
- **Blogs on unusual stacks** — Substack, Ghost hosted, Medium (each has its own DOM quirks that broke us before)

For each site you pick:

```bash
# 1. Add to a new corpus file so we don't pollute the pinned ones
echo "example.com,ecommerce,mid,en," >> harness/corpus/handoff.csv

# 2. Snapshot it (needs network — pin the snapshot immediately so replays are hermetic)
python harness/run_audit.py --site example.com --set handoff

# 3. Inspect the report
cat harness/out/handoff/example.com.report.json | python -m json.tool
```

Aim for **≥ 3 sites per archetype family** so archetype-specific bugs have somewhere to show up.

### 6b. Run the AI-judge pass on those new reports

For each new site:
1. Open the report and the live site in two tabs.
2. Ask Claude and Gemini (or ChatGPT) — separately, each with its own fresh context — this exact prompt:

   > *You are auditing this brand AI-readiness report against the live site. For each finding, verdict: TP (real and actionable), FP (evidence does not hold up on the live site), WRONG-SEVERITY (right defect wrong urgency), PROHIBITED-REC (uses imperative fix language like "Add" / "Wrap" / "Replace" instead of describing what's missing), or OVERLOOKED (a real defect on this page the audit missed). Quote the exact HTML / URL / heading you used to justify each verdict.*

3. Log every disagreement in a new file: `docs/evals/judge-findings-phase9.md`. Use the same columns as `docs/evals/adjudication-queue.md` if you want a template.
4. Cluster disagreements by root cause the way §3 describes. If ≥ 2 sites show the same root-cause pattern, it's a real bug worth fixing.

---

## 7. What's left in Phase 8 (blocks submission)

These are the two remaining items from the original patch list. Both are small.

**Item 9 — Write D-035 in `docs/DECISIONS.md`**. This is the decision-log entry that closes Phase 8. It should say, briefly:
- What was decided: the 8 patches (items 0–7) plus the item-8 calibration
- Why: the dual-AI-judge study — link to `docs/evals/adjudication-queue.md` and the 8 bug classes in §3 of this file
- Evidence: findings-delta on the corpus (baseline vs after Phase 8 — the Phase 8 baseline reports are preserved under `harness/out/phase8-step*`)
- What was **not** done and why: no WAF pattern-matching (OFFICIALS-QA §2.2 + Action #10 forbids it), `page_classifier.py` was left alone (that's D-034's territory), D-013 wording wasn't opened up beyond the `not_determinable` routing
- Follow-ups: whatever your Phase-9 judge pass surfaces

Follow the format of D-033 / D-034 already in `docs/DECISIONS.md`.

**Item 10 — Push to `origin/main`** after D-035 lands. Nothing fancy: `git push origin main`.

---

## 8. Guardrails (please keep)

- **Never `--no-verify` or `--force`.** If a hook fails, fix the underlying issue.
- **Do NOT touch `page_classifier.py`** — that's the archetype classifier v2 workstream (D-034).
- **Do NOT commit anything under `harness/`** — it's gitignored on purpose.
- **Do NOT re-introduce WAF pattern-matching** beyond using the existing `degraded_stages` signal. OFFICIALS-QA is clear that guessing whether a WAF is present is out of scope.
- **Ask before commit / push.** Edits are fine without asking; anything that touches remote history isn't.
- **Attribution**: end commits with `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` when Claude helped.

---

## 9. Quick-reference commands

```bash
# Replay the current corpus (hermetic, offline)
python harness/run_audit.py --set dev --offline
python harness/run_audit.py --set negative --offline

# Audit one site live (needs network; also refreshes its snapshot)
python harness/run_audit.py --site example.com

# Look at a report
cat harness/out/dev/gohugo.io.report.json | python -m json.tool | less

# See the corpus lists
cat harness/corpus/dev.csv
cat harness/corpus/negative.csv

# Score against gold labels (Stage E precision/recall/FP by check_id)
python harness/score_dev.py
```

Ping me on WORKLOG.md if anything here is unclear.
