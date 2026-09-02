# brand-ai-readiness-audit

An Agent Skill Marketplace that audits **any** website for the problems that
make a brand hard for AI assistants to find and cite, and hard for arriving
visitors to understand and engage with — then emits one prioritized,
evidence-backed report.

**Read-only and recommend-only.** No skill here ever modifies the audited site.

> This folder is a **reference template** showing every file a submission needs.
> Two specialist skills are included as worked examples; the real submission
> adds `structured-data-extraction` and `entity-identity-corroboration` in the
> identical shape.

## Layout

```
sample-marketplace/
├── marketplace.json                 # manifest: every skill + exactly one entrypoint
├── README.md                        # this file
├── APPROACH.md                      # the thinking behind the checks
├── lib/
│   └── fetch_lib.py                 # shared stdlib-only crawler (one crawl, all checks)
├── examples/
│   └── sample-report.json           # what the entrypoint emits
└── skills/
    ├── audit-orchestrator/          # ← ENTRYPOINT
    │   ├── SKILL.md
    │   ├── scripts/run_audit.py
    │   └── references/
    │       ├── report-schema.md
    │       ├── severity-rubric.md
    │       └── proactive-playbook.md
    ├── crawl-access-audit/
    │   ├── SKILL.md
    │   ├── scripts/check_crawl_access.py
    │   └── references/checks.md
    └── engagement-onsite-audit/
        ├── SKILL.md
        ├── scripts/check_engagement.py
        └── references/checks.md
```

## The skills

| Skill | Concern | Answers |
|---|---|---|
| **audit-orchestrator** *(entrypoint)* | Composition & reporting | What ran, what matters most, what to do first |
| **crawl-access-audit** | Layer 0–1 · reach & read | Can a machine get in, and does it see what a human sees? |
| **engagement-onsite-audit** | Layer 4 · humans | Once someone lands deep and context-free, can they orient and act? |

Each owns a distinct failure layer, so a finding belongs to exactly one skill —
that is the separation of concerns, not a folder split.

## How the entrypoint composes them

1. Normalises the URL and stamps `audited_at`.
2. Runs each specialist script as a subprocess, collecting `{"findings": [...]}`.
3. **Gates on Layer 0** — if the crawler is blocked or the homepage is
   unreachable, downstream checks are marked `not_assessed` rather than guessed.
4. De-duplicates by `(check_id, affected_urls)`, keeping the worst severity.
5. Ranks by the fixed rubric in `references/severity-rubric.md` (deterministic).
6. Appends up to five proactive `info` recommendations.
7. Renumbers `F-001…` and writes one JSON report.

A skill that fails or times out never breaks the audit — it is recorded in
`scope.checks_not_assessed`.

## Run it

```bash
python skills/audit-orchestrator/scripts/run_audit.py --url example.com --max-pages 8
```

Individual skills run standalone too:

```bash
python skills/crawl-access-audit/scripts/check_crawl_access.py --url example.com
```

Python 3.8+, standard library only. No install step, no network services, no
model weights.

## Guardrails

- `GET` only — never `POST`, form submission, or login.
- `robots.txt` honoured; disallowed paths are **not fetched**, only reported.
- ≥ 0.4 s between requests; hard page cap (default 8); 10 s request timeout;
  2 MB response cap.
- Whole audit completes in well under 5 minutes for a typical site.
- Deterministic ordering — the same site produces the same report.
