# Crawler agent classification

Used by step 2 of the collection procedure to populate `robots.agents[*].class`. This
classification is the sole basis for the distinction between CHK-D-001 and CHK-D-002, and it
is the reason the audit does not say "AI bot blocked = bad."

## Why the classes differ

Blocking a **retrieval** agent removes the site from the pool a assistant can fetch and cite
*at answer time*. That is a direct, present-tense consequence for discoverability.

Blocking a **training** agent affects whether the site's content enters a future model's
parametric memory. Research on data-opt-out compliance measured approximately no loss of
general knowledge from honouring these blocks, and many organisations block training
crawlers deliberately as policy. Treating that as a defect would be a false positive
against an intentional choice.

Consequently: a retrieval block is a `critical` finding; a training block is `low` and
informational, suppressed entirely when a retrieval block is already reported.

## Classification table

Match is case-insensitive on the `User-agent` token. Unknown agents classify as `unknown`
and are recorded but never raise a finding.

| Agent token | Class | Notes |
| --- | --- | --- |
| `GPTBot` | training | OpenAI corpus crawler |
| `OAI-SearchBot` | retrieval | OpenAI search indexing |
| `ChatGPT-User` | retrieval | Fetches on behalf of a user's request |
| `ClaudeBot` | training | Anthropic corpus crawler |
| `Claude-Web`, `Claude-User` | retrieval | User-initiated fetch |
| `Claude-SearchBot` | retrieval | Search indexing |
| `PerplexityBot` | retrieval | Search index |
| `Perplexity-User` | retrieval | User-initiated fetch |
| `Google-Extended` | training | Gemini/Vertex training opt-out; does **not** affect Google Search |
| `Googlebot` | hybrid | Classic search index; also feeds AI Overviews |
| `Bingbot` | hybrid | Classic index; feeds Copilot |
| `Applebot-Extended` | training | Apple Intelligence training opt-out |
| `Applebot` | hybrid | Search and Siri |
| `CCBot` | training | Common Crawl; a corpus input, not a live retriever |
| `Bytespider` | training | |
| `Amazonbot`, `Meta-ExternalAgent` | training | |
| `Meta-ExternalFetcher` | retrieval | |
| `cohere-ai`, `Diffbot`, `Omgilibot`, `anthropic-ai` | unknown | Legacy or ambiguous; record only |
| `*` | generic | The wildcard rule; applies where no specific rule matches |

## Rules for use

1. **Specificity wins.** A specific `User-agent` block overrides `*` for that agent, per the
   robots exclusion convention. Record which rule matched in `matched_line`.
2. **A `hybrid` agent blocked at root is reported as retrieval-class**, because the
   present-tense consequence dominates: classic index removal also removes the site from the
   AI surfaces built on that index.
3. **`unknown` never raises a finding.** It appears in the bundle so the evidence is complete
   and so this table can be extended without changing any analyser.
4. **This table is data, not logic.** Extending it must never require touching
   `crawl-access-audit`. Agents change faster than skills should.

## Known limitation

Agent tokens are self-declared and this list is a point-in-time snapshot. A site blocking an
agent that does not appear here is recorded as `unknown` and produces no finding — the
audit's coverage of crawler access is therefore a lower bound, not a complete picture. This
is stated in the report rather than implied.
