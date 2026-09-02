# Progress

Living state of the Round 3 build. Updated at the end of every meaningful chunk of work
(see the `project-flow` skill). Newest notes at the top of each list.

**Current phase:** 3 — Authoring the skills. Phase 2 closed by D-013 / `ARCHITECTURE.md`.

## Done

- 2026-09-02 — **Phase 1b Synthesis Complete.**
  - `docs/RESEARCH.md` mapped with all 24 signal definitions (13 discoverability, 11 engagement) backed by literature.
  - `docs/research/EVIDENCE-LEDGER.md` populated with the 24 candidate checks, their source mappings, severity rules, and false-positive guards.
  - `docs/EVALS.md` rewritten with the concrete metric targets and procedures derived from `05-evaluation-methodology.md`.
  - `docs/CORPUS.md` rewritten with the stratified sampling frame and split logic derived from `08-web-corpora-and-sampling.md`.
- 2026-09-01 — **Domains 04 and 06 landed**, executed in Antigravity (separate tool,
  separate budget) from the stored briefs — 13 entries each, statuses marked per entry:
  [`papers/04-...`](research/papers/04-web-agents-page-understanding.md) (WebArena,
  Mind2Web, VisualWebArena, WorkArena, BrowserGym, AssistantBench, WebVoyager, AutoWebGLM,
  Trafilatura) and
  [`papers/06-...`](research/papers/06-structured-data-entity-grounding.md) (WDC Oct 2024,
  Web Almanac 2024, MAVE, FEVER, BLINK, ReFinED, PopQA/Mallen, FreshLLMs, TempLAMA).
  These close the two substantive discoverability gaps.
- 2026-09-01 — **Literature review, priority half complete.** Four domain agents landed: 01 (GEO), 05 (Eval), 07 (On-site), 08 (Corpora). Conclusions banked as decisions **D-006** to **D-010**.
- 2026-09-01 — Research scaffolding: `research/README.md`, `research/EVIDENCE-LEDGER.md`, `research/AGENT-BRIEFS.md`, `EVALS.md`, `CORPUS.md`.
- 2026-09-01 — Handout read in full, copied to `round3-handout.pdf`, distilled into the `round3-spec` skill; working method in the `project-flow` skill.

## Next — phased, each phase ends in a checkpointed state

**Phase 2 — architecture.** Fix the skill decomposition and the entrypoint's composition
contract. Blocked on nothing, but running research domains 02 and 03 would strengthen the justification.

**Phase 3 — author the skills.** `SKILL.md` per concern, `references/` for checklists,
`scripts/` for executable checks.

**Phase 4 — corpus + harness.** Build the dev/held-out/negative-control/adversarial sets
and the eval harness per D-010.

**Phase 5 — harden and package.** Guardrail and generalization gates, root `README.md`,
manifest, zip.

## Deferred — the four unrun research domains

Briefs are ready in [`AGENT-BRIEFS.md`](research/AGENT-BRIEFS.md); relaunch is copy-paste.

| Domain | Why it was deferred | What we lose without it |
| --- | --- | --- |
| 02 Skill authoring | Phase 3 can proceed on general practice | Weaker evidence base for *how* instructions are written for reliability and determinism |
| 03 Composition | Phase 2 can proceed on judgment | The rubric's composition line becomes an argument from taste, not evidence |

**Honest status of coverage:** both halves of the audit now have a research base — 01/04/06
for discoverability, 07 for engagement, 05 for evaluation, 08 for corpora. The two
remaining domains affect how well we can *justify* design choices (how skills are authored,
and how many there should be), not what the checks are. They are worth running before
Phase 2 if budget allows, but they do not block it.

## Phase 1b review — corrections outstanding

Reviewed 2026-09-02; full detail in
[`research/EVIDENCE-LEDGER.md`](research/EVIDENCE-LEDGER.md) under "Review — 2026-09-02".

- **R-1 (done)** — all 24 rows had been self-certified as hand-verified by the authoring
  tool; reset to `— pending`. A human must spot-check one cited source per check.
- **R-2 (done)** — search-only sources removed from load-bearing roles: CHK-D-003's severity
  rule is now definitional rather than threshold-based; CHK-E-024 demoted to a proactive
  recommendation under the new single-source rule.
