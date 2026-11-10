# Q&A directory — `brand-ai-readiness-audit`

A study/defence pack for the Adobe University Hackathon 2026 Round 3 submission
(*Build the Agent Skill Marketplace*). Everything here is answered **from the repo as it
stands**, not from memory — each answer points at the file that backs it.

Use it to revise the project, to prepare for a demo or viva, or to onboard someone new in
an hour instead of a week.

---

## How this is organised

| File | What it covers | Question style |
| --- | --- | --- |
| [01-basics.md](01-basics.md) | The task, the deliverable, the shape of the thing | Basic — "what is it, what does it do" |
| [02-keywords.md](02-keywords.md) | Every term of art in the repo, defined | Keyword-specific — "what does X mean here" |
| [03-concepts.md](03-concepts.md) | Mechanisms A–F, evidence discipline, determinism, degradation | Concept-specific — "why does it work this way" |
| [04-skills.md](04-skills.md) | The five skills, one section each | Component-specific |
| [05-checks.md](05-checks.md) | All 32 checks, one Q&A each | Check-specific |
| [06-report.md](06-report.md) | The output schema, field by field | Output-specific |
| [07-evaluation.md](07-evaluation.md) | The harness, the corpus, the measured numbers | Evidence-specific |
| [08-decisions.md](08-decisions.md) | D-001 … D-037, what each settled | History-specific |
| [09-guardrails.md](09-guardrails.md) | Safety, legality, robots.txt, the officials' constraints | Compliance-specific |
| [10-constructive.md](10-constructive.md) | Hard questions, known weaknesses, doc drift, what to do next | Constructive — "where would a critic push" |

---

## Conventions used in the answers

- **Q** is the question, **A** is the answer, and a trailing *(→ file)* names the source of
  truth. Where two files in the repo disagree, the disagreement itself is recorded in
  [10-constructive.md](10-constructive.md) rather than smoothed over.
- **Check IDs** are `CHK-D-NNN` (discoverability) and `CHK-E-NNN` (engagement), in one
  global sequence. IDs are stable and never reused.
- **Decision IDs** are `D-NNN` and refer to `docs/DECISIONS.md`.
- **Limitation IDs** are `LIM-01` … `LIM-05`.

## The five files worth reading before this pack

1. `brand-ai-readiness-audit/README.md` — the marketplace itself
2. `brand-ai-readiness-audit/skills/audit-orchestrator/SKILL.md` — the 7-step procedure
3. `docs/ARCHITECTURE.md` — why five skills, and the tests that would falsify the split
4. `docs/research/EVIDENCE-LEDGER.md` — one row per check
5. `docs/DECISIONS.md` — the numbered log of everything that was decided and why
