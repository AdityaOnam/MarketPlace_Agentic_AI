# brand-ai-readiness-audit

A read-only Agent Skill Marketplace that audits any website for two failure classes:

1. **Off-site discoverability** — why AI assistants fail to find, fetch, read, or
   correctly cite a brand.
2. **On-site engagement** — why visitors who do arrive don't stay, or can't.

Given a URL or domain, it produces one structured JSON report: findings with evidence and
severity, prioritized suggested actions, proactive recommendations that go beyond detected
defects, and an explicit statement of what the audit could not measure. It never modifies
the site it audits — every check is observational.

---

## Running the audit

**Entrypoint:** `audit-orchestrator` (marked `"entrypoint": true` in `marketplace.json`).
Invoke it with a `target` (URL or bare domain) and an optional `budget_s` (default 300).
Never invoke the other four skills directly for a live audit — the orchestrator does that.

**Tools the agent needs:** only `http_fetch` (GET/HEAD), and only inside
`site-evidence-collector`. The other four skills declare `allowed-tools: []`. A
`headless_browser` tool is declared as optional; when it is absent (the expected case), the
collector marks the render pass `abandoned` at zero elapsed time and the report lists the
affected sub-checks in `degraded_stages[]` rather than guessing.

**The procedure** is in [`skills/audit-orchestrator/SKILL.md`](skills/audit-orchestrator/SKILL.md)
→ *Procedure*, steps 1–7. In one line: collect once → run three analysers → separate
findings from recommendations → roll up site-wide defects → assemble → self-check → emit.

**Progressive disclosure — what to load when:**

| Load | When |
| --- | --- |
| `skills/audit-orchestrator/SKILL.md` | always; it drives the run |
| `skills/site-evidence-collector/SKILL.md` + `references/procedure.md` | step 1 (collection) |
| `skills/site-evidence-collector/references/bundle-schema.md` | if a field in the bundle is unclear |
| `skills/<analyser>/SKILL.md` | step 2, one per analyser |
| `skills/<analyser>/references/checks.md` | only when a check's exact rule or threshold is needed |
| `skills/audit-orchestrator/references/report-schema.md` | step 6 (assembly) |

**Executable checks.** Every check is a pure function. Each analyser's
`scripts/*_checks.py` exposes `evaluate(bundle: dict) -> list[dict]` returning one
envelope per check outcome (`present` / `absent` / `not_determinable` / `not_applicable`).
`skills/audit-orchestrator/scripts/compose_report.py` implements steps 3–6 as
`compose_report(site, audited_at, all_envelopes, bundle) -> report`. The collector's
`scripts/` turn already-fetched raw content into bundle sections; they never fetch anything
themselves. All Python is stdlib-only — nothing to install.

---

## Skills

Five skills, split by mechanism, with network access isolated in exactly one of them.

| Skill | Role | Checks |
| --- | --- | --- |
| **`audit-orchestrator`** *(entrypoint)* | Invokes the collector once, runs the three analysers against the resulting bundle, assembles and self-checks the final report | none of its own |
| `site-evidence-collector` | The only skill that touches the network. Fetches robots.txt, a deterministically sampled page inventory, and bounded internal-link and off-site identity-anchor reachability checks — emits one in-memory evidence bundle, no findings | none — observes only |
| `crawl-access-audit` | Is the site's AI-crawler policy actually letting retrieval-time assistants in? Distinguishes retrieval-time agents (GPTBot, ChatGPT-User, PerplexityBot, Claude-*, OAI-SearchBot…) from training-corpus agents (Google-Extended, CCBot, ClaudeBot, Bytespider…); blocking the first is `critical`, blocking only the second is `low` | CHK-D-001, D-002 |
| `content-engagement-audit` | Is the content complete, substantial, well-structured and non-duplicated in what a non-rendering fetch actually receives — **and** are there statically detectable defects (WCAG lang/alt/label failures, zoom-blocking viewport meta, non-descriptive anchor text, autoplay media, missing landmarks, undimensioned images) that obstruct a visitor who already arrived? | CHK-D-003, D-004, D-005, D-009, D-010, D-011, D-013, CHK-E-014 – E-022, E-024 |
| `entity-identity-audit` | Does the site state who it is unambiguously, mark it up machine-readably, stay internally consistent, and anchor itself to external profiles? | CHK-D-006, D-007, D-008, D-012, D-025, D-026, D-027 |

