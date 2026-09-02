---
name: audit-orchestrator
description: >-
  Entrypoint for the brand AI-readiness audit marketplace. Given a website URL
  or domain, runs every specialist audit skill (crawl access, structured data,
  entity corroboration, on-site engagement), merges and de-duplicates their
  findings, assigns severity and priority, adds proactive recommendations, and
  emits one JSON audit report. Use when asked to audit a site for AI
  discoverability, why a brand is missing or misrepresented in AI assistants,
  or why visitors who arrive do not engage.
license: MIT
allowed-tools:
  - Bash
  - Read
  - Write
---

# Audit Orchestrator (entrypoint)

Composes the specialist skills in this marketplace into a single audit report.
This skill decides *what to run and how to rank it*; it does not itself perform
network checks.

## When to use

Invoke this skill whenever the request is "audit `<url>`" for AI
discoverability and/or on-site engagement. This is the only skill an evaluator
needs to call — it drives the rest.

## Inputs

| Input | Required | Default | Notes |
|---|---|---|---|
| `url` | yes | — | Target site. Accepts `example.com` or a full URL. Normalise to `https://<host>/`. |
| `max_pages` | no | `8` | Page budget across the whole audit. Keeps runtime < 5 min. |
| `out` | no | `audit-report.json` | Where the final report is written. |

## Safety contract (non-negotiable)

Every skill invoked here inherits these rules. Do not relax them.

1. **Read-only.** `GET`/`HEAD` only. Never `POST`, submit a form, or log in.
2. **Recommend-only.** Never modify the audited site. Findings are advice.
3. **Respect `robots.txt`.** Skip any path disallowed for `*`. Never bypass.
4. **No authenticated areas.** Do not follow login/account/checkout flows.
5. **No rate abuse.** >= 0.4 s between requests; hard cap at `max_pages`.
6. **Bounded.** Abort a check that exceeds its budget and report it as
   `not_assessed` rather than guessing.

## Procedure

1. **Normalise the target.** Strip whitespace, add `https://` if absent, keep
   scheme + host. Record `site` (bare host) and `audited_at` (UTC ISO-8601).

2. **Fetch the page set once.** Run
   `scripts/run_audit.py --url <url> --max-pages <n>`. It builds one shared
   crawl (homepage + capped same-domain internal links, robots-filtered) and
   hands the same page set to every check, so the site is fetched once, not
   once per skill.

3. **Run the specialist skills in dependency order.** Layer 1 gates the rest —
   if a machine cannot reach the page, deeper checks are meaningless.

   | Order | Skill | Answers |
   |---|---|---|
   | 1 | `crawl-access-audit` | Can a machine reach and read it? |
   | 2 | `structured-data-extraction` | Can it extract a clean fact? |
   | 3 | `entity-identity-corroboration` | Does it know *who* this is, and is that corroborated? |
   | 4 | `engagement-onsite-audit` | Will a human who arrives stay? |

   If a Layer-1 check returns a blocking failure (homepage unreachable, or
   `robots.txt` disallows `/` for `*`), emit that finding alone with
   `severity: "critical"`, mark the remaining checks `not_assessed`, and stop.
   Do not fabricate downstream findings you could not observe.

4. **Merge findings.** Concatenate all skill outputs, then:
   - drop any finding whose `evidence` is empty or says "0 pages sampled";
   - collapse duplicates by `(check_id, page_scope)`, keeping the higher
     severity and unioning the evidence;
   - renumber sequentially as `F-001`, `F-002`, … in final sort order.

5. **Rank.** Sort by severity (`critical` > `high` > `medium` > `low` >
   `info`), then by confidence, then by breadth (share of sampled pages
   affected). See `references/severity-rubric.md` — apply it verbatim so two
   runs on the same site produce the same ordering.

6. **Add proactive recommendations.** Independently of defects found, emit up
   to five `severity: "info"` findings from
   `references/proactive-playbook.md` that are relevant to the site type
   observed. Mark each `"proactive": true` so they are visibly distinct from
   detected defects.

7. **Emit the report.** Write JSON matching
   `references/report-schema.md` exactly, then print a short human-readable
   summary: total findings, counts by severity, and the top three actions.

## Output

A single JSON object. Required keys — `site`, `audited_at`, `summary`
(with counts by severity), `findings[]`; each finding requires `id`, `title`,
`severity`, `evidence`, `suggested_action` (`summary` + `priority`).

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": { "total_findings": 6, "critical": 1, "high": 2, "medium": 3 },
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

Full field list, including the optional fields this marketplace adds
(`category`, `confidence`, `affected_urls`, `proactive`, `suggested_action.steps`,
`suggested_action.effort`, `suggested_action.mechanism`), is in
`references/report-schema.md`.

## References

- `references/report-schema.md` — the exact output contract.
- `references/severity-rubric.md` — deterministic severity + priority rules.
- `references/proactive-playbook.md` — beyond-defect recommendations.
