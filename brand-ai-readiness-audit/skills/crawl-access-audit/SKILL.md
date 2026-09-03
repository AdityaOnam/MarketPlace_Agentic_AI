---
name: crawl-access-audit
description: Determine whether AI systems are permitted to fetch a site at all, by reading the parsed robots.txt rules in an evidence bundle and distinguishing blocks on retrieval-time crawlers (which remove the site from what an assistant can cite right now) from blocks on training-corpus crawlers (which are frequently deliberate policy and are not a defect). Use as the first analysis stage of a website audit, because a site an AI cannot fetch makes every other discoverability finding moot.
license: Apache-2.0
allowed-tools: []
---

# Crawl Access Audit

Mechanism A of the brief: *the crawler has to be let in.* If it is not, the page does not
exist for that system — plainly visible to a human, invisible to the machine.

**This skill declares no tools and makes no network requests.** It is a pure function from
an evidence bundle to findings. All fetching happened in `site-evidence-collector`.

## When to use

Invoked by `audit-orchestrator` with an evidence bundle. Its output gates several other
findings: when access is blocked at the root, downstream content findings describe content
no AI system will reach, and the orchestrator uses this result to say so.

## Inputs

The `robots` section of an evidence bundle (`references/bundle-schema.md` in
`site-evidence-collector`). Reads `robots.status`, `robots.agents[*]`, and
`robots.fetch_status`. Reads nothing else.

## Output

Zero to two findings in the standard envelope. Emits `absent` (checked, clean) explicitly —
the negative-control evaluation needs to distinguish "checked and clean" from "never ran".

## Executable checks

`scripts/crawl_access_checks.py` implements both checks deterministically —
`evaluate(bundle) -> list[envelope]`. Tested against synthetic robots.txt bodies covering
retrieval-block, training-block, hybrid-at-root, and robots-unavailable cases.

## Procedure

1. **Gate on evidence.** If `robots.status != "ok"`, emit both checks as
   `not_determinable` with `robots.reason`. Stop. Never infer permission from silence.
2. **Partition agents by class.** `retrieval` and `hybrid` in one set, `training` in the
   other, per the collector's classification. `generic` and `unknown` are recorded but never
   raise a finding on their own.
3. **Evaluate CHK-D-001.** Any agent in the retrieval set with `allowed_root: false` is a
   `critical` finding.
4. **Evaluate CHK-D-002** *only if CHK-D-001 did not fire.* A training-class block with
   retrieval access intact is `low` and informational.
5. **Emit** with `matched_line` quoted in the evidence string.

## The two checks

### CHK-D-001 — Retrieval-time AI crawler blocked at root
- **Strength**: `HARD-MECHANICAL`. The consequence is definitional, not statistical — a
  disallowed path is not fetched. No effect size is required, so this may reach `critical`.
- **Fires when**: any `retrieval` or `hybrid` agent has `allowed_root: false`.
- **Evidence**: `` robots.txt line {matched_line}: Disallow: {rule} applies to {agent} (retrieval-time AI crawler). ``
- **Severity**: `critical`.
- **Suppresses**: CHK-D-002.
- **Silent when**: only `training` agents are blocked; or the block is on a path other than
  root, since a site restricting `/admin` is behaving correctly.
- **Action**: name the specific agent and line, and recommend narrowing the rule to the
  paths that actually need protection rather than removing the file.

### CHK-D-002 — Training-corpus crawler blocked, retrieval intact
- **Strength**: `CORRELATIONAL`, low impact. Research on data-opt-out compliance measured
  approximately no loss of general knowledge from honouring these blocks.
- **Fires when**: a `training` agent has `allowed_root: false` **and** CHK-D-001 did not fire.
- **Evidence**: `` robots.txt blocks {agent} (a training-corpus crawler) but permits retrieval-time AI crawlers. ``
- **Severity**: `low`, informational.
- **Silent when**: CHK-D-001 fired.
- **Action**: state plainly that this is **frequently intentional** and is not necessarily a
  defect; note only that it forgoes future parametric-memory coverage, and leave the
  decision with the site owner.

## Why there is no `references/checks.md`

Two checks reading one bundle section do not need progressive disclosure; a separate file
here would be padding of exactly the kind the rubric penalises. The agent classification
table — the part that genuinely changes over time and is genuinely long — lives in
`site-evidence-collector/references/ai-crawler-agents.md`, next to the code that applies it.

## False-positive discipline

The single largest false-positive risk in this skill is treating "blocks an AI crawler" as
"has a problem". Many organisations block training crawlers as considered policy. The
retrieval/training split exists precisely so this audit does not lecture them about a choice
they made on purpose.
