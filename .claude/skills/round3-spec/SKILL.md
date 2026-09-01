---
name: round3-spec
description: Canonical, always-load context for the Adobe University Hackathon 2026 Round 3 task — "Build the Agent Skill Marketplace" (a brand AI-readiness audit marketplace of agentskills.io skills). Use at the start of every session in this repo, and whenever a question touches what we must submit, the marketplace.json manifest, the entrypoint skill, the audit-report schema, the rubric, guardrails, or the Round-2 background concepts. Read this before designing, writing, or reviewing any skill in the marketplace.
---

# Round 3 — Build the Agent Skill Marketplace (canonical spec)

Source of truth: `docs/round3-handout.pdf` (Adobe University Hackathon 2026, Round 3
handout, "updated"). This skill is the distilled, always-available version. If this
file and the PDF ever disagree, **the PDF wins** — re-read it and fix this file.

Full transcription: [`references/handout-full.md`](references/handout-full.md).
Derived checklists: [`references/checklists.md`](references/checklists.md).

## The one-sentence framing

Round 2 tested reasoning *on paper*: why a brand is invisible / stale / bouncing in AI
apps, and what to do about it. **Round 3 tests whether that reasoning can be encoded
into reusable agent skills**, so that a general AI agent, pointed at *any* website, can
audit it automatically and produce a report of findings plus suggested fixes.

Two halves of the problem, both must be covered:

1. **Off-site discoverability** — why the brand isn't found or cited by AI assistants.
2. **On-site engagement** — why visitors who do arrive don't stay.

## Non-negotiable framing rules

- **No example sites are provided.** Field research is part of the task: study real
  sites that AI assistants cite well vs. ones they ignore or misrepresent, and distil
  the *repeatable* signals into the skill, each with evidence and a severity.
- We are **never asked which sites we studied**, and none of them are used in grading.
- **Design for patterns, not fit-to-examples.** Grading is on unseen websites —
  generalization is "tested by construction."
- **Recommend-only.** No skill in the marketplace may modify a live website. It audits
  and reports; suggested actions are recommendations, not applied changes.

## 1. What we submit

A single **Agent Skill Marketplace**: a package of one or more skills, each authored in
the standard **Agent Skills (agentskills.io) format** (a `SKILL.md` with YAML
frontmatter + instructions, optional bundled `scripts/` and `references/`), tied
together by a **marketplace manifest** and **exactly one designated entrypoint skill**
that receives the audit request and emits the final report.

- Decomposing the reasoning into multiple focused skills (**one concern per skill**) is
  the point of the marketplace format, and is rewarded in the rubric.
- A marketplace with only one skill is **accepted as a floor** — a valid submission, but
  not the target.

Given a website, the entrypoint audits it and produces an audit report containing:

- **Problems found** — the issues hurting the brand's AI discoverability and on-site
  engagement (the Round-2 failure modes), each with **evidence** and a **severity**.
- **Suggested actions** — what to change and how to fix each problem, **prioritized**.
  Suggestions **may go beyond** the detected problems: proactive improvements that would
  strengthen discoverability or engagement even where no explicit defect was found.

## 2. Required audit report schema (floor, not ceiling)

