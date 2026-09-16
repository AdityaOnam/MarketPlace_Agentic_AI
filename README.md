# Brand AI-Readiness Audit — Agent Skill Marketplace

**Give it a URL. It tells you why AI assistants can't find you, and why visitors who do
arrive don't stay — with evidence, not opinions.**

![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)
![Python: stdlib only](https://img.shields.io/badge/python-stdlib--only-3776AB?logo=python&logoColor=white)
![Skills: 5](https://img.shields.io/badge/skills-5-6f42c1)
![Checks: 32](https://img.shields.io/badge/checks-32-informational)
![Runtime: <5 min](https://img.shields.io/badge/runtime-%3C5%20min-success)
![Status: submission-ready](https://img.shields.io/badge/status-submission--ready-brightgreen)

[Marketplace README](brand-ai-readiness-audit/README.md) · [Architecture](docs/ARCHITECTURE.md) · [Evaluation results](docs/evals/stage-e-report.md) · [Decision log](docs/DECISIONS.md)

Built for **Adobe University Hackathon 2026 — Round 3, "Build the Agent Skill
Marketplace."**

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Skills](#skills)
- [Tech stack](#tech-stack)
- [Repository map](#repository-map)
- [How to run an audit](#how-to-run-an-audit)
- [Evaluation results](#evaluation-results)
- [Guardrails](#guardrails)
- [Running the harness locally](#running-the-harness-locally)
- [Project status](#project-status)
- [Contributors](#contributors)
- [License](#license)

---

## Overview

`brand-ai-readiness-audit/` is a **read-only [agentskills.io](https://agentskills.io)
marketplace** — a set of composable agent skills, not a hosted service — that audits any
website for two failure classes:

1. **Off-site discoverability** — why AI assistants fail to find, fetch, read, or
   correctly cite a brand (robots.txt policy, entity/identity markup, crawler access).
2. **On-site engagement** — why visitors who do arrive don't stay, or can't (thin content,
   accessibility defects, broken structure).

Given a URL or bare domain, the entrypoint skill returns **one structured JSON report**:
evidence-backed findings with severity, prioritized suggested actions, proactive
recommendations that go beyond detected defects, and an explicit list of what the audit
could not measure. Every check is observational — the marketplace never mutates the site
it audits.

Everything outside `brand-ai-readiness-audit/` — research, decision log, evaluation
harness, corpus — is the evidence trail that produced the shipped skills; see
[Repository map](#repository-map).

---

## Architecture

```
                              target URL / domain
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │   audit-orchestrator     │   ENTRYPOINT
                        │   (drives the 7-step     │
                        │    procedure)            │
                        └────────────┬─────────────┘
                                     │  step 1: collect once
                                     ▼
                        ┌─────────────────────────┐
                        │ site-evidence-collector  │   only skill with
                        │ http_fetch (+ optional   │   network access
                        │ headless_browser)        │
                        └────────────┬─────────────┘
                                     │  one in-memory evidence bundle
                     ┌───────────────┼───────────────────┐
                     ▼               ▼                    ▼
            ┌────────────────┐ ┌────────────────────┐ ┌────────────────────┐
            │ crawl-access-   │ │ content-engagement- │ │ entity-identity-    │
            │ audit           │ │ audit               │ │ audit               │
            │ (2 checks)      │ │ (17 checks)         │ │ (13 checks)         │
            └────────┬────────┘ └──────────┬──────────┘ └──────────┬──────────┘
                     │                     │                        │
                     └───────────┬─────────┴────────────────────────┘
                                 ▼
                   roll up → separate findings /
                   recommendations / limitations →
                   assemble → self-check (meta_evaluation)
                                 │
                                 ▼
                       one JSON audit report
```

Analysers are **blind to each other by construction** — none reads another's output. The
design started as six skills; a leave-one-skill-out ablation against 36 real sites showed
the one cross-skill rule between two of them never fired, so they were merged on that
evidence, not intuition. Full rationale and the tests that would falsify the split:
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Skills

| Skill | Role | Checks |
| --- | --- | --- |
| **`audit-orchestrator`** *(entrypoint)* | Invokes the collector once, runs the three analysers, assembles and self-checks the final report | — |
| `site-evidence-collector` | The only skill that touches the network — robots.txt, sampled page inventory, bounded link/anchor reachability | — (observes only) |
| `crawl-access-audit` | Distinguishes retrieval-time AI crawlers (GPTBot, ChatGPT-User, PerplexityBot…) from training-corpus crawlers (Google-Extended, CCBot…); blocking the first is `critical` | CHK-D-001, D-002 |
| `content-engagement-audit` | Content completeness/substance/structure via a non-rendering fetch, plus statically detectable on-page defects (WCAG, viewport, autoplay, missing landmarks) | 17 checks |
| `entity-identity-audit` | Does the site state who it is unambiguously, mark it up machine-readably, and anchor itself to external profiles? | 13 checks |

**Graceful degradation, always.** A `headless_browser` tool is optional. When it's absent
(the expected grading case), the four checks that need rendered geometry are reported as
`not_determinable` and named in `degraded_stages[]` — never guessed from static HTML.

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Skill format | [agentskills.io](https://agentskills.io) `SKILL.md` + `references/` + `scripts/` (progressive disclosure) |
| Check logic | Python 3, **stdlib-only** — no `pip install`, keeps the marketplace self-contained and under the 50 MB cap |
| HTML parsing | Hand-built DOM tree on `html.parser` — no bundled dependency |
| Evidence bundle | In-memory only, one run, discarded after — no persistent storage, no cross-run influence |
| Eval harness | `harness/` — local-only, git-ignored, imports the shipped `scripts/` unmodified |
| Docs | Markdown decision log, evidence ledger, architecture notes — all shipped or mirrored into the zip |

---

## Repository map

```
.
├── brand-ai-readiness-audit/     ← THE SUBMISSION. This folder is what gets zipped.
│   ├── marketplace.json          manifest — five skills, one entrypoint
│   ├── README.md                 marketplace README: how to run, skills, evaluation
│   ├── skills/
│   │   ├── audit-orchestrator/        entrypoint — drives the 7-step procedure
│   │   ├── site-evidence-collector/   the only skill with network access
│   │   ├── crawl-access-audit/        robots.txt / AI-crawler policy (2 checks)
│   │   ├── content-engagement-audit/  content + on-site defects (17 checks)
│   │   └── entity-identity-audit/     who-are-you / structured data (13 checks)
│   └── docs/                     copies of the design + eval docs, so the zip is self-contained
│
├── docs/                         canonical project docs (the shipped copies mirror these)
│   ├── PROGRESS.md               where the work stands — read this first
│   ├── DECISIONS.md              numbered, dated decision log (D-001 … D-032)
│   ├── ARCHITECTURE.md           why five skills, and the tests that would falsify the split
│   ├── EVALS.md                  the evaluation protocol
│   ├── OFFICIALS-QA.md           constraints clarified by the organisers (no headless browser, etc.)
│   ├── RESEARCH.md               the mechanism-anchored signals, and every signal rejected + why
│   ├── research/EVIDENCE-LEDGER.md   one row per check: sources, evidence strength, severity cap
│   ├── research/papers/          literature review, 102 sources across 6 domains
│   └── evals/                    gold labels, stage reports, adjudication queue, retest log
│
├── PLAN.md                       self-contained briefing: task, rubric, what's done, what's left
├── harness/                      local eval harness — git-ignored, see below
└── dist/                         built zips and labelling kits — git-ignored
```

---

## How to run an audit

The marketplace is provider-neutral: any agent runtime that can load agentskills.io
`SKILL.md` files and expose an `http_fetch` tool can run it.

1. Unzip (or point the runtime at) `brand-ai-readiness-audit/`.
2. Load `marketplace.json`. The skill marked `"entrypoint": true` is `audit-orchestrator`.
3. Invoke `audit-orchestrator` with:
   - `target` — a URL or bare domain, e.g. `example.com`
   - `budget_s` — optional, default `300` (hard ceiling on collection time)
4. Follow `skills/audit-orchestrator/SKILL.md` → **Procedure** (steps 1–7). The orchestrator
   invokes `site-evidence-collector` once, runs the three analysers against the resulting
   bundle, assembles the report, and self-checks it before emitting.
5. The output is one JSON document: `site`, `audited_at`, `summary`, `findings[]`
   (`id` / `title` / `severity` / `evidence` / `suggested_action`), plus
   `recommendations[]`, `limitations[]`, `degraded_stages[]`, `preamble`,
   `meta_evaluation`. Full schema:
   [`skills/audit-orchestrator/references/report-schema.md`](brand-ai-readiness-audit/skills/audit-orchestrator/references/report-schema.md).

Full detail: [`brand-ai-readiness-audit/README.md`](brand-ai-readiness-audit/README.md).

---

## Evaluation results

Measured, not just designed — full record in
[`docs/evals/stage-e-report.md`](docs/evals/stage-e-report.md).

| Metric | Result |
| --- | --- |
| Gold labels | 624 cells — 24 dev sites × 26 checks at labelling time, hand-labelled from frozen snapshots before seeing tool output |
| Precision (checks with n ≥ 10 sites) | 11 of 15 checks ≥ 0.90, 8 of those at 1.00 |
| Clean-site false-positive rate | 0.00 on 14 of 21 checks with a defined FP rate; 15 negative-control sites, 2–3 per dimension |
| Adversarial robustness | 6 sites (bot-blocked / unfetchable / malformed) — 0 crashes, 100% schema conformance after fixes |
| Composition test | Leave-one-skill-out ablation + merge test on 36 real sites — the one cross-skill rule never fired, so 6 skills merged to 5 on that evidence |
| Set stability (k = 3) | Identical `(check_id, locus)` finding set across 3 live runs, 5 sites |
| Open | Intra-rater test–retest (Krippendorff's α), scheduled ≥ 48h after first labelling pass |

No check was tuned to make a number look better: three checks were fixed because a
disagreement traced to a real bug (a robots.txt parser missing RFC 9309 `$` support was
reporting a site as *blocking* crawlers it explicitly *allowed*, on a `critical`-severity
check) — see [`docs/DECISIONS.md`](docs/DECISIONS.md) D-029…D-032.

---

## Guardrails

- **Recommend-only** — no skill ever mutates a live site.
- **`robots.txt` is obeyed**, including `crawl-delay`, by the one skill that fetches.
- **No authenticated areas, no bot-detection evasion, no rate abuse** — 2 concurrent
  requests per host, HEAD-only for reachability checks.
- **< 5 minute runtime**, hard per-stage time budget with graceful degradation — a slow
  site yields a partial report on time, never a complete one late.
- **No persistent storage** — the evidence bundle is in-memory for one run and discarded.
- **Severity capped by evidence strength** — causal/hard-mechanical evidence may reach
  `critical`; normative and correlational evidence caps lower; contested support ships
  only as a recommendation, never a scored finding.
- **A fixed list of recommendations this marketplace will never make** — `llms.txt` as a
  substantive fix, citation-outcome promises, bulk-generated content, hidden or
  retriever-directed text — each with a documented reason (`docs/DECISIONS.md` D-007).

---

## Running the harness locally

`harness/` is a local driver that imports the shipped `scripts/` unmodified and walks a
real site end to end, so the checks can be measured against hand-labelled gold data. It is
**git-ignored — never part of the submission** — so a fresh clone won't have it. Requires
Python ≥ 3.12, no third-party packages.

```bash
# audit one live site (collect → analyse → compose → validate)
python harness/run_audit.py --site example.com

# audit a whole corpus set; --offline replays frozen snapshots for reproducibility
python harness/run_audit.py --set dev --offline
python harness/run_audit.py --set negative --out harness/out/negative

# Stage E: precision / recall / clean-site FP per check vs docs/evals/gold-labels-dev.csv
python harness/score_dev.py
python harness/score_dev.py --check CHK-D-001

# Stage D′: intra-rater test–retest (Krippendorff's α), ≥ 48h after the first pass
python harness/retest.py --emit     # draw the 8-site subset, write a blind worksheet
python harness/retest.py --score    # score pass 2 against pass 1

# composition tests
python harness/ablation.py dev negative          # set names; defaults to dev negative
python harness/stability.py                      # k=3 live runs over harness/corpus/runtime-sample.csv

# Phase 5: validate the deliverable and build the zip
python harness/package.py           # gates only
python harness/package.py --zip     # gates, then dist/brand-ai-readiness-audit.zip
```

**Two rules the harness enforces:**
- Gold labels (`docs/evals/gold-labels-dev.csv`) are **human-authored only**. A model may
  queue a disagreement in `docs/evals/adjudication-queue.md`; it never writes a label.
- Never read `harness/out/dev/*.report.json` while deciding what a label should be — that
  is the tool's own verdict, and using it makes the evaluation circular.

---

## Project status

See [`docs/PROGRESS.md`](docs/PROGRESS.md) for the live state and
[`PLAN.md`](PLAN.md) for the full briefing. Research, architecture, skill authoring, the
corpus + gold labels + measured precision/recall, and packaging are done. One item remains
on the critical path: the 8-site test–retest reproducibility pass.

Every design decision is logged in [`docs/DECISIONS.md`](docs/DECISIONS.md), numbered and
dated — what was done, why, what it cost, and what is still unresolved.

---

## Contributors

| Name | Role |
| --- | --- |
| **Aditya Onam** ([@AdityaOnam](https://github.com/AdityaOnam)) | Architecture, research, skill authoring, evaluation harness, packaging |
| **Aditya Gupta** ([@code-epic-adi](https://github.com/code-epic-adi)) | Contributor |
| **Varada Patel** ([@Varada2908](https://github.com/Varada2908)) | Contributor |

---

## License

Apache-2.0 for the marketplace skills (declared in each `SKILL.md` frontmatter). Research
notes and evaluation data in `docs/` are provided for review.
