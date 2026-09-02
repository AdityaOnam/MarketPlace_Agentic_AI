# Fetch strategy — what to do when direct collection fails

Research note answering three questions: (1) can MCP servers supply the data, (2) what
fallbacks exist when a direct fetch fails, (3) how do we audit and test against sites that
block bots.

**Verification status of this note.** One source was opened and read (the IETF crawler
best-practices draft, marked VERIFIED). Everything else is SEARCH-ONLY under D-003 — usable
as a lead, not as justification for a shipped check. Two claims in §4 are load-bearing and
must be verified before anything is built on them; they are flagged inline.

---

## 1. MCP is not a data source for this audit

The premise "sites expose SEO/LLMO data through an MCP server" does not hold, for three
reasons:

- **Coverage.** ~17,000 MCP servers were publicly listed in 2026 against a web of hundreds
  of millions of active sites. The ones that exist — GitHub, Vercel, Linear, Notion,
  Stripe, Figma — are SaaS products exposing *their own* application data.
- **Purpose mismatch.** An MCP server exposes an application's functions to an agent. It is
  not a description of the site's own HTML, robots.txt, structured data, or rendered
  layout. Every signal in our evidence ledger is a property of the delivered page. An MCP
  endpoint, where one exists, does not describe that page.
- **Auth.** Remote MCP servers standardised on OAuth 2.1. An audit of an arbitrary domain
  has no credentials and must not acquire any — the brief forbids authenticated areas.

The adjacent convention, `/llms.txt`, is already banned as a *recommendation* under D-007
(97% of existing files were never requested in a 137k-domain measurement). It is equally
useless as an *input*: it is self-declared, rare, and unverified.

**Conclusion: no change. The collector fetches the site directly.** This is the right
design, not a limitation to be worked around.

---

## 2. The fallback ladder

When direct collection of a page fails, these are the options, ranked by whether they
actually help.

| Rank | Source | Key needed | What it gives | Honest verdict |
| --- | --- | --- | --- | --- |
| 1 | **Wayback CDX API** (`web.archive.org/cdx/search/cdx`) | none | Capture history, timestamps, status codes, MIME per URL | **Adopt.** Cheap, keyless, and answers a question we cannot otherwise answer (§5) |
| 2 | **Common Crawl CDXJ index** (`index.commoncrawl.org`) + WARC byte-range fetch from `data.commoncrawl.org` | none | Whether CCBot got the page, and the archived HTML itself via a `Range` request | **Adopt for the access signal only.** Not as a content substitute — see §4 |
| 3 | **Wikidata** (`wbsearchentities` / `wbgetentities`) | none | Entity existence, aliases, `sameAs`-equivalent external identifiers | **Adopt.** This is the answer to open question 4 (§6) |
| 4 | Google PageSpeed Insights / CrUX API | key, quota | Field performance data | **Reject.** CrUX excludes small sites — exactly our target population — and D-007 bans Lighthouse-chasing |
| 5 | Brave Search API | card + key | SERP results | **Reject.** Free tier was eliminated in February 2026; now ~$0.003–0.005/query with no spending cap |
| 6 | Mojeek / Exa / other independent indexes | key | SERP results | **Reject for v1.** Adds a procurement dependency and a per-run cost to a submission that must be self-contained |
| 7 | Headless browser with a spoofed consumer UA | none | The page, maybe | **Reject.** See §3 |

Only the top three are keyless, free, deterministic, and compatible with "the manifest
resolves with no external service" — and even they are network calls, so they belong
inside `site-evidence-collector` and nowhere else.

---

## 3. The user-agent question — and why differential-UA fetching must be dropped

The planned "differential-UA fetch" differentiator should be **cut**. Three independent
reasons, any one of which is sufficient:

1. **It is impersonation.** The IETF crawler best-practices draft (VERIFIED) requires that
   "Crawlers must be easily identifiable through their user agent string," carrying both
   owner and purpose. Sending `User-Agent: GPTBot` when we are not GPTBot violates the
   norm our own audit is built on recommending.
2. **It measures the wrong thing.** Major edge providers verify bot identity by reverse DNS
   and IP range, not by the UA string. A fake `GPTBot` from an arbitrary IP is classified as
   a *spoofer* and blocked for spoofing. We would measure our own dishonesty and report it
   as the site's defect — a false positive by construction.
3. **It is out of scope.** Deliberately triggering bot-detection to observe it sits against
   the "no rate-abusing actions, read-only, sandboxed" constraint.

**The collector uses one honest UA for every request**, in the documented form:

```
Mozilla/5.0 (compatible; BrandAIReadinessAudit/1.0; +<project-url>)
```

