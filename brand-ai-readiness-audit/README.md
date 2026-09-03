# brand-ai-readiness-audit

A read-only Agent Skill Marketplace that audits any website for two failure classes:

1. **Off-site discoverability** — why AI assistants fail to find, fetch, read, or
   correctly cite a brand.
2. **On-site engagement** — why visitors who do arrive don't stay, or can't.

Given a URL or domain, it produces a single structured report: findings with evidence and
severity, prioritized suggested actions, proactive recommendations that go beyond detected
defects, and an explicit statement of what the audit could not measure. It never modifies
the site it audits — every check is observational.

## Skills

Six skills, split by mechanism (the brief's own ontology), with network access isolated
into exactly one of them:

| Skill | Role | Checks |
| --- | --- | --- |
| **`audit-orchestrator`** *(entrypoint)* | Invokes the collector once, runs the four analysers against the resulting bundle, resolves cross-skill dependencies and shared-root-cause duplicates, assembles the final report | none of its own |
| `site-evidence-collector` | The only skill that touches the network. Fetches robots.txt, a sampled page inventory, a shared rendered-page pass, and bounded internal/off-site link checks — emits one in-memory evidence bundle, no findings | none — observes only |
| `crawl-access-audit` | Is the site's AI-crawler policy actually letting retrieval-time assistants in? | CHK-D-001, D-002 |
| `render-extractability-audit` | Is the content complete, substantial, well-structured, and non-duplicated in what a non-rendering fetch actually receives? | CHK-D-003, D-004, D-005, D-009, D-010, D-011, D-013 |
| `entity-identity-audit` | Does the site state who it is unambiguously, mark it up machine-readably, stay internally consistent, and anchor itself to external profiles? | CHK-D-006, D-007, D-008, D-012, D-025, D-026, D-027 |
| `engagement-defect-audit` | Are there statically/mechanically detectable defects — accessibility, mobile layout, blocking overlays, autoplay, ad density — that obstruct a visitor who already arrived? | CHK-E-014 – E-024 |

27 checks total, disjoint — no check is owned by more than one skill. Full rationale for
this decomposition (why six skills and not one, why not more, and the three tests that
would falsify it) is in [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

## How the entrypoint composes them

`audit-orchestrator` is the only skill meant to be invoked directly for a live audit.

1. **Collect** — run `site-evidence-collector` once against the target; every other skill
   reads that bundle read-only and never fetches anything itself.
2. **Analyse** — run the four analysers against the bundle. They are blind to each other
   by construction, so the same underlying evidence (e.g. the raw-vs-rendered content gap)
   is sometimes computed independently by two of them.
3. **Reconcile** — resolve the one genuinely cross-skill dependency (a blank first paint
   finding deferring to the render-gap finding that explains it), and collapse a JS-only
   site's several downstream symptoms into one root-cause finding rather than reporting
   the same defect four times.
4. **Assemble** — separate confirmed defects (`findings[]`) from proactive,
   beyond-the-defects suggestions (`recommendations[]`) and from what the audit is
   structurally unable to measure (`limitations[]` — e.g. actual cross-web agreement about
   the brand, which would require a search API this marketplace deliberately doesn't call),
   ordered by severity so repeated runs are comparable.
5. **Meta-evaluate** — a light self-check over the finished report before it is emitted:
   do the severity counts reconcile, does every finding carry evidence and an action, did
   suppression actually fire (no duplicate check for one locus), and did any prohibited
   recommendation reach the wording. Warnings are reported in `meta_evaluation`, never
   silently corrected — a report that quietly edits itself until its own audit passes is
   the failure mode this project is most careful about.

Full composition logic — the suppression rule, the dedup rule, the meta-evaluation checks,
and budget arbitration when the collector's time budget runs out mid-audit — is in
`audit-orchestrator/SKILL.md` and its `references/report-schema.md`.

## Recommendations are vertical-specific

Every suggested action is scoped to the site's vertical, and the report states which one it
assumed (`preamble.archetype`). The archetype decides which checks run at all — a personal
or portfolio site is exempt from identity-anchor and Organization-markup checks, a
non-commercial site from trust signals — and how each surviving action is worded: "add a
canonical tag" means something different on a faceted 10,000-SKU catalogue than on a
six-page brochure site. Where no archetype rule matches, the report says `unknown` and
suppresses every archetype-conditioned check rather than guessing, because guessing a
vertical activates suppression logic written for a different kind of site.

**What makes these recommendations more than an issue → fix lookup:** each action's urgency
is capped at the strength of the evidence behind it (a WCAG violation is reported as a
standards violation, never as a conversion claim), co-occurring symptoms are collapsed into
the one root-cause fix that resolves them all rather than issued as four separate tickets,
wording is conditioned on the site's vertical and page type, and the fashionable advice a
checklist would confidently emit — llms.txt as a substantive fix, citation guarantees,
above-the-fold rules — is refused, with that refusal enforced mechanically in the
meta-evaluation step rather than merely promised.

## Guardrails

- **Recommend-only.** No skill ever mutates a live site; every check is a read against
  already-collected, already-fetched evidence.
- **`robots.txt` is obeyed**, including `crawl-delay`, by the one skill that fetches.
- **No authenticated areas, no bot-detection evasion, no rate abuse** — rate-limited to 2
  concurrent requests per host, HEAD-only for internal-link and off-site anchor checks.
- **&lt;5 minute runtime**, enforced by a hard per-stage time budget with graceful
  degradation: a stage that runs out of time is abandoned and reported as
  `not_determinable`, never guessed from partial evidence. The budget bounds how long the
  audit will *wait* on an external origin — it is not a claim about how fast any given
  site responds. A slow site produces a partial report on time, never a complete report
  late, and `budget.stages[].actual_s` records where the time went.
- **No persistent storage anywhere.** The evidence bundle is built in memory during a
  single run, passed to the analysers within that run, and discarded when it ends. Nothing
  is written to disk, nothing is cached, and no run can be influenced by a previous one.
- **Severity is capped by evidence strength**, never asserted past what the underlying
  research supports (see `docs/DECISIONS.md` D-004/D-011) — normative violations (WCAG,
  Better Ads Standards) cap at `high`; single-study, unreplicated support ships only as a
  recommendation, never a scored finding.
- **A fixed list of recommendations this marketplace will never make** — including
  `llms.txt` as a substantive fix, any promise of citation outcomes, and several widely
  repeated but unverifiable performance statistics — recorded in `docs/DECISIONS.md` D-007.

## What this audit does not, and cannot, measure

Stated explicitly in every report's `limitations[]`, not omitted silently:

- Whether the wider web actually agrees with the brand's own claims (would require a
  search or web-scale index API).
- Whether the brand name collides with an unrelated same-named entity elsewhere.
- Whether any AI assistant currently cites the brand — this marketplace never queries a
  live generative engine, because doing so would break reproducibility and the runtime
  budget at once (see `docs/DECISIONS.md` D-006).
- Field engagement outcomes — bounce, dwell time, scroll depth, conversion — none of which
  are observable read-only. The engagement half of this audit detects known-obstructive
  defects; it does not predict how any visitor will behave.

## A note on determinism

The pipeline is built so that the same input against the same site state yields the same
report — same findings, same ordering, same IDs. **This is a design goal in service of
reproducibility, not a requirement imposed on the audit.** It exists so two runs can be
compared, so a fix can be verified as having landed, and so the evaluation harness has
something stable enough to measure. It is not a claim that a live website is a fixed
object: content changes, origins vary their responses, and a stage abandoned on one run
may complete on the next. Where that happens the report says so — `degraded_stages`,
`not_determinable`, and per-stage timings — rather than presenting one run's luck as a
settled result.

## Further reading

- [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) — the skill decomposition and why it's
  split this way
- [`docs/BUNDLE-SCHEMA.md`](../docs/BUNDLE-SCHEMA.md) — the exact evidence-bundle contract
  between the collector and the four analysers
- [`docs/research/EVIDENCE-LEDGER.md`](../docs/research/EVIDENCE-LEDGER.md) — one row per
  check: mechanism, cited sources, evidence strength, severity rule, false-positive guard
- [`docs/DECISIONS.md`](../docs/DECISIONS.md) — the append-only log of every design
  decision and why it was made