- **R-3 (done)** — `NORMATIVE` recorded as **D-011** with a full strength vocabulary and
  ceilings; CHK-E-020 re-grounded on WCAG 2.2 SC 1.4.2 and demoted to `medium`; CHK-E-021
  given one coherent label and capped.
- **R-7 (done)** — ID sequence documented as deliberate and stable; dev gold labels 20 → 24;
  negative controls 24 → 27; report schema settled as **D-012** (`findings[]` for defects,
  sibling `recommendations[]` and `limitations[]`).
- **R-4 (done)** — headless rendering now budgeted: one shared render pass per sampled page
  (max 3), seven declared consumers, 220 s subtotal against the 300 s cap with 80 s
  reserve, and a degradation rule emitting `not_determinable` rather than inferring from
  static HTML.
- **R-5 (done)** — off-site coverage added: **CHK-D-025** (no declared identity anchors),
  **CHK-D-026** (declared anchors that don't resolve — bounded off-site HEAD checks),
  **CHK-D-027** (identity attributes self-inconsistent across own pages). What stays
  unmeasurable is declared as **LIM-01…LIM-04** and reported, not omitted. Ledger is now
  **27 checks + 4 declared limitations**.
  - *Follow-on:* `CORPUS.md` sizes negative controls at 3 per each of 8 dimensions; the
    off-site dimension makes 9, so that set should grow to 27 sites.
- **R-6 (done)** — Phase 2 decomposition decided deliberately as **D-013**: six skills, split
  by mechanism with network I/O extracted into `site-evidence-collector`. Full rationale,
  composition contract, and check map in [`ARCHITECTURE.md`](ARCHITECTURE.md), now
  authoritative for check ownership.

**All seven review findings resolved.** Phase 2 complete.

## Phase 3 — authoring (in progress)

Marketplace root created at [`brand-ai-readiness-audit/`](../brand-ai-readiness-audit) —
this directory is what gets zipped.

- **Done — the interface.** [`BUNDLE-SCHEMA.md`](BUNDLE-SCHEMA.md) pins the evidence bundle
  to exact field names, with a coverage walk confirming all 27 checks can be satisfied.
  Three caveats recorded (ad detection is the weakest check; CHK-D-012's time-sensitivity
  label belongs in the analyser; CHK-E-016's "standalone" is deliberately collector-side).
  One conflict with ARCHITECTURE.md found and resolved: 3 navigations / 4 viewport
  measurements, not 6.
- **Done — `marketplace.json`** with exactly one entrypoint.
- **Done — `site-evidence-collector`**: `SKILL.md` (lean), plus `references/procedure.md`,
  `references/ai-crawler-agents.md` (the retrieval-vs-training classification that separates
  CHK-D-001 from CHK-D-002), and `references/bundle-schema.md`.
- **Next — the five remaining skills.** Four analysers and the orchestrator. All are now
  unblocked and mutually independent, since the bundle schema and the finding envelope
  (ARCHITECTURE.md §4.2) are both fixed. They can be written in parallel.
- **Then — `scripts/`** for the deterministic checks, and the marketplace root `README.md`.

**Packaging note (Phase 5):** `docs/BUNDLE-SCHEMA.md` is canonical during development and is
copied to `skills/site-evidence-collector/references/bundle-schema.md`. Re-copy it at
packaging time so the shipped bundle is self-contained and cannot drift.

## Blocked / open questions

- **No public AI-assistant citation dataset exists**, and no curated site-quality label
  corpus — domain 08 searched and found neither. Gold labels must be hand-authored.
- **Corpus access blockers:** HTTP Archive needs a billed Google Cloud project; CrUX needs
  an API key and excludes small sites (exactly our target population); ClueWeb22 is gated;
  Tranco's combined-list licence is unclear. Wayback is unreliable as a fixture source (at
  most ~17.9% of composite mementos are both temporally coherent and complete).
- **Nothing in the literature measures our actual target quantity** — the effect of a
  specific site-side fix on a specific brand's representation in a specific assistant. That
  experiment does not appear to exist publicly. We build on mechanism-level evidence, and
  the report's language must say so.
- **ICC assumption.** Domain 08's sample-size math assumes ρ≈0.20 (unmeasured). ρ > 0.4
  falsifies the split plan.