26 checks, disjoint — no check is owned by more than one skill. Why five and not one, why
not more, and the three tests that would falsify the split: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

**What runs without a browser.** Everything above except four sub-checks: contrast ratio
(part of CHK-E-014), 375 px overflow (part of CHK-E-015), tap-target size (CHK-E-016) and
load-time overlay coverage (CHK-E-018). Those need rendered geometry; with no
`headless_browser` they are reported as `not_determinable` and named in
`degraded_stages[]`. Two checks that used to depend on the render pass — JS-only content
(CHK-D-003) and blank first paint (CHK-E-019) — re-derive a one-sided static signal (no
`<h1>` and < 50 words; `<noscript>` plus static volume) capped one severity tier below
their two-sided result.

---

## How the entrypoint composes them

1. **Collect** — run `site-evidence-collector` once; every other skill reads that bundle
   read-only and never fetches anything itself.
2. **Analyse** — run the three analysers against the bundle. They are blind to each other
   by construction; no analyser reads another's output.
3. **Reconcile** — nothing remains at this step. The one cross-skill dependency the design
   started with was tested against real sites and removed (see *Design history*).
4. **Roll up** — a defect found on ≥ 3 sampled pages becomes one site-wide finding rather
   than N per-page findings.
5. **Assemble** — separate confirmed defects (`findings[]`) from proactive suggestions
   (`recommendations[]`) and from what the audit is structurally unable to measure
   (`limitations[]`), ordered by severity so repeated runs are comparable.
6. **Meta-evaluate** — seven coherence checks over the finished report: severity counts
   reconcile, every finding carries evidence and an action, no duplicate check per locus,
   every check ID is known, no prohibited recommendation reached the wording, limitations
   present. Warnings are emitted in `meta_evaluation`, **never silently corrected** — a
   report that edits itself until its own audit passes is the failure mode this project is
   most careful about.

---

## What a finding looks like

A real finding from the evaluation corpus (a German news site), unedited:

```json
{
  "id": "F-001",
  "check_id": "CHK-D-001",
  "title": "Retrieval-time AI crawler blocked at root",
  "severity": "critical",
  "evidence_strength": "HARD-MECHANICAL",
  "state": "present",
  "locus": { "url": null, "selector": null },
  "evidence": "robots.txt line 120: Disallow: / applies to Applebot (retrieval-time AI crawler). robots.txt line 180: Disallow: / applies to ChatGPT-User (retrieval-time AI crawler). robots.txt line 494: Disallow: / applies to OAI-SearchBot (retrieval-time AI crawler). robots.txt line 520: Disallow: / applies to PerplexityBot (retrieval-time AI crawler). ...",
  "suggested_action": {
    "summary": "Narrow the Disallow rule to the paths that actually need protection rather than the site root for: Applebot, ChatGPT-User, Claude-SearchBot, Claude-User, Claude-Web, Meta-ExternalFetcher, OAI-SearchBot, Perplexity-User, PerplexityBot.",
    "priority": "critical"
  },
  "suppressed_by": []
}
```

Beyond the required fields (`id`, `title`, `severity`, `evidence`, `suggested_action`),
every finding carries the `check_id` it came from, the `evidence_strength` grade that
capped its severity, and a `locus` (page URL and CSS selector where applicable) so the
fix can be located. Proactive items live in a sibling array:

```json
{
  "id": "R-001",
  "check_id": "CHK-E-021",
  "title": "Images/iframes missing dimensions (layout-shift cause)",
  "rationale": "714 image(s)/iframe(s) lack explicit width/height or aspect-ratio, so content reflows during load.",
  "suggested_action": { "summary": "Add width/height attributes or CSS aspect-ratio to reserve layout space before the resource loads. (Proactive — not a confirmed defect.)", "priority": "low" }
}
```

