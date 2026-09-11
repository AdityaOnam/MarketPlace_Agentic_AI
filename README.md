# MarketPlace_Agentic_AI

Submission repository for **Adobe University Hackathon 2026 — Round 3, "Build the Agent
Skill Marketplace."** The deliverable is `brand-ai-readiness-audit/`: a marketplace of
[agentskills.io](https://agentskills.io) skills that, given any website, audits it
read-only for **off-site AI-discoverability** and **on-site engagement** defects and emits
one evidence-backed JSON report.

Everything else in this repo is the research, decision log, and evaluation harness that
produced it.

---

## Repository map

```
.
├── brand-ai-readiness-audit/     ← THE SUBMISSION. This folder is what gets zipped.
│   ├── marketplace.json          manifest — five skills, one entrypoint
│   ├── README.md                 marketplace README: how to run, skills, evaluation
│   ├── skills/
│   │   ├── audit-orchestrator/   entrypoint — drives the 7-step procedure
│   │   ├── site-evidence-collector/   the only skill with network access
│   │   ├── crawl-access-audit/        robots.txt / AI-crawler policy (2 checks)
│   │   ├── content-engagement-audit/  content + on-site defects (18 checks)
│   │   └── entity-identity-audit/     who-are-you / structured data (6 checks)
│   └── docs/                     copies of the design + eval docs, so the zip is self-contained
│
├── docs/                         canonical project docs (the shipped copies mirror these)
│   ├── PROGRESS.md               where the work stands — read this first
│   ├── DECISIONS.md              numbered, dated decision log (D-001 … D-032)
│   ├── ARCHITECTURE.md           why five skills, and the tests that would falsify the split
│   ├── EVALS.md                  the evaluation protocol
│   ├── OFFICIALS-QA.md           constraints clarified by the organisers (no headless browser, etc.)
│   ├── RESEARCH.md               the 26 mechanism-anchored signals, and every signal rejected + why
│   ├── research/EVIDENCE-LEDGER.md   one row per check: sources, evidence strength, severity cap
│   ├── research/papers/          literature review, 102 sources across 6 domains
│   └── evals/                    gold labels, stage reports, adjudication queue, retest log
│
├── PLAN.md                       self-contained briefing: task, rubric, what's done, what's left
├── harness/                      local eval harness — git-ignored, see below
├── dist/                         built zips and labelling kits — git-ignored
└── .claude/skills/               Claude Code project skills (round3-spec, project-flow)
```

---

## How to use the marketplace

The marketplace is provider-neutral. Any agent runtime that can load agentskills.io
`SKILL.md` files and expose an `http_fetch` tool can run it.

1. Unzip (or point the runtime at) `brand-ai-readiness-audit/`.
2. Load `marketplace.json`. The skill marked `"entrypoint": true` is `audit-orchestrator`.
3. Invoke `audit-orchestrator` with:
   - `target` — a URL or bare domain, e.g. `example.com`
   - `budget_s` — optional, default `300` (hard ceiling on collection time)
4. Follow `skills/audit-orchestrator/SKILL.md` → **Procedure** (steps 1–7). The orchestrator
   invokes `site-evidence-collector` once, runs the three analysers against the resulting
   bundle, assembles the report, and self-checks it before emitting.
5. The output is one JSON document. Required fields (`site`, `audited_at`, `summary`,
   `findings[]` with `id / title / severity / evidence / suggested_action`) plus
   `recommendations[]`, `limitations[]`, `degraded_stages[]`, `preamble`, `meta_evaluation`.
   Full schema: `skills/audit-orchestrator/references/report-schema.md`.

**Tools.** Only `site-evidence-collector` declares tools: `http_fetch` (GET/HEAD) and an
optional `headless_browser`. The other four declare `allowed-tools: []`. If no browser is
available — the expected case — the collector marks the render pass `abandoned` and the
report lists the four affected sub-checks in `degraded_stages[]` rather than guessing.

**Executable checks.** All check logic is stdlib-only Python, no install needed. Each
analyser's `scripts/*_checks.py` exposes `evaluate(bundle) -> list[envelope]`;
`audit-orchestrator/scripts/compose_report.py` turns envelopes into the report. See the
marketplace README's *Running the audit* section for the progressive-disclosure map.

Full detail: [`brand-ai-readiness-audit/README.md`](brand-ai-readiness-audit/README.md).

---

## Running the marketplace locally (harness)

`harness/` is a local driver that imports the shipped `scripts/` unmodified and walks a real
site end to end, so the checks can be measured against hand-labelled gold data. It is
**git-ignored** — never part of the submission — so a fresh clone won't have it; ask a
maintainer for a copy. Requires Python ≥ 3.12, no third-party packages.

```bash
# audit one live site (collect → analyse → compose → validate)
python harness/run_audit.py --site example.com

# audit a whole corpus set; --offline replays frozen snapshots for reproducibility
python harness/run_audit.py --set dev --offline
python harness/run_audit.py --set negative --out harness/out/negative

# Stage E: precision / recall / clean-site FP per check vs docs/evals/gold-labels-dev.csv
python harness/score_dev.py
python harness/score_dev.py --check CHK-D-001

# Stage D′: intra-rater test–retest (Krippendorff's α), ≥ 48 h after the first pass
python harness/retest.py --emit     # draw the 8-site subset, write a blind worksheet
python harness/retest.py --score    # score pass 2 against pass 1

# composition tests
python harness/ablation.py dev negative          # set names; defaults to dev negative
python harness/stability.py                     # k=3 live runs over harness/corpus/runtime-sample.csv

# Phase 5: validate the deliverable and build the zip
python harness/package.py           # gates only
python harness/package.py --zip     # gates, then dist/brand-ai-readiness-audit.zip
```

Every run writes `harness/out/<set>/<site>.bundle.json` and `<site>.report.json`, and
appends a row to `harness/out/<set>/index.json` (wall-clock, request count, schema
conformance, finding counts, meta-evaluation warnings).

**Two rules the harness enforces and the docs repeat:**
- Gold labels (`docs/evals/gold-labels-dev.csv`) are **human-authored only**. A model may
  queue a disagreement in `docs/evals/adjudication-queue.md`; it never writes a label.
- Never read `harness/out/dev/*.report.json` while deciding what a label should be — that
  is the tool's own verdict, and using it makes the evaluation circular.

---

## Where the project stands

See [`docs/PROGRESS.md`](docs/PROGRESS.md) for the live state and
[`PLAN.md`](PLAN.md) for the full briefing. In short: research (Phase 1), architecture
(Phase 2), skill authoring (Phase 3), corpus + gold labels + measured precision/recall
(Phase 4, Stages A–E) and packaging (Phase 5) are done. One item remains on the critical
path — the 8-site test–retest reproducibility pass, which needs a human ≥ 48 h after the
first labelling pass.

Every design decision is in [`docs/DECISIONS.md`](docs/DECISIONS.md), numbered and dated,
stating what was done, why, what it cost, and what is still unresolved.

---

## Working with Claude Code

[`.claude/skills/`](.claude/skills/) holds two project skills that give Claude Code the
task context (`round3-spec`) and the session ritual — reload `PROGRESS.md`, work, record
(`project-flow`). Two Claude sessions on two machines coordinated through git plus a local
`WORKLOG.md`.

## License

Apache-2.0 for the marketplace skills (declared in each `SKILL.md` frontmatter). Research
notes and evaluation data in `docs/` are provided for review.
