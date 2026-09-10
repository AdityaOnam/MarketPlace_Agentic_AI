# Handoff prompt — merge the 3-site human relabel, re-score Stage E

Copy everything below the line into a fresh session, then attach or point at the filled
worksheet.

---

## Context

You are working in `D:\MarketPlace_Agentic_AI` — a submission for the Adobe University
Hackathon 2026, Round 3 ("Build the Agent Skill Marketplace"). The deliverable is
`brand-ai-readiness-audit/`: a 5-skill agentskills.io marketplace with **26 checks** that
audits any website read-only for AI-discoverability and on-site-engagement defects.

Supporting material, none of which ships:
- `harness/` — the evaluation driver (gitignored). `run_audit.py`, `score_dev.py`,
  `retest.py`, `package.py`, `collect.py`, corpora in `harness/corpus/`, results in
  `harness/out/`.
- `docs/` — `PLAN.md` (root, not in docs), `docs/DECISIONS.md` (append-only decision log,
  currently through **D-032**), `docs/EVALS.md` (evaluation protocol — this is the
  authority), `docs/PROGRESS.md`, `docs/evals/*` (worksheets and stage reports).

Read `PLAN.md` §4 and `docs/EVALS.md` §1–§3 before doing anything substantive.

## Absolute rules — these are not style preferences

1. **Never author or edit a gold label.** `EVALS.md` §1 requires gold labels to be
   hand-authored by a human. A model may flag disagreements into
   `docs/evals/adjudication-queue.md` as a queue for human adjudication — never resolve one.
   This rule has already been violated once and it produced measurable damage (see D-031,
   "circularity"), so it is load-bearing, not ceremonial.
2. **Never read `harness/out/dev/*.report.json` while reasoning about what a label should
   be.** That is the tool's own verdict; using it to inform labels makes the evaluation
   circular.
3. **Never adjust check code to make a disagreement with gold data disappear.** `PLAN.md` §5:
   we author both the checks and the gold labels, so every weakness in the matching rule
   fails silently in our favour. When a check disagrees with a label, diagnose which one is
   wrong. If it is the label, queue it; do not tune the check.
4. **Every non-trivial decision gets an entry in `docs/DECISIONS.md`**, numbered, dated,
   stating what was done, why, what it cost, and what is still unresolved. Follow the
   existing D-028…D-032 format — they are the house style.

## Where things stand (as of 2026-09-11)

**Phase 4** (corpus + harness) is nearly closed:

- Stage D gold labelling complete: `docs/evals/gold-labels-dev.csv`, **624 rows** (24 sites ×
  26 checks), 100% filled.
- Stage E scored: `docs/evals/stage-e-report.md`. The first run returned precision 0.00 /
  recall 0.00 for **all 26 checks** — the matching rule's two evidence-text conditions were
  unsatisfiable by construction. Repaired as **D-028**; matching is now `check_id` + locus
  (rollup-aware), and both retired conditions are printed as diagnostics.
- A diagnosis pass over every cut-rule trip (**D-029 → D-032**) fixed three genuine check
  defects and sent nine disagreements to `docs/evals/adjudication-queue.md` unresolved.
- Current cut-rule trips (8): precision — D-002, D-010 · recall — D-010, E-015 · FP rate —
  D-004, D-007, E-021, E-022. **Six of the eight point at gold data, not code.**
- Three sites are **voided** and score nothing (D-029): `tailscale.com` and `www.thalia.de`
  were audited with 0 pages collected; `vitejs.dev` has 1 snapshot against 11 audited pages.

**The known weakness you are about to fix:** 11 of the 24 sites' gold labels were authored by
a model, not a human — a direct violation of rule 1 above. Three of those sites were packaged
into `dist/human-relabel-kit/` for a first human pass: **`overreacted.io`,
`www.pizzeriabianco.com`, `www.tartinebakery.com`** — 78 cells (3 sites × 26 checks).

## Your task

The user will provide the filled worksheet (normally
`dist/human-relabel-kit/relabel-worksheet.csv`, 78 rows, columns:
`site,archetype_expected,check_id,check_title,where_to_look,criteria,label,locus_url,evidence,notes`).

Do this, in order:

**1. Validate the input before touching anything.**
- 78 rows, exactly the 3 sites above, 26 distinct `check_id` values per site.
- Every `label` is one of `PRESENT` / `ABSENT` / `UNMEASURABLE` / `N/A` (or `SKIP` — the kit
  told the user to write that if they accidentally saw a pass-1 answer; treat `SKIP` as
  "leave the existing row untouched" and report how many).
- Report anything malformed rather than silently coercing it.

