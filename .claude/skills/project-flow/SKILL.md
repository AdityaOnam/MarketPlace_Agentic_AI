---
name: project-flow
description: Session continuity and working flow for the MarketPlace Agentic AI repo (Adobe Hackathon Round 3). Use at the start of every session to reload where the work stands, and at the end of any meaningful chunk of work to record it. Covers the orientation ritual, the phase plan from research to submission, where decisions and progress are logged, and the invariants that must hold before anything is called done.
---

# Project flow — how work proceeds in this repo

Companion to [`round3-spec`](../round3-spec/SKILL.md), which holds *what* the task is.
This skill holds *how we work on it* and *how context survives across sessions*.

## Orientation ritual (do this first, every session)

1. Read [`round3-spec/SKILL.md`](../round3-spec/SKILL.md) — the task, schema, rubric,
   guardrails. Never work from memory of the task.
2. Read [`docs/PROGRESS.md`](../../../docs/PROGRESS.md) — current phase, what's done,
   what's next, what's blocked.
3. Read [`docs/DECISIONS.md`](../../../docs/DECISIONS.md) — settled choices. **Do not
   re-litigate anything recorded there** unless new evidence contradicts it; if it does,
   append a new entry that supersedes the old one rather than editing history.
4. Skim `marketplace.json` (once it exists) to see the current skill set.
5. Say in one or two lines where things stand before proposing new work.

## Closing ritual (end of any meaningful chunk)

1. Update `docs/PROGRESS.md`: move items between Done / In progress / Next, and note
   anything newly blocked or newly learned.
2. Append to `docs/DECISIONS.md` any choice that a future session would otherwise
   re-open (a check we deliberately included or excluded, a severity rule, a
   decomposition boundary, a runtime trade-off) — with the *reason*, not just the choice.
3. If a research finding shaped a check, record it in
   [`docs/RESEARCH.md`](../../../docs/RESEARCH.md) as **mechanism → signal → check →
   false-positive guard**, never as "site X does Y". The handout grades generalization;
   site-specific notes are a liability.

## Phase plan

| Phase | Goal | Done when |
| --- | --- | --- |
| 0. Context | Task encoded as durable, reloadable repo context | `round3-spec` + `project-flow` skills exist and match the PDF |
| 1. Field research | Distil repeatable signals separating cited from uncited sites, and engaged from bouncing visitors | `docs/RESEARCH.md` holds mechanism-anchored signals, each with a candidate check, evidence shape, severity, and false-positive guard |
| 2. Architecture | Decide the skill decomposition and the entrypoint's composition contract | `docs/DECISIONS.md` records the skill list, each skill's single concern, and the inputs/outputs each returns to the entrypoint |
| 3. Build skills | Author each `SKILL.md` + `references/` + `scripts/` | Every skill is agentskills.io-valid, lean, tool-declaring, deterministic |
| 4. Entrypoint | Compose sub-skill outputs into one report | Report validates against the required schema; counts match findings; ordering stable |
| 5. Harden | Guardrails, runtime budget, graceful degradation | Safety + generalization gates in `round3-spec/references/checklists.md` all pass |
| 6. Package | Root `README.md`, manifest, zip | Submission-compliance gate passes end to end |

Phases can overlap, but **never skip Phase 1**: the whole rubric leans on checks derived
from mechanisms rather than from examples.

## Invariants (hold at all times, not just at the end)

- **Recommend-only.** Nothing we build mutates a live site, authenticates, bypasses
  robots.txt, or abuses request rates. If a check can't be done read-only, it doesn't
  ship.
- **Exactly one entrypoint** in `marketplace.json`.
- **No hard-coded sites, brands, or selectors.** Anywhere. Ever.
- **Every check declares its false-positive guard.** Rubric penalizes false positives as
  much as misses.
- **Every finding carries concrete evidence** — a count, a ratio, a quoted absence — not
  a restatement of the title.
- **Determinism.** Same input ⇒ same output, same order.
- **< 5 min** typical-site runtime; every loop has an explicit cap.
- **Lean `SKILL.md`s.** Detail goes to `references/`, executables to `scripts/`.

## Working style for this project

- Prefer *fewer, well-justified* skills over many thin ones. Padding is explicitly
  penalized; a single well-built skill scores fully on composition.
- When adding a check, write the finding it would emit **first** (title, evidence
  sentence, severity, suggested action) — if that finding wouldn't help a non-expert act,
  the check isn't worth adding.
- When a question about the task comes up, quote the handout rather than inferring.
  If the handout is silent, say so explicitly and record the assumption in
  `docs/DECISIONS.md`.
- Before claiming any phase is complete, run the relevant gate in
  [`round3-spec/references/checklists.md`](../round3-spec/references/checklists.md) and
  report the result honestly, including anything skipped.

## Budget discipline (account limits are a hard project risk)

This is a take-home built with an agent under a shared account rate limit. When the limit
is hit, subagents die mid-task **and so does the main session** — there is no agent left
to recover anything held only in context. Run 1 of the literature review lost eight agents'
work this way. Treat budget as a resource to be spent deliberately.

- **Concurrency ≤ 3-4 subagents.** Eight parallel research agents exhausted a session
  budget without producing a single file. More parallelism past this point buys nothing
  because the limit, not wall-clock, is the bottleneck.
- **Every long-running agent writes its output file incrementally** — first few results
  early, appended as it goes. Never "collect everything, then write." A throttled agent
  that wrote half its findings is useful; one that wrote nothing is a total loss.
- **Checkpoint before spending.** Before launching a batch, `PROGRESS.md` must already
  describe what is running, what is queued, and how to resume. Assume the session dies the
  moment after launch.
- **Prompts are stored, not re-derived.** Agent briefs live in
  `docs/research/AGENT-BRIEFS.md`; relaunching is copy-paste. Re-deriving a brief costs
  budget that should go to the actual work.
- **Prioritize by rubric exposure, not by tidiness.** If only part of the budget is
  available, spend it on the work that carries the rubric lines hardest to bluff, and
  leave the rest queued. A complete high-value half beats eight shallow domains.
- **Don't spend budget on verification theatre.** Re-reading files just written, restating
  finished work, or re-summarizing across turns all cost tokens that the remaining build
  needs.
- **Prefer the cheapest agent that can do the job.** Search-and-extract work does not need
  the largest model; design synthesis does.

## Context-retention rules for the agent

- These skills are the memory. If something learned this session would be needed next
  session, it goes in a file — `PROGRESS.md`, `DECISIONS.md`, `RESEARCH.md`, or the spec
  skill — before the session ends.
- Keep `round3-spec/SKILL.md` in sync with `docs/round3-handout.pdf`. The PDF wins.
- Don't duplicate spec text into other files; link to `round3-spec` instead, so there is
  exactly one place to correct.
