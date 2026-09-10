# R-1 verification worksheet

`R-1` (`PLAN.md` §4, §9): every check's evidence trail needs at least one hand-verified
source before the marketplace ships. The evidence ledger's rows were originally
self-certified by the AI tool that wrote them, which defeats the control — a human has to
actually open the source and confirm it says what the ledger claims. This cannot be
delegated to a model, same rule as Stage D's gold labels: a system verifying its own
sourcing is exactly the failure the control exists to catch.

This worksheet only organizes the work. It does not verify anything.

## What's in `r1-verification-worksheet.csv`

38 distinct sources are cited across the 26 checks (`docs/research/EVIDENCE-LEDGER.md`).
Each row is one source, not one check — several checks often share a source, so the sheet
is sorted to make that leverage visible:

- `in_minimum_set` — `YES` for the 14 sources that, verified together, cover **all 26
  checks** at least once (computed by greedy set-cover: repeatedly pick the source that
  clears the most still-unclosed checks). This is the shortest real path through R-1's
  actual requirement ("one source per check"), not just a leverage ranking.
- `checks_this_clears` / `check_ids` — how many checks cite this source, and which ones.
- `agent_read_status` — `VERIFIED` means the AI research agent that did the original
  Phase 1b literature review actually opened and read this source (as opposed to only
  seeing it in a search result). **This is not R-1 verification** — it only tells you the
  source is genuinely fetchable and the ledger's summary of it was written from the real
  text, not guessed from a title. `SEARCH-ONLY` sources are higher-risk and worth
  prioritizing: the AI agent itself never confirmed what they actually say.
- `human_opened` / `claim_confirmed` / `notes` — blank, yours to fill in.

## Workflow

1. Work down the sheet from the top — it's pre-sorted so the `in_minimum_set=YES` rows
   (highest leverage first) come before the rest.
2. Open the `url`. Read enough to confirm the ledger's claim about this source is
   accurate — check the specific number, mechanism, or finding the relevant check(s) in
   `EVIDENCE-LEDGER.md` actually cite it for, not just that the paper exists.
3. Fill in `human_opened` (yes/no — a paywall or 404 counts as "no", not a pass),
   `claim_confirmed` (yes / no / partially), and `notes` for anything that doesn't match
   what the ledger says.
4. Once every check has at least one row with `human_opened=yes` and
   `claim_confirmed=yes` (or `partially`, with notes on what's off) among its cited
   sources, R-1 is satisfied for that check. Verifying the 14 `in_minimum_set` sources
   alone is enough to satisfy every check at least once — the other 24 sources are
   redundant coverage for the same checks (or single-cite sources whose one check is
   already covered another way), not required.
5. If a claim doesn't hold up, don't silently fix the ledger — flag it. A check whose
   evidence turns out to be wrong is a design problem (per `PLAN.md`: "Prefer cutting a
   check to shipping one we cannot defend"), not just a paperwork fix.

## When you're done

Update `EVIDENCE-LEDGER.md`'s `Verified by hand` column (currently `— pending` on every
row) for each check with at least one confirmed source — cite which source code confirmed
it. That column, not this worksheet, is the record R-1 actually gates on.