**2. Back up, then merge.**
```bash
cp docs/evals/gold-labels-dev.csv docs/evals/gold-labels-dev.pre-relabel-backup.csv
```
Merge by `(site, check_id)` key, replacing `label`, `locus_url`, `evidence`, `notes` for those
78 rows only. **Do not touch any other site's rows.** Afterwards, verify the other 546 rows
are byte-identical to the backup and say so explicitly.

**3. Diff model vs human and report it.**
This is the most interesting output of the whole exercise. For each of the 78 cells, compare
the model-authored label (in the backup, and in `docs/evals/draft-overreacted.io.csv`,
`draft-www.pizzeriabianco.com.csv`, `draft-www.tartinebakery.com.csv`) against the human one.
Report:
- agreement rate overall and per site,
- every disagreement with both labels and the human's note,
- which checks the model got wrong most.

This is a direct measurement of how unreliable model-authored labels are, and it tells the
user how much to worry about the **eight remaining model-labelled sites** (`lwn.net`,
`www.heise.de`, `www.asahi.com`, `franklinbbq.com`, `www.sacher.com`, `jvns.ca`,
`danluu.com`, `sive.rs`). Do not soften it.

**4. Re-score Stage E.**
```bash
python harness/score_dev.py
```
No need to re-run `run_audit.py` — check code has not changed, only labels. Compare against
the pre-merge numbers recorded in `docs/evals/stage-e-report.md` §1.

**5. Update everything that quotes the old numbers.**
- `docs/evals/stage-e-report.md` — §1 table, cut-rule list, and §4/§4b/§4c prose.
- `docs/evals/adjudication-queue.md` — one queued item is `CHK-E-015` on
  `www.tartinebakery.com`; the new human label may resolve it. Check the others too.
- `docs/PROGRESS.md` and `PLAN.md` §4 if the headline changes.
- New decision entry **D-034** in `docs/DECISIONS.md` recording the relabel, the
  model-vs-human agreement rate, and what it implies for the remaining eight sites.
  (**Note:** D-033 is already referenced in a code comment in
  `brand-ai-readiness-audit/skills/audit-orchestrator/scripts/compose_report.py` for the
  action-locus coherence check, but its `DECISIONS.md` entry was never written — write that
  one too, or renumber. Do not leave a dangling reference.)

## After that — what is still open

**Phase 4's remaining gate:** the 8-site intra-rater test–retest (`EVALS.md` §1). Kit is built
at `dist/retest-kit/` (208 cells, blinded, `README.md` explains the protocol). Requires a
human, blind, **≥ 48 h after the labels being tested**. Because this relabel resets pass-1 for
three of those eight sites, their clock restarts from the relabel date. Score with
`python harness/retest.py --score` → Krippendorff's α per check, cut below 0.67.
**No check may be cut until this runs.**

**Phase 5** (harden and package) was started and is partly done:
- ✅ `docs/BUNDLE-SCHEMA.md` re-copied into the collector's `references/` (it had drifted 14
  lines, missing the D-015 note about `rendered` always being `[]`).
- ✅ Action-locus coherence check implemented in `compose_report.meta_evaluate` (`EVALS.md` §4
  specified it; it had never been implemented).
- ✅ `harness/package.py` written — validates manifest, one entrypoint, SKILL.md frontmatter,
  doc drift, no model weights, stdlib-only imports, zip ≤ 50 MB. **Never run yet.** Run
  `python harness/package.py` then `--zip`.
- ❌ **`EVALS.md` §6 held-out generalization has not run and may not be achievable**: it needs
  precision on 12 held-out sites, which needs 312 hand-authored gold labels that do not exist.
  `docs/evals/holdout-log.md` shows 0 of 3 looks used. A defensible partial is one look that
  verifies the audit runs clean on unseen sites (no crashes, schema conformance, runtime
  within budget) while declaring precision-generalization unmeasured — **but running it burns
  one of three irreversible looks, so ask the user first.**

## Environment gotchas

- Shell is Git Bash on Windows. Start commands with `cd /d/MarketPlace_Agentic_AI &&` — the
  working directory does not always persist.
- Prefix `PYTHONIOENCODING=utf-8` on any Python that prints non-ASCII (the corpus contains
  German, Greek and Japanese text; cp1252 will crash the process).
- `python harness/run_audit.py --set dev --offline` regenerates all 24 reports from cached
  fetches in ~2–4 minutes. It exceeds a 120 s tool timeout — run it in the background.
- `harness/score_dev.py` reads `docs/evals/gold-labels-dev.csv` by default.

## Tone

The user wants findings stated plainly, including bad ones about work done earlier in this
project — several of the most valuable results so far were "this number is wrong and here is
why", including a case where the model's own labels were circular. Do not round results toward
looking good, and do not present a partially-completed gate as complete.
