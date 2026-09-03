# Progress

Living state of the Round 3 build. Updated at the end of every meaningful chunk of work
(see the `project-flow` skill). Newest notes at the top of each list.

**Current phase:** 3 — Authoring the skills. **Complete** as of 2026-09-03: all six
`SKILL.md` files, the root `README.md`, and `scripts/` for every skill now exist, and
every check has been exercised against synthetic bundles (module tests plus one full
end-to-end pipeline run: real HTML through extraction, all four analysers, orchestrator
composition). Phase 2 closed by D-013 / `ARCHITECTURE.md`. R-1 hand-verification remains
open and blocking before ship (see `EVIDENCE-LEDGER.md`'s gate).

## Done

- 2026-09-02 — **Phase 3, all 6 skills authored.** See "Phase 3 — skill authoring
  (6 of 6 — 2026-09-02)" below for the full per-skill breakdown and the note on how the
  three duplicated skills were reconciled between two parallel sessions.

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

## Phase 3 — skill authoring (6 of 6 — 2026-09-02)

Marketplace root at [`brand-ai-readiness-audit/`](../brand-ai-readiness-audit).

Authored across two parallel Claude sessions on two devices working from the same handoff
brief. `render-extractability-audit` was written once (session A only). The other three —
`entity-identity-audit`, `engagement-defect-audit`, and `audit-orchestrator` — were written
independently by *both* sessions, producing two full versions of each. Reconciled
2026-09-02: for each of the three, the more rigorous version was kept (concrete numeric
thresholds and normalization rules rather than looser prose — e.g. named legal-entity-suffix
equivalence for CHK-D-027, explicit WCAG contrast ratios for CHK-E-014f), and
`audit-orchestrator/references/report-schema.md` was enriched with the other session's
27-check title-map table, which the kept version didn't have but needs for D-010's
run-to-run title stability. Both sessions independently reached the same correction to
`ARCHITECTURE.md` §4.3 (see below) — a useful cross-check that it's actually right.

- ✅ `BUNDLE-SCHEMA.md` — interface contract with coverage walk (all 27 checks satisfied).
  Three caveats recorded (ad detection is the weakest check; CHK-D-012's time-sensitivity
  label belongs in the analyser; CHK-E-016's "standalone" is deliberately collector-side).
  One conflict with ARCHITECTURE.md found and resolved: 3 navigations / 4 viewport
  measurements, not 6.
- ✅ `marketplace.json` — exactly one entrypoint, all six skill paths now exist on disk.
- ✅ `site-evidence-collector` — `SKILL.md` (lean), plus `references/procedure.md`,
  `references/ai-crawler-agents.md` (the retrieval-vs-training classification that separates
  CHK-D-001 from CHK-D-002), and `references/bundle-schema.md`.
- ✅ `crawl-access-audit` — `SKILL.md` (lean, no `references/` — two checks reading one
  bundle section don't need progressive disclosure).
- ✅ `render-extractability-audit` — `SKILL.md` + `references/checks.md` (7 checks,
  mechanisms B/C: CHK-D-003, D-004, D-005, D-009, D-010, D-011, D-013).
- ✅ `entity-identity-audit` — `SKILL.md` + `references/checks.md` (7 checks, mechanism D —
  the only skill reading `anchors`; classifies EVERGREEN vs. TIME-SENSITIVE for CHK-D-012
  per `BUNDLE-SCHEMA.md` Caveat 2; documents LIM-01/LIM-02 as structurally out of scope).
- ✅ `engagement-defect-audit` — `SKILL.md` + `references/checks.md` (11 checks, mechanisms
  E/F — the biggest skill; framed per D-008 as defect detection, never outcome prediction;
  CHK-E-024 routes to `recommendations[]` via `"route": "recommendations"` under the
  single-source rule; CHK-E-023 requires ≥2 independent ad-detectors to agree).
- ✅ `audit-orchestrator` — `SKILL.md` + `references/report-schema.md` (entrypoint; collect
  → run four analysers → cross-skill suppression (rule O-1: CHK-E-019 yields to CHK-D-003,
  the one genuinely cross-skill dependency) → JS-only root-cause dedup (rule O-2, requires
  all of CHK-D-003/004/005/E-019 present simultaneously before collapsing) → separate
  findings/recommendations/limitations → assemble). Documents that two of
  `ARCHITECTURE.md` §4.3's three named "cross-skill suppression" examples
  (CHK-D-002/D-001, CHK-D-010/D-004) are actually same-skill pairs already resolved inside
  `crawl-access-audit` and `render-extractability-audit` respectively.
- ✅ **`brand-ai-readiness-audit/README.md`** — the root README required at submission per
  `round3-spec` §7: what the marketplace does, a table of all six skills and their checks,
  how `audit-orchestrator` composes them (collect → analyse → reconcile → assemble), the
  guardrails, and the declared limitations. Links verified against the actual `docs/`
  paths.
- ✅ **`scripts/` for all six skills** (2026-09-03), stdlib-only Python (no pip installs,
  keeps the marketplace self-contained). `site-evidence-collector`'s scripts turn
  already-fetched raw content into bundle sections — robots.txt parsing/classification, a
  full HTML extraction pipeline built on a from-scratch DOM tree (`html.parser`, no
  bundled dependency), deterministic seeded sampling, and the render-geometry
  classification (WCAG contrast ratio via the real relative-luminance formula, the
  ad-region two-detector rule, overlay/tap-target detection) — they never fetch or render
  anything themselves; that stays the agent's `http_fetch`/`headless_browser` tool calls.
  Every one of the 27 checks is implemented as a pure `evaluate(bundle)` function and
  exercised against synthetic bundles; a full pipeline run (real HTML → extraction → all
  four analysers → orchestrator composition) confirmed the pieces integrate, not just
  each in isolation. Two real bugs found and fixed during testing: an `href=""` falsy-string
  check that silently excluded empty anchors from the `interactive_empty` count, and a
  leftover-redistribution step in page sampling that ignored the per-type cap it was
  supposed to enforce. One naming bug found and fixed structurally: all four analysers had
  independently named their check script `checks.py` — `import checks` after adding more
  than one to `sys.path` would silently reuse whichever loaded first for all the others;
  renamed each to a unique module name (`crawl_access_checks.py`,
  `render_extractability_checks.py`, `entity_identity_checks.py`,
  `engagement_defect_checks.py`) rather than relying on the invoking agent to use
  `importlib` correctly. One doc inconsistency found in `BUNDLE-SCHEMA.md`: it claims
  `trigram_hash` (a single SHA-256 digest) "supports CHK-D-013's Jaccard comparison," but a
  single hash of a whole set can only prove two pages identical or different — it cannot
  produce a similarity *percentage*. Routed around it rather than redesigning the schema:
  CHK-D-013 computes Jaccard directly from `pages[].main_text`, which is already in the
  bundle at no extra cost; `trigram_hash` is left as documented, unused by this check.
- ✅ **Review-pass changes (2026-09-03)** — seven items from an external read of the
  submission, all applied to the marketplace root (`docs/` internal research retains its
  original wording; only `brand-ai-readiness-audit/` ships):
  1. **"rendered page evidence", not "headless browser evidence"** throughout the prose and
     the `not_determinable` reason strings. `headless_browser` stays as the literal
     `allowed-tools` identifier — renaming that would break the tool contract the invoking
     agent binds to; the change is about how the *evidence* is described.
  2. **Determinism reframed as a reproducibility goal, not a requirement.** A live site is
     not a fixed object; the report now says where run-to-run variation is possible
     (`degraded_stages`, `not_determinable`) instead of implying stability it cannot promise.
  3. **Meta-evaluation step added** as orchestrator Step 7 — seven coherence checks over the
     finished report (counts reconcile, findings complete, no duplicate check per locus, known
     check IDs, D-007 prohibited-recommendation scan, limitations present), emitted as a
     `meta_evaluation` block. Warnings are reported, never auto-corrected. **This surfaced a
     real bug in itself on first run:** CHK-E-014 and CHK-E-015 each legitimately grade one
     page twice (static WCAG vs. contrast; viewport meta vs. overflow), which the duplicate
     detector flagged falsely — fixed structurally by tagging those envelopes with a
     `subcheck` discriminator rather than by loosening the check.
  4. **Recommendations stated as vertical-specific**, with the assumed archetype now carried
     in `preamble.archetype` / `recommendations_scoped_to` so a reader knows which vertical
     the actions were written for; `unknown` suppresses archetype-conditioned checks rather
     than guessing.
  5. **Runtime scope clarified**: the budget bounds how long the audit *waits* on an external
     origin, and is not a claim about site latency — a slow site yields a partial report on
     time, never a complete one late.
  6. **Persistent storage removed as an assumption** — the bundle is in-memory for one run
     and discarded; nothing is written to disk or cached, and no run can influence another.
  7. **Novelty stated explicitly** — evidence-capped urgency, root-cause collapse instead of
     four tickets, vertical-conditioned wording, and mechanically-enforced refusal of the
     advice a baseline checklist would emit.
- **Still outstanding from Phase 2 (R-1, blocking before ship):** every row in
  `EVIDENCE-LEDGER.md` still reads `Verified by hand: — pending`. Authoring the skills
  didn't require this, but shipping does — a human needs to open at least one cited source
  per check before this goes in the zip.

**Packaging note:** `docs/BUNDLE-SCHEMA.md` is canonical during development. Re-copy it
to `skills/site-evidence-collector/references/bundle-schema.md` at packaging time (Phase 5).

## Phase 4 — corpus + harness (next)

Build the dev/held-out/negative-control/adversarial sets and the eval harness per D-010.

## Phase 5 — harden and package (queued)

Guardrail and generalization gates, root `README.md`, manifest, zip.


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
