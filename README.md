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

Built for **Adobe University Hackathon 2026 — Round 3, "Build the Agent Skill Marketplace."**

---

## Table of Contents

- [Overview](#overview)
- [How it works](#how-it-works)
- [Skills](#skills)
- [How to run an audit](#how-to-run-an-audit)
- [Evaluation results](#evaluation-results)
- [Guardrails](#guardrails)
- [Tech stack](#tech-stack)
- [Repository map](#repository-map)
- [Running the harness locally](#running-the-harness-locally)
- [Project status](#project-status)
- [Contributors](#contributors)
- [License](#license)

---

## Overview

`brand-ai-readiness-audit/` is a **read-only [agentskills.io](https://agentskills.io)
marketplace**. It is a set of composable agent skills, not a hosted service, and it audits
any website for two failure classes:

1. **Off-site discoverability**: why AI assistants fail to find, fetch, read or correctly
   cite a brand (robots.txt policy, crawler access, entity and identity markup).
2. **On-site engagement**: why visitors who do arrive don't stay, or can't (thin content,
   accessibility defects, broken structure).

Given a URL or bare domain, the entrypoint skill returns **one structured JSON report**:
evidence-backed findings with severity, prioritized suggested actions, proactive
recommendations that go beyond detected defects, and an explicit list of what the audit
could not measure. Every check is observational. The marketplace never changes the site it
audits.

Everything outside `brand-ai-readiness-audit/` (research, decision log, evaluation harness,
corpus) is the evidence trail that produced the shipped skills. See
[Repository map](#repository-map).

---

## How it works

<p align="center">
  <img width="760" alt="Brand AI-Readiness Audit: architecture, evidence bundle, evaluation harness, severity ceiling and final report" src="https://github.com/user-attachments/assets/25a6f1e3-80c8-47cf-9a8f-1828ad17ecff" />
</p>

| Panel | What it shows |
| --- | --- |
| **01 Architecture** | `audit-orchestrator` (the entrypoint) calls the collector once. Three analysers read the same evidence bundle, and the orchestrator composes and self-checks the report. |
| **02 Evidence bundle** | The collector's deterministic steps: robots.txt → discovery → static pages → internal links → off-site anchors → render pass. All run in memory, in under 5 minutes. |
| **03 Evaluation harness** | Frozen snapshots, hand-labelled gold data, a scorer, and stress tests (clean controls, adversarial sites, AI-judge reviews) feeding a diagnose → fix → re-run loop. |
| **04 Severity ceiling** | The strength of a check's evidence caps how severe its finding can be. Weak or single-study support ships as a recommendation only. |
| **05 Final report** | One JSON file in which every finding points to the evidence behind it. |

**Why five skills.** The analysers are **blind to each other by construction**: none reads
another's output. The design started as six skills. A leave-one-skill-out ablation on 36
real sites showed that the one cross-skill rule between two of them never fired, so those
two were merged on evidence, not intuition. The full rationale, and the tests that would
falsify the split, are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Skills

| Skill | Role | Checks |
| --- | --- | --- |
| **`audit-orchestrator`** *(entrypoint)* | Invokes the collector once, runs the three analysers, then assembles, ranks and self-checks the final report | — |
| `site-evidence-collector` | The only skill that touches the network: robots.txt, sampled page inventory, bounded link and anchor reachability, site archetype | — (observes only) |
| `crawl-access-audit` | Separates retrieval-time AI crawlers (ChatGPT-User, PerplexityBot…) from training-corpus crawlers (GPTBot, Google-Extended, CCBot…). Blocking retrieval at the root is `critical` | 2 |
| `content-engagement-audit` | Content completeness and structure from a non-rendering fetch, plus statically detectable on-page defects (WCAG, viewport, autoplay, landmarks) | 17 |
| `entity-identity-audit` | Does the site say who it is unambiguously, mark it up machine-readably, and anchor itself to external profiles? Includes archetype-specific schema checks | 13 |

**Graceful degradation.** A `headless_browser` tool is optional. When it's absent (the
expected grading case), checks that need rendered geometry report `not_determinable` and
are listed in `degraded_stages[]`. They are never guessed from static HTML.

---

## How to run an audit

The marketplace is provider-neutral: any agent runtime that can load agentskills.io
`SKILL.md` files and expose an `http_fetch` tool can run it.

1. Unzip `brand-ai-readiness-audit/`, or point the runtime at it.
2. Load `marketplace.json`. The skill marked `"entrypoint": true` is `audit-orchestrator`.
3. Invoke `audit-orchestrator` with:
   - `target`: a URL or bare domain, e.g. `example.com`
   - `budget_s`: optional, default `300` (hard ceiling on collection time)
4. Follow `skills/audit-orchestrator/SKILL.md` → **Procedure** (steps 1–7).
5. The output is one JSON report (GIF panel 05). The full schema is in
   [`report-schema.md`](brand-ai-readiness-audit/skills/audit-orchestrator/references/report-schema.md).

Full detail: [`brand-ai-readiness-audit/README.md`](brand-ai-readiness-audit/README.md).

---

## Evaluation results

The audit was measured, not just designed. The full record is in
[`docs/evals/stage-e-report.md`](docs/evals/stage-e-report.md).

| Metric | Result |
| --- | --- |
| Gold labels | 624 cells: 24 dev sites × 26 checks, hand-labelled from frozen snapshots before seeing tool output |
| Precision (checks with n ≥ 10 sites) | 11 of 15 checks ≥ 0.90, 8 of those at 1.00 |
| Clean-site false-positive rate | 0.00 on 14 of 21 checks with a defined FP rate (15 negative-control sites) |
| Adversarial robustness | 6 bot-blocked, unfetchable or malformed sites: 0 crashes, 100% schema conformance |
| Composition test | Leave-one-skill-out ablation and merge test on 36 real sites |
| Set stability (k = 3) | Identical `(check_id, locus)` finding set across 3 live runs on 5 sites |
| External review | 25 sites scored by three independent judges on six rubric axes; fixes are logged in `docs/DECISIONS.md` D-035 to D-037 |

No check was tuned to make a number look better. Checks were changed only when a
disagreement traced to a real bug. For example, a robots.txt parser missing RFC 9309 `$`
support was reporting a site as *blocking* crawlers it explicitly *allowed*, on a
`critical`-severity check (D-031).

---

## Guardrails

- **Recommend-only.** No skill ever changes a live site.
- **robots.txt is obeyed**, including `crawl-delay`, by the one skill that fetches.
- **No authenticated areas, no bot-detection evasion, no rate abuse.** At most 2 concurrent
  requests per host, and HEAD-only for reachability checks.
- **Under 5 minutes.** Each stage has a hard time budget. A slow site yields a partial
  report on time, never a complete one late.
- **No persistent storage.** The evidence bundle lives in memory for one run and is then
  discarded.
- **Severity is capped by evidence strength** (GIF panel 04).
- **Recommendations this marketplace will never make:** `llms.txt` as a substantive fix,
  promises about citation outcomes, bulk-generated content, or hidden text aimed at
  retrievers. Each has a documented reason (D-007).

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Skill format | [agentskills.io](https://agentskills.io) `SKILL.md` + `references/` + `scripts/` (progressive disclosure) |
| Check logic | Python 3, **standard library only**: no `pip install`, self-contained, under the 50 MB cap |
| HTML parsing | Hand-built DOM tree on `html.parser` |
| Evidence bundle | In memory only, one run, discarded afterwards |
| Eval harness | `harness/`: local-only and git-ignored; imports the shipped `scripts/` unmodified |

---

## Repository map

```
.
├── brand-ai-readiness-audit/     ← THE SUBMISSION. This folder is what gets zipped.
│   ├── marketplace.json          manifest: five skills, one entrypoint
│   ├── README.md                 marketplace README: how to run, skills, evaluation
│   └── skills/
│       ├── audit-orchestrator/        entrypoint: drives the 7-step procedure
│       ├── site-evidence-collector/   the only skill with network access
│       ├── crawl-access-audit/        robots.txt / AI-crawler policy (2 checks)
│       ├── content-engagement-audit/  content + on-site defects (17 checks)
│       └── entity-identity-audit/     identity / structured data (13 checks)
│
├── docs/                         canonical project docs
│   ├── PROGRESS.md               where the work stands; read this first
│   ├── DECISIONS.md              numbered, dated decision log (D-001 … D-037)
│   ├── ARCHITECTURE.md           why five skills, and the tests that would falsify the split
│   ├── EVALS.md                  the evaluation protocol
│   ├── OFFICIALS-QA.md           constraints clarified by the organisers
│   ├── RESEARCH.md               mechanism-anchored signals, and every rejected signal + why
│   ├── research/                 evidence ledger + literature review (102 sources)
│   └── evals/                    gold labels, stage reports, adjudication queue
│
├── PLAN.md                       briefing: task, rubric, what's done, what's left
└── harness/                      local eval harness (git-ignored)
```

---

## Running the harness locally

`harness/` is a local driver that imports the shipped `scripts/` unmodified, so the checks
can be measured against hand-labelled gold data. It is **git-ignored and never part of the
submission**, so a fresh clone won't have it. It requires Python ≥ 3.12 and no third-party
packages.

<details>
<summary><b>Show commands</b></summary>

```bash
# audit one live site (collect → analyse → compose → validate)
python harness/run_audit.py --site example.com

# audit a corpus set; --offline replays frozen snapshots for reproducibility
python harness/run_audit.py --set dev --offline

# precision / recall / clean-site FP per check vs the gold labels
python harness/score_dev.py

# intra-rater test–retest (Krippendorff's α)
python harness/retest.py --emit
python harness/retest.py --score

# composition tests
python harness/ablation.py dev negative
python harness/stability.py

# validate the deliverable and build the zip
python harness/package.py --zip
```

</details>

**Two rules the harness enforces:**
- Gold labels are **human-authored only**. A model may queue a disagreement in
  `docs/evals/adjudication-queue.md`, but it never writes a label.
- The tool's own reports are never read while deciding a label. Doing so would make the
  evaluation circular.

---

## Project status

Research, architecture, skill authoring, the corpus, gold labels, measured
precision/recall, external judge review and packaging are all done. See
[`docs/PROGRESS.md`](docs/PROGRESS.md) for the live state. Every design decision is
logged in [`docs/DECISIONS.md`](docs/DECISIONS.md), numbered and dated: what was done, why,
what it cost, and what is still unresolved.

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
