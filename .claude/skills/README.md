# Claude Skills

Project-scoped skills for Claude Code, used when working in this repository.

## Layout

Each skill is a directory containing a `SKILL.md` file with YAML frontmatter:

```
.claude/skills/
└── <skill-name>/
    └── SKILL.md
```

`SKILL.md` frontmatter format:

```markdown
---
name: skill-name
description: One-line description of when to use this skill, written so Claude can
  match it against a request (what it's for + when to trigger).
---

Instructions for Claude to follow when this skill is invoked.
```

## Adding a skill

1. Create a new directory under `.claude/skills/` named for the skill (kebab-case).
2. Add a `SKILL.md` with frontmatter (`name`, `description`) and the instructions body.
3. Keep the description specific — it's what Claude uses to decide when to trigger
   the skill, and what a user types after `/` to invoke it directly.

## Skills in this repository

- [`round3-spec/`](round3-spec/SKILL.md) — **canonical task context.** The Adobe
  University Hackathon 2026 Round 3 brief ("Build the Agent Skill Marketplace"):
  what we submit, the `marketplace.json` convention, the required audit-report schema,
  the rubric, the guardrails, and the Round-2 background mechanisms. Bundles a full
  transcription of the handout and the compliance checklists.
- [`project-flow/`](project-flow/SKILL.md) — **session continuity.** The orientation and
  closing rituals, the phase plan (research → architecture → build → entrypoint → harden
  → package), the standing invariants, and where progress, decisions, and research notes
  are written down.
- [`example-skill/`](example-skill/) — leftover starter template; safe to delete.

Load `round3-spec` before designing or reviewing anything, and `project-flow` at the
start and end of a work session. Mutable state lives in [`docs/`](../../docs):
`PROGRESS.md`, `DECISIONS.md`, `RESEARCH.md`, plus the source handout
`round3-handout.pdf`.