and every report ends with five declared limitations (`LIM-01` … `LIM-05`) and a
`degraded_stages[]` list, so what was *not* measured is as visible as what was.

---

## How it was evaluated

The marketplace was measured, not just designed. Full record in
[`docs/evals/stage-e-report.md`](docs/evals/stage-e-report.md) and
[`docs/EVALS.md`](docs/EVALS.md); every number below carries how it was obtained.

- **Gold labels:** 624 cells — 24 dev sites (6 archetypes × 4, four of them non-English)
  × 26 checks — hand-labelled by a human from frozen snapshots, *before* seeing tool
  output, using a closed `PRESENT / ABSENT / UNMEASURABLE / N/A` taxonomy. A model never
  authors a label; it may only queue a disagreement for human adjudication.
- **Negative controls:** 15 clean sites, 2–3 per dimension, chosen by fetching and reading
  their markup rather than by reputation, to measure clean-site false-positive rate — the
  number most likely to sink a submission graded on "few false positives".
- **Adversarial set:** 6 sites (bot-blocked, unfetchable, malformed) scored only on graceful
  degradation. One of them exposed a false-positive mechanism affecting 10 checks (an
  unfetchable page read at face value) that was fixed before any gold label was written.
- **Result (2026-09-10):** of the 15 checks with a defined precision at n ≥ 10 sites, 11 are
  ≥ 0.90 and 8 are 1.00. Clean-site FP rate is 0.00 on 14 of the 21 checks that have one.
  Four checks trip the FP cut (> 0.15) and are documented with their cause — one is a
  measured base-rate effect deliberately left in, two point at gold-data rows queued for
  human adjudication, one is an open question against the code — rather than tuned away.
  **No check was adjusted to make a number look
  better**; three checks were fixed because the disagreement turned out to be a real bug
  (a robots.txt parser lacking RFC 9309 `$` support was reporting a site as *blocking*
  crawlers it explicitly *allowed*, on a `critical`-severity check).
- **Composition was tested, not asserted.** A leave-one-skill-out ablation and a merge test
  ran against 36 real sites. The orchestrator's one cross-skill suppression rule never
  fired, so two skills were merged into one on that evidence (six → five). Set stability at
  k = 3 on five live sites: identical `(check_id, locus)` set all three runs.
- **What has not been measured yet, stated plainly:** intra-rater test–retest
  (Krippendorff's α per check, scheduled ≥ 48 h after the first labelling pass); recall
  carries a wide interval (~±12 pp) and is the weakest number reported.

---

## Recommendations are vertical-specific

Every suggested action is scoped to the site's vertical, and the report states which one it
assumed (`preamble.archetype`). The archetype decides which checks run at all — a personal
or portfolio site is exempt from identity-anchor and Organization-markup checks, a
non-commercial site from trust signals — and how each surviving action is worded: "add a
canonical tag" means something different on a faceted 10,000-SKU catalogue than on a
six-page brochure site. Where no archetype rule matches, the report says `unknown` and
suppresses every archetype-conditioned check rather than guessing. The classifier is
deliberately conservative and abstains often; that is a known limitation, not a hidden one.

**What makes these more than an issue → fix lookup:** each action's urgency is capped at the
strength of the evidence behind it (a WCAG violation is a standards violation, never a
conversion claim); wording is conditioned on vertical and page type; and the fashionable
advice a checklist would confidently emit — `llms.txt` as a substantive fix, citation
guarantees, above-the-fold rules — is refused, with that refusal enforced mechanically in
the meta-evaluation step and stated visibly in `limitations[]`.

---

## Guardrails

- **Recommend-only.** No skill ever mutates a live site; every check is a read against
  already-collected evidence.
- **`robots.txt` is obeyed**, including `crawl-delay`, by the one skill that fetches.
- **No authenticated areas, no bot-detection evasion, no rate abuse** — 2 concurrent
  requests per host, HEAD-only for internal-link and off-site anchor checks.
- **< 5 minute runtime**, enforced by a hard per-stage time budget with graceful
  degradation: a stage that runs out of time is abandoned and reported as
  `not_determinable`, never guessed from partial evidence. A slow site produces a partial
  report on time, never a complete report late; `budget.stages[].actual_s` records where
  the time went.
- **No persistent storage.** The evidence bundle is built in memory, passed to the
  analysers within the run, and discarded. Nothing is cached; no run influences another.
- **Severity is capped by evidence strength.** Causal or hard-mechanical evidence may reach
  `critical`; normative (WCAG, Better Ads) caps at `high`; correlational at `high`;
  theoretical at `medium`; single-study or contested support ships only as a
  recommendation, never a scored finding.
- **A fixed list of recommendations this marketplace will never make** — hidden or
  retriever-directed text, bulk generated content, `llms.txt` as a substantive fix, any
  promise of citation outcomes, "improve visual design to build trust", reading-grade
  targets, blanket popup removal, Lighthouse-100 chasing, "accessible sites convert
  better". Each has a documented reason in [`docs/DECISIONS.md`](docs/DECISIONS.md) (D-007).

---

## What this audit does not, and cannot, measure

Stated in every report's `limitations[]`, not omitted silently:

- Whether the wider web agrees with the brand's own claims (needs a search or web-scale
  index API).