Cloaking detection is therefore **not determinable** by us, and belongs in `limitations[]`
as a new LIM entry, not in `findings[]`. The academic method for detecting cloaking
("Cloak of Visibility", Kapravelos et al., IEEE S&P 2016) requires exactly the
multi-identity crawling infrastructure we have just ruled out — worth citing as the reason
we decline, which is stronger than silence.

---

## 4. The finding that matters: the fallback fails where it is needed

This is the important result and it is negative.

The intuition is that archives cover us when a site blocks us. They do not, because
**archive coverage and bot-blocking are correlated in the wrong direction**:

- Common Crawl selects URLs per domain by **harmonic centrality** — small, sparsely-linked
  sites get few pages or none. Our corpus is deliberately 3 head / 3 mid / **4 tail** per
  stratum, so the fallback is thinnest exactly on the majority of our targets.
  ⚠️ **VERIFY BEFORE USE.**
- Common Crawl is not a representative sample of the web and skews English.
  ⚠️ **VERIFY BEFORE USE.**
- A site that blocks crawlers generally blocks CCBot too. The "Consent in Crisis" work
  (already cited in our domain-01 brief) measured a 28–45% decline in crawler access, with
  ~45% of C4 restricted and >25% of tokens on critical domains newly restricted inside one
  year.

So: on a site that blocks us, Common Crawl most likely also has nothing — and when it does
have something, it may be a year stale. **Archived HTML must never be silently substituted
for a live fetch.** Doing so would put non-verbatim evidence into a finding, breaking
D-010's third matching condition (evidence appears verbatim in the snapshot) and corrupting
the metric we most need to protect.

**Use the archives for the access signal, not for content.** Presence/absence of recent
captures is itself evidence, and it is evidence we can get no other way.

---

## 5. Block taxonomy — deterministic detection

The current procedure treats robots.txt as the access question. It is not the whole
question: **a site can allow `GPTBot` in robots.txt and still block it at the edge.** That
gap is real and currently unreported.

Response classes the collector should distinguish and record (not infer from status alone):

| Class | Signal | Meaning |
| --- | --- | --- |
| `robots_disallow` | Parsed rule matches path | Declared policy. Already CHK-D-001/D-002 |
| `edge_challenge` | `cf-mitigated: challenge` header; body contains `cdn-cgi/challenge-platform`; typically 403, formerly 503 | Interstitial challenge — automated clients get no content |
| `edge_block` | Flat 403 with a provider error code in body (e.g. 1020 firewall rule, 1006/1007 IP ban), no `cf-mitigated` | Hard WAF/IP decision |
| `rate_limited` | 429, or `Retry-After` present | Our own pacing — back off, never retry aggressively |
| `soft_404` | 200 with body matching an error template | Content absent despite success status |
| `ok` | 200, content present | — |

Status code alone is insufficient: challenge and block both surface as 403, and the
JS-challenge moved 503→403 during 2023, so any rule keyed on 503 is stale. The
`cf-mitigated` header is the reliable discriminator. ⚠️ SEARCH-ONLY — verify against a
live challenge response before shipping a check on it.

### Proposed new check

**CHK-D-028 — retrieval agents permitted by robots.txt but blocked at the edge.**
State `present` when robots.txt grants root access to a retrieval-class agent *and* our own
honest, rule-compliant request is met with `edge_challenge` or `edge_block`.
Evidence strength `HARD-MECHANICAL` (an interstitial returns no content — definitional, no
effect size needed). Severity ceiling `high`, not `critical`: our UA is not a retrieval
agent, so this is a strong indicator that automated clients are refused, not proof about a
specific named agent. FP guard: suppress when `rate_limited`, since that is our own fault.
Corroborating signal: absence of Wayback captures in the last 12 months.

This check is worth having because it catches a genuine and common misconfiguration — a
site whose owner believes they have opted into AI retrieval because robots.txt says so,
while the WAF in front of it says otherwise. A robots.txt-only audit reports that site as
clean.

---

## 6. Off-site corroboration without a search API (open question 4)

Open question 4 assumed entity corroboration needs a search API. It does not, for the
narrow version we actually need.

We are not measuring citation share (D-006 forbids it) or search rank. We are measuring
**whether the brand is resolvable as an entity and whether its declared identity anchors
agree**. That is answerable from keyless sources:

1. **On-site:** `Organization`/`Person` JSON-LD, `sameAs` array, `outbound_profile_links` —
   already collected.
2. **Wikidata** (`wbsearchentities`, then `wbgetentities`): does an entity for this brand
   exist; what aliases and external identifiers does it carry. Keyless, free, documented.
   Known limitation: `wbsearchentities` cannot filter by entity type, so results mix
   people, places and organisations — a name-match alone is **not** identification.
3. **Existing anchor HEAD checks** (≤8, one per registrable domain, already specified).

