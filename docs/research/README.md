# Research program

The Round 3 rubric rewards checks that surface *real* causes with *few false positives*,
and generalize to unseen sites. The only defensible way to get there is to derive every
check from a documented mechanism rather than from intuition or from sites we happened to
look at. This directory is that evidence base.

**The rule that governs everything here:** a check does not enter the marketplace unless
it can name the mechanism it tests, the source(s) that establish that mechanism, the
quantitative evidence it will emit, the rule that assigns its severity, and the condition
under which it must stay silent. That trace lives in
[`EVIDENCE-LEDGER.md`](EVIDENCE-LEDGER.md).

## Domains

Eight parallel reviews, ~13-15 sources each (~100-115 total). Each file uses a fixed
per-source schema: mechanism → quantitative result → transfer to our audit →
false-positive risk → eval implication.

| # | File | Question it answers | Feeds |
| --- | --- | --- | --- |
| 01 | [`papers/01-geo-ai-search-visibility.md`](papers/01-geo-ai-search-visibility.md) | What actually determines whether an AI assistant finds, cites, and correctly represents a brand? | Discoverability checks |
| 02 | [`papers/02-agent-architecture-skill-design.md`](papers/02-agent-architecture-skill-design.md) | How do you author agent instructions so behaviour is reliable, deterministic, portable? | How every `SKILL.md` is written |
| 03 | [`papers/03-multi-agent-orchestration.md`](papers/03-multi-agent-orchestration.md) | When does decomposition help, when does it hurt, what does the entrypoint owe? | Marketplace composition |
| 04 | [`papers/04-web-agents-page-understanding.md`](papers/04-web-agents-page-understanding.md) | How do machines really read pages, and what signals machine-unreadability? | Crawl/render checks + runtime budget |
| 05 | [`papers/05-evaluation-methodology.md`](papers/05-evaluation-methodology.md) | How do we measure detection quality, action quality, determinism, generalization? | [`../EVALS.md`](../EVALS.md) |
| 06 | [`papers/06-structured-data-entity-grounding.md`](papers/06-structured-data-entity-grounding.md) | What makes a fact extractable, believed, disambiguated, and current? | Extraction / corroboration / freshness checks |
| 07 | [`papers/07-onsite-engagement-evidence.md`](papers/07-onsite-engagement-evidence.md) | Which *observable page properties* measurably predict visitors leaving? | Engagement checks |
| 08 | [`papers/08-web-corpora-and-sampling.md`](papers/08-web-corpora-and-sampling.md) | Where do dev and held-out test websites come from, and how are they split? | [`../CORPUS.md`](../CORPUS.md) |

Domain 07 is the one most likely to be hand-waved by other submissions and is treated
accordingly: the constraint that we observe only what a read-only crawler sees — never
analytics, dwell time, or bounce rate — means every engagement check must rest on a
published link between a *page property* and a *measured outcome*, or be reported as not
determinable.

## Evidence standards

Every source carries a status and, where it matters, a type:

- `VERIFIED` — the reviewing agent opened it and read the abstract or paper.
- `SEARCH-ONLY` — it surfaced in search with a plausible title and venue but could not be
  opened. Usable as a lead, **not** as a foundation for a check.
- `PEER-REVIEWED` vs. `INDUSTRY (not peer-reviewed)` — industry web-performance numbers
  are widely repeated and often untraceable to a primary source; they are labelled, and
  an untraceable statistic is recorded as untraceable rather than repeated.
- `CAUSAL` / `CORRELATIONAL` / `THEORETICAL` / `PRACTITIONER OBSERVATION` — engagement
  research especially is mostly correlational, which caps how strongly we may phrase a
  finding and how high its severity may go.

Anything an agent inferred rather than read is marked `(our inference)`. Fabrication
protocol: no source enters a file without a URL that was actually retrieved; unverifiable
candidates are dropped, not guessed at.

**These files are drafted by AI research agents and are not self-certifying.** Before any
source is used to justify a shipped check, it gets spot-checked by hand — see the
verification gate in [`EVIDENCE-LEDGER.md`](EVIDENCE-LEDGER.md).

## How research becomes a skill

```
mechanism (Round-2 appendix A-F)
   └─ source(s) establishing it            → papers/NN-*.md
        └─ signal observable read-only     → RESEARCH.md entry
             └─ check with a page budget   → EVIDENCE-LEDGER.md row
                  └─ finding + severity + suggested action → a skill's SKILL.md
                       └─ measured on dev, frozen on held-out test → EVALS.md
```

A check that cannot complete this chain is not shipped. A check whose only justification
is "this is a known SEO best practice" is not shipped either — that is precisely the
fit-to-folklore failure the rubric's generalization line is designed to catch.