- Whether the brand name collides with an unrelated same-named entity elsewhere.
- Whether any AI assistant currently cites the brand — this marketplace never queries a
  live generative engine; doing so would break reproducibility and the runtime budget at
  once.
- Field engagement outcomes — bounce, dwell time, scroll depth, conversion — none of which
  are observable read-only. The engagement half detects known-obstructive defects; it does
  not predict how any visitor will behave.
- `llms.txt` adoption — deliberately not recommended: a 137k-domain measurement found 97 %
  of existing files were never requested.

Also deliberately absent, because the evidence base does not support them as findings:
meta-description tags (no measured effect on AI retrieval), sitemap presence on its own,
AI-text detection, hidden-text detection, cloaking detection, and field Core Web Vitals
verdicts. The full list with reasons is in [`docs/research/EVIDENCE-LEDGER.md`](docs/research/EVIDENCE-LEDGER.md).

---

## A note on determinism

Same input against the same site state yields the same report — same findings, same
ordering, same IDs. This is a design goal in service of reproducibility, not a claim that
a live website is a fixed object. Where content or origin behaviour changes between runs,
the report says so — `degraded_stages`, `not_determinable`, per-stage timings — rather than
presenting one run's luck as a settled result.

---

## Design history

- Started as **six** skills (2026-09-02). A leave-one-skill-out ablation against 36 real
  sites found the one cross-skill suppression rule between `render-extractability-audit`
  and `engagement-defect-audit` never fired; they merged into `content-engagement-audit`
  with byte-identical output across all 42 available sites (D-025).
- An earlier orchestrator step collapsed a four-check "JS-only" cluster into one finding.
  A suppression-necessity test proved the pattern can never occur — two of the four checks
  require contradictory word counts on the same page — and the rule was removed rather than
  kept as an untested claim (D-016).
- The officials' Q&A confirmed no headless browser in grading. Rather than let seven
  render-dependent checks silently vanish, two were re-derived static-only and the rest are
  declared in `degraded_stages[]` (D-015).

---

## Further reading (shipped in this package)

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the decomposition and the tests that would falsify it
- [`docs/BUNDLE-SCHEMA.md`](skills/site-evidence-collector/references/bundle-schema.md) — the evidence-bundle contract between collector and analysers
- [`docs/research/EVIDENCE-LEDGER.md`](docs/research/EVIDENCE-LEDGER.md) — one row per check: mechanism, cited sources, evidence strength, severity rule, false-positive guard, and the signals rejected with reasons
- [`docs/EVALS.md`](docs/EVALS.md) — the evaluation protocol
- [`docs/evals/stage-e-report.md`](docs/evals/stage-e-report.md) — measured precision / recall / clean-site FP per check
- [`docs/DECISIONS.md`](docs/DECISIONS.md) — the numbered, dated log of every design decision, what it cost, and what is still unresolved