Deterministic conclusions available from that:

- Declared `sameAs` targets that do not resolve — *already covered*.
- No `Organization` entity anywhere and no Wikidata entity → the brand has no
  machine-resolvable identity. Reportable.
- Wikidata entity exists but its external identifiers and the site's `sameAs` **disagree**
  → a genuine disambiguation risk, evidence-backed and verbatim-quotable.
- Multiple distinct Wikidata entities share the brand name → ambiguity risk, reportable as a
  `recommendations[]` item, never as a defect.

What stays **not determinable**: whether any assistant actually confuses the brand. That is
an outcome claim, banned by D-006. Say so in `limitations[]`.

---

## 7. How to test against sites that block bots

The eval never depends on a live blocked site, because a live site's block state is not
reproducible and `pass^k` at k=5 would fail on network variance alone.

1. **Fixtures, not live sites.** `CORPUS.md` already lists bot cloaking, challenge pages,
   robots-blocking and paywalled sites in the adversarial set. Each becomes a **frozen
   bundle** — a recorded response including the real headers (`cf-mitigated`, error body,
   429 with `Retry-After`). Analysers run against bundles, so a blocked site is just a
   bundle whose sections are `unavailable`. This is the payoff of the collector boundary in
   ARCHITECTURE §3: **the hard part of testing blocked sites was already solved by making
   analysers network-free.**
2. **Self-hosted replicas.** A local server returning a genuine Cloudflare-shaped challenge
   body, a 1020, a 429 with `Retry-After`, and a soft-404 costs almost nothing and is fully
   deterministic. This is how the §5 taxonomy gets verified without hammering anyone's site.
3. **Score graceful degradation, not detection.** The adversarial set is already specified
   as scored on graceful degradation only. The pass condition for a blocked site is: the
   run completes inside budget, emits `not_determinable` rather than inferring, names the
   block class in `limitations[]`, and raises **zero** findings that depend on unfetched
   evidence. A blocked site that produces confident findings is the worst failure mode we
   have — it is a false positive on a site we never saw.
4. **Negative control.** A site that blocks *everything* must produce a report with an empty
   `findings[]` and a populated `limitations[]`. If it produces findings, the guard is
   broken. This belongs in the negative-control set, which §2 of `EVALS.md` already
   protects above all other metrics.

---

## 8. What this changes

| # | Change | Where |
| --- | --- | --- |
| 1 | Drop differential-UA fetching; single honest UA | `procedure.md` §4, and the differentiator list |
| 2 | Add the six-class block taxonomy; record class, never infer from status | `procedure.md`, `BUNDLE-SCHEMA.md` |
| 3 | Add CHK-D-028 (robots-allows / edge-blocks) to `crawl-access-audit` | `EVIDENCE-LEDGER.md`, `ARCHITECTURE.md` §5 |
| 4 | Add Wayback + Common Crawl presence as a bounded access signal — **not** a content source | `procedure.md` §7, alongside identity anchors |
| 5 | Add Wikidata lookup to close open question 4 | `entity-identity-audit` |
| 6 | Add LIM entry: cloaking not determinable, with the reason | `audit-orchestrator` |
| 7 | Build challenge/block fixtures before writing any check that reads the taxonomy | `CORPUS.md` |

Items 4 and 5 add off-origin requests, so they need a budget line and a hard cap in the same
style as the existing ≤8 anchors — suggest ≤3 archive queries and ≤2 Wikidata queries,
3 s timeout each, all failures degrading to `not_determinable`.

---

## 9. Sources

VERIFIED (opened and read):
- IETF, *Crawler Best Practices* (draft-illyes-aipref-cbcp-00) —
  https://www.ietf.org/archive/id/draft-illyes-aipref-cbcp-00.html

SEARCH-ONLY (leads; must be verified before any check depends on them):
- Common Crawl CDXJ Index — https://commoncrawl.org/cdxj-index · https://index.commoncrawl.org/
- Wayback CDX Server API — https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
- Wikibase API — https://www.mediawiki.org/wiki/Wikibase/API/en
- `Cf-Mitigated` header reference — https://http.dev/cf-mitigated
- Kapravelos et al., *Cloak of Visibility*, IEEE S&P 2016 — https://www.kapravelos.com/publications/cloaking-SP16.pdf
- Longpre et al., *Consent in Crisis* (already in domain-01 brief)
- Mozilla Foundation, *Training Data for the Price of a Sandwich* (Common Crawl representativeness) —
  https://www.mozillafoundation.org/en/research/library/generative-ai-training-data/common-crawl/
- Nagel & Vaughan, *Robots.txt — Crawler Politeness in the Age of GenAI* —
  https://netpreserve.org/resources/WAC25_POSTER17_NAGEL-VAUGHAN.pdf