Extra fields are allowed; these are the minimum every submission must include.

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3
  },
  "findings": [
    {
      "id": "F-001",
      "title": "No JSON-LD structured data on product pages",
      "severity": "high",
      "evidence": "Crawled 12 product pages; 0/12 contain schema.org markup.",
      "suggested_action": {
        "summary": "Add Product/Offer JSON-LD to every product page.",
        "priority": "high"
      }
    }
  ]
}
```

- **Required per finding:** `id`, `title`, `severity`, `evidence`, `suggested_action`.
- **Required summary metadata:** `site`, `audited_at`, and a counts-by-severity `summary`.

## 3. Marketplace rules

agentskills.io defines the **single-skill** `SKILL.md` format but **does not** define a
multi-skill marketplace format — `marketplace.json` is *this contest's own lightweight
convention*. Every skill folder must still independently satisfy the official
agentskills.io spec.

- Every skill folder listed in the marketplace must contain a valid `SKILL.md` per the
  agentskills.io spec (`name`, `description`, etc.). Optional sanity check if
  Python/npm is available: `skills-ref validate ./skill-folder` (a convenience, not
  required).
- The marketplace root must include a top-level `marketplace.json` listing every skill
  and marking **exactly one** as the entrypoint. The entrypoint is the skill we invoke;
  it is responsible for composing the outputs of any other skills into the single audit
  report.

```json
{
  "name": "brand-ai-readiness-audit",
  "version": "1.0.0",
  "skills": [
    { "id": "audit-orchestrator", "path": "skills/audit-orchestrator", "entrypoint": true },
    { "id": "crawl-render-audit", "path": "skills/crawl-render-audit" },
    { "id": "freshness-corroboration", "path": "skills/freshness-corroboration" },
    { "id": "engagement-audit", "path": "skills/engagement-audit" }
  ]
}
```

### Example layout (illustrative — any structure is fine if the rules hold)

```
brand-ai-readiness-audit/        <- marketplace root (this is what you zip)
  marketplace.json               <- manifest: lists skills + the entrypoint
  skills/
    audit-orchestrator/          <- entrypoint: composes the others, emits final report
      SKILL.md
      scripts/
      references/
    crawl-render-audit/
      SKILL.md
    freshness-corroboration/
      SKILL.md
    engagement-audit/
      SKILL.md
  README.md
