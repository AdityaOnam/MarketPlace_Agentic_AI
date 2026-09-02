# Composition rules — audit-orchestrator

The concrete algorithms behind `SKILL.md`'s procedure steps 4 and 8. This is where the
"not padding" case for the marketplace's decomposition is actually won or lost
(`docs/ARCHITECTURE.md` §4.3) — write these rules down precisely enough that they're
falsifiable, not just asserted.

---

## 1. Root-cause dedup

**Group by locus.** Every finding envelope carries a `locus.url`. Group all envelopes with
`state == "present"` by that URL (site-level checks with no per-page locus — e.g.
`CHK-D-001`, `CHK-D-025` — form their own single-member group keyed by the site itself).

**Within the homepage's group, check for the JS-only pattern:**

1. If `CHK-D-003` is `present` for this locus (any severity — `critical`, `medium`, or
   `low` per its tiered rule), it is the **root-cause finding** for the group.
2. Any of `CHK-D-004`, `CHK-D-005`, `CHK-E-019` that are **also** `present` for the same
   locus are **not** added to `findings[]` as separate entries. Instead, append each one's
   `check_id` and `evidence` string to the root finding's own record as a `consequences[]`
   array:

   ```json
   {
     "id": "F-001",
     "check_id": "CHK-D-003",
     "consequences": [
       { "check_id": "CHK-D-004", "evidence": "Page https://example.com/: main-content extraction yielded 12 words after boilerplate removal." },
       { "check_id": "CHK-E-019", "evidence": "Homepage: plain HTTP fetch yielded 12 words; no loading indicator or noscript present." }
     ],
     ...
   }
   ```

3. The merged finding's `severity` is `CHK-D-003`'s own severity (never averaged or
   escalated by the consequences), and its `suggested_action` stays `CHK-D-003`'s ("implement
   SSR/SSG") — fixing the root mechanically resolves the consequences too, and a suggested
   action list padded with three ways of saying "render server-side" would fail the
   suggested-action-quality rubric line.
4. `CHK-D-005` merges into the group only when its own locus matches the homepage; if it
   fired on a *different* sampled page than the one `CHK-D-003` evaluated, it is **not**
   merged — it stands as its own finding, because the shared root cause established for
   the homepage doesn't extend evidentially to a page that wasn't part of that comparison.

**When `CHK-D-003` did not fire** (`absent` or `not_determinable`) but `CHK-D-004`,
`CHK-D-005`, or `CHK-E-019` independently fired elsewhere (e.g. a non-JS site with a
genuinely thin page), **do not merge them.** There is no established shared root cause;
each stands as an independent finding with its own evidence and severity.

**Do not invent additional dedup pairs beyond this one.** The falsification test in
`docs/ARCHITECTURE.md` §7 (test 3) is explicit that if this logic never fires across the
dev corpus, the decomposition it exists to justify is decorative. Adding speculative merge
rules to make this section look busier would defeat the point of that test.

## 2. Access-block framing (not suppression)

If `crawl-access-audit` reports `CHK-D-001` (retrieval-time crawler blocked at root)
`present`: do **not** suppress any other finding because of it. Instead, add one line to
the report preamble naming the blocked agent(s) and stating that content findings below
describe content those specific agents cannot currently reach. A human fixing the site, or
an assistant not in the blocked set, still needs every other finding at full strength.

## 3. Budget arbitration — `degraded_stages[]`

Read `bundle.budget.stages[]`. For every stage with `abandoned == true`, emit one entry:

```json
{ "stage": "render_pass", "planned_items": 3, "completed_items": 2, "affected_checks": ["CHK-D-003", "CHK-E-014", "CHK-E-015", "CHK-E-016", "CHK-E-018", "CHK-E-019", "CHK-E-023"] }
```

`affected_checks` is the fixed consumer list from
`docs/research/EVIDENCE-LEDGER.md`'s "Runtime budget and the shared render pass" table —
reproduced here so this skill doesn't have to re-derive it at run time:

| Stage | Consumer checks |
| --- | --- |
| `robots_discovery` | CHK-D-001, CHK-D-002 |
| `static_fetch` | every check reading `pages[]` (all `render-extractability-audit` and `entity-identity-audit` checks, plus CHK-E-014/017/020/021/022/024) |
| `render_pass` | CHK-D-003, CHK-E-014 (contrast subtype), CHK-E-015 (overflow subtype), CHK-E-016, CHK-E-018, CHK-E-019, CHK-E-023 |
| `internal_links` | CHK-D-009 |
| `offsite_anchors` | CHK-D-026 |

This is purely informational — it does **not** change which analysers run (they always run;
they are cheap pure functions with no budget of their own) and it does **not** override any
`not_determinable` an analyser already emitted correctly per its own FP guard. It exists
so a report reader sees "the render pass completed 2 of 3 pages" instead of silently
wondering why several checks came back unmeasured.

## 4. What this skill does not do

- It does not re-score, escalate, or demote any severity an analyser assigned — the one
  exception is the dedup merge in §1, which changes *reporting shape*, not the severity
  value itself.
- It does not second-guess an analyser's `not_applicable`/`not_determinable` classification.
- It does not invent a check. Every `check_id` it ever emits originates in an analyser's
  own envelope.
