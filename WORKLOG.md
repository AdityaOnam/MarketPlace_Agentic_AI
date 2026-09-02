# WORKLOG — shared coordination log

Two Claude sessions work in this folder. There is no git here, so this file is
the only shared memory between them. **Read this file fully before doing
anything.** Update it before you finish your turn if you touched any files.

---

## How to use this file

> **Git is now initialized** (repo root, initial commit `b0d06a7`). Git covers
> **what changed** (`git log`, `git diff`) — this file covers **why / what's
> next / who's claiming what**. Use both:

1. **Before starting work:** run `git log --oneline` and `git status`, then
   read `## Current status` and `## Claims` below. If the area you're about to
   touch is claimed by the other session and not marked done, either work
   elsewhere or leave a note asking before editing their files.
2. **When you start a chunk of work:** add/update a row in `## Claims` so the
   other session doesn't collide with you.
3. **When you finish a chunk of work:**
   - `git add` + commit your changes with a small, descriptive message,
   - move your row from `## Claims` to done (or delete it),
   - append one entry to `## Log` (newest entry at the **bottom**) — mention
     the commit hash,
   - update `## Current status` if the overall picture changed.
4. Keep log entries short — file paths + one line of what/why; git already
   has the diff. This is a log, not a report.
5. Never edit another session's in-progress files without saying so in a new
   log entry first, and never `git reset`/`git push --force`/rewrite history —
   only ever add commits.

---

## Current status

*(last updated: 2026-09-02, by Opus/Claude Code session — "sample builder")*

- **`brand-ai-readiness-audit/`** — the real submission in progress. Has
  `audit-orchestrator`, `crawl-access-audit`, `engagement-onsite-audit`,
  `entity-identity-corroboration`, `structured-data-extraction` folders
  scaffolded (owner: other session — not yet logged in detail here; other
  session should fill in `## Current status` for this folder next time it
  touches it).
- **`sample-marketplace/`** — a complete, runnable reference template built
  by this session. Full marketplace shape (manifest, entrypoint + 2 specialist
  skills, shared `lib/fetch_lib.py`, references, scripts) + `APPROACH.md`
  explaining the design (5-layer causal chain: Access → Readability →
  Extractability → Identity → Engagement). Verified working end-to-end against
  `example.com` — see `sample-marketplace/examples/sample-report.json`.
  **This is NOT the submission** — it's scaffolding/reference for building the
  real one out.
- **Not started yet:** the "extraordinary" differentiators discussed
  (fixture/precision-recall harness, citation-rehearsal check, template-diverse
  sampling, differential-UA fetch, cross-page contradiction check, dual-path
  script/agent execution). See `APPROACH.md` bottom section + this session's
  chat for the full list and suggested build order.

---

## Claims

*(work currently in progress — check before editing these paths)*

| Path | Claimed by | Since | Status |
|---|---|---|---|
| *(none active)* | | | |

---

## Log

*(append new entries at the bottom, newest last)*

### 2026-09-02 — Opus session — built `sample-marketplace/` reference template
- Created full marketplace: `marketplace.json`, `README.md`, `APPROACH.md`,
  `lib/fetch_lib.py` (shared stdlib-only crawler), `skills/audit-orchestrator`
  (entrypoint), `skills/crawl-access-audit`, `skills/engagement-onsite-audit`,
  each with `SKILL.md` + `references/checks.md` + `scripts/*.py`.
- Verified: `python skills/audit-orchestrator/scripts/run_audit.py --url
  example.com --max-pages 4` runs in 1.8s, produces 9 findings, output saved
  at `sample-marketplace/examples/sample-report.json`.
- Design basis: 5-layer causal chain (L0 Access, L1 Readability, L2
  Extractability, L3 Identity, L4 Engagement) from the Round-2 appendix —
  severity = layer position, skill boundaries = layer boundaries.
- Did **not** touch `brand-ai-readiness-audit/` — left it untouched for the
  other session.
- Next (not yet done): build `structured-data-extraction` (L2) and
  `entity-identity-corroboration` (L3) skills in the same shape; build the
  fixture/precision-recall test harness (highest-leverage remaining item —
  see chat discussion in this session).

### 2026-09-02 — other session — git init
- Other session (`adobe-d5`) ran `git init` + made initial commit `b0d06a7`
  covering everything in the repo at that point (both `brand-ai-readiness-audit/`
  and `sample-marketplace/` plus this file). Added `.gitignore` to exclude
  `.~lock.PS.odt#`.
- Protocol going forward: **commit your own changes with small, descriptive
  messages** as you make them — git carries "what changed" via `log`/`diff`;
  this file stays for "why / what's next / claims". Do not force-push or
  rewrite history — only add commits.