```

### SKILL.md format (each skill)

Frontmatter carries `name`, `description` (a rich "what + when to use" description),
`license`. The body is expected to cover:

```
# <Skill title>
## When to use
## Inputs (e.g. a URL / domain)
## Procedure (numbered, deterministic steps)
## Output (an audit report against a fixed schema: findings + suggested actions)
```

Handout guidance, verbatim in spirit:

- Keep each skill's `SKILL.md` **lean** — push detailed checklists to `references/` and
  executable checks to `scripts/` (**progressive disclosure**).
- **Declare any allowed-tools.**
- Narrowly-scoped skills (one concern each) compose more cleanly under the entrypoint
  than one skill that tries to do everything.

## 4. What the marketplace must do

"The skill" = whichever skill performs a given check; split across skills or handled by
one, either is fine **as long as the entrypoint's final report covers everything**.

- **Detect** — cover both halves of the Round-2 problem, reasoning from how these
  systems actually work (see the appendix in `references/handout-full.md`):
  off-site discoverability, and on-site engagement.
  → *Working out the specific, concrete checks that surface each of these is part of
  the task — the handout deliberately provides no checklist.*
- **Report** — for each problem: evidence + severity, then a suggested action (what to
  change and how), prioritized by impact.
- Suggested actions may go **beyond** the problems found (proactive improvements).
- → Emit a **single** audit report (fixed schema): findings + suggested actions.

## 5. How submissions are evaluated

They evaluate **the submitted marketplace itself** — its skills' instructions, checks,
logic, and how they're composed by the entrypoint — **not any single report** it happens
to produce. They look for:

- **What problems it is built to identify** — does it encode the right checks to surface
  the real causes of poor AI discoverability and engagement, with evidence and without
  false positives?
- **How it addresses them** — are the fixes correct, specific, mechanism-sound, and do
  they actually resolve the problems found?
- **How the marketplace is composed** — if split across skills, does the decomposition
  reflect genuine separation of concerns and does the entrypoint compose them cleanly,
  or is it padding? *A single well-built skill is not penalized for not decomposing.*
- **What it does to improve discoverability & engagement beyond fixing specific
  defects** — does it recommend actions that genuinely strengthen how the brand is
  found, cited, and experienced?
- **Generalization** — no example sites are provided, so generalization is tested by
  construction.

### Rubric

| Criterion | Looking for |
| --- | --- |
| Detection accuracy | Correctly identifies the real problems (evidence-backed) across both discoverability and engagement, with few misses and few false positives |
| Suggested-action quality | Fixes are correctly targeted, mechanism-sound, and prioritized; beyond-problem suggestions are relevant and non-obvious |
| Output design | The marketplace's entrypoint skill is built to emit a clear, structured, actionable report (evidence + severity + prioritized actions) a non-expert could act on |
| Skill-format & engineering hygiene | Each skill folder is agentskills.io compliant; the marketplace manifest is well-formed with exactly one entrypoint; deterministic; safe |
| Marketplace composition | Decomposition into skills (if any) reflects genuine separation of concerns, with clean composition by the entrypoint — not padding; a single well-built skill scores fully here too |
| Generalization | Works on unseen sites — no example sites are provided during the task, so generalization is tested by construction |

## 6. Scope & guardrails (hard constraints)

- **Recommend-only** — the marketplace audits and reports; no skill in it ever alters a
  live site, and everything runs **read-only in a sandbox**.
- **No destructive, authenticated-area, or rate-abusing actions. Respect robots.txt.**
- Each skill should be **portable** (agentskills.io format is provider-neutral) and
  **declare its tool needs**; the manifest should be **self-contained** — no external
  service needed to resolve it.
- **Submission zip ≤ 50 MB** (no pre-trained model weights).
- **Audit runtime < 5 minutes** on a standard machine for a typical website.

## 7. Logistics

- Format: **take-home** — building and testing a skill doesn't fit a proctored hour.
- **AI assistance is allowed in Round 3** — building agent tooling with an agent is the
  intended, realistic skill.
- Works on unseen sites; generalization is tested by construction.
- **Submission:** a zip of the marketplace root directory (containing `marketplace.json`
  and every skill folder), with a short **`README.md` at the root** describing what each
  skill does and how the entrypoint composes them.

## 8. Round-2 background concepts (the mechanisms to reason from)

Full text in [`references/handout-full.md`](references/handout-full.md#appendix). The
appendix explains *how these systems behave*, not what to do about any particular site —
deriving checks and fixes from these mechanisms is the job.

- **A. How search visibility works.** A crawler must (1) be let in, (2) be able to read
  what's on the page, and (3) be able to pick out the specific fact being looked for.
  Any one failing ⇒ the page effectively doesn't exist for that system — visible to a
  human, invisible to the machine.
- **B. How assistants use sources.** Assistants search, fetch a few pages, and build the
  answer from what those pages say, often citing them. Pages that get picked tend to be
  **easy to reach, easily read, and easy to quote a clear fact from**. Nothing easy to
  reach/read/quote ⇒ the brand simply isn't in the answer.
- **C. How machines "read" a page.** Content assembled only after load, or in a form a
  simple reader can't interpret, is invisible to a program that isn't looking the same
  way. The more **explicitly and unambiguously a fact is stated in plain, readable
  text**, the more likely it's extracted correctly; implied, buried, or locked in
  non-textual form ⇒ missed.
- **D. Why agreement across the web matters.** A fact repeated consistently across many
  independent, easily-found sources is far more likely to be believed and repeated. A
  claim living in only one spot is fragile. Related failure: **mistaken identity** —
  when several things share a name, a system mixes them up unless something clearly
  distinguishes one. How a brand is described **across the wider web** — not just its own
  pages — shapes what assistants say.
- **E. Personalization and prior context.** Assistants weight prior context about a user
  (earlier messages, past questions, stated preferences, location) — two people asking
  the same question can get different brands, framing, or emphasis. Part of the answer
  depends on **who's asking**.
- **F. Why machines drop content from emails.** AI summaries of long messages are built
  from the message text. When the substance isn't available as readable text (carried by
  something a summarizer can't read, or surrounded by low-value filler), the summary has
  little to work with and the important part disappears.

## How to use this skill

1. Load it first in any session about this repo, before designing or reviewing skills.
2. When answering "does X satisfy the task?", quote the relevant rule from above rather
   than paraphrasing from memory.
3. Before any submission-shaped step, run
   [`references/checklists.md`](references/checklists.md) end to end.
4. If we learn something new about the task (clarification, updated handout), update
   this file *and* `references/handout-full.md`, and note the change in
   `docs/PROGRESS.md`.
