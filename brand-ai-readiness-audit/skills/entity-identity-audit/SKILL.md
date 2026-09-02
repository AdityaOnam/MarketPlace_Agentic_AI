---
name: entity-identity-audit
description: Determine whether a site states plainly who it is, marks that identity up so a machine can parse it, keeps it consistent across its own pages, points to the external profiles that let the wider web corroborate it, and dates its time-sensitive content — by reading extracted page text, structured data, and off-site anchor reachability in an evidence bundle. Use as the identity/disambiguation stage of a website audit, covering mechanism D from the brief's appendix (why agreement across the web matters, and the mistaken-identity failure mode).
license: Apache-2.0
allowed-tools: []
---

# Entity Identity Audit

Mechanism D of the brief: a fact repeated consistently across many independent,
easily-found sources is far more likely to be believed and repeated; a claim living in one
spot is fragile, and when several things share a name, a system mixes them up unless
something clearly distinguishes one. This skill is the only analyser that touches off-site
evidence at all — and it audits *the anchoring the site itself provides* for that
corroboration, never corroboration itself. See "Scope boundary" below before treating any
of these seven checks as more than that.

**This skill declares no tools and makes no network requests.** It is a pure function from
an evidence bundle to findings. The off-site HEAD checks in `CHK-D-026` were already
executed by `site-evidence-collector`; this skill only interprets their results.

## When to use

Invoked by `audit-orchestrator` with an evidence bundle. Its findings are one of the two
inputs (with `render-extractability-audit`) into the disambiguation picture the orchestrator
assembles — an unnamed, unmarked-up, off-site-unanchored entity is exactly the shape of
brand a same-named competitor gets confused with.

## Inputs

The `pages` and `anchors` sections of an evidence bundle
(`site-evidence-collector/references/bundle-schema.md`). Reads nothing else — in particular,
never `robots`, `rendered`, or `links`. `anchors` is the only off-site evidence anywhere in
the marketplace; no other skill reads it.

## Output

Zero to seven findings in the standard envelope. Emits `absent` where a check ran clean and
`not_applicable` where an archetype exclusion took a check out of scope (e.g. `CHK-D-025` on
a personal/portfolio site) — distinguishable from `not_determinable`, which means the
evidence needed to judge was itself missing.

## Procedure

1. **Gate on evidence.** If `pages.status != "ok"`, every check reading `pages[]` emits
   `not_determinable` with `pages.reason`. If `anchors.status != "ok"`, `CHK-D-025` and
   `CHK-D-026` do the same with `anchors.reason`. Never infer identity signals from a
   partial page set.
2. **Classify time-sensitivity for `CHK-D-012`.** The bundle supplies `page_type`,
   `dates`, the URL, and `main_text` — not a temporal-sensitivity label; that judgment
   belongs here (`docs/BUNDLE-SCHEMA.md` Caveat 2), not in the collector, because it needs
   page-specific reasoning the collector's per-page extraction doesn't attempt. Classify a
   page `TIME-SENSITIVE` if its `page_type` is `article`, or its URL contains a date/year
   segment, or its `main_text` uses present/future tense about a dated event (a sale
   deadline, an event date, "as of {year}"); classify everything else `EVERGREEN`
   (`about`, `pricing`, `faq`, `product`, `documentation`, `legal`, etc. by default).
3. **Evaluate `CHK-D-006`** (explicit entity definition) on home/about pages: is there a
   sentence in the first 300 words naming the organisation, its category, and its
   function?
4. **Evaluate `CHK-D-007`** (Organization JSON-LD) on the homepage's
   `structured_data.json_ld[]`: present, and which required fields are missing.
5. **Evaluate `CHK-D-008`** (canonical tag correctness) across sampled pages'
   `pages[].canonical`.
6. **Evaluate `CHK-D-012`** using step 2's classification: a `TIME-SENSITIVE` page with no
   `dates.meta_published`, no `dates.visible_dates`, and no `headers['last-modified']`
   fires. **Never raise on a page classified `EVERGREEN`.**
7. **Evaluate `CHK-D-025`** (no declared identity anchors): scan
   `pages[].structured_data.json_ld[].fields_present` for `sameAs` and
   `pages[].outbound_profile_links` on home + about. Any one resolvable anchor found in
   step 8 passes this check regardless of count.
8. **Evaluate `CHK-D-026`** (declared anchors that don't resolve) from `anchors.results[]`,
   **only if `CHK-D-025` did not fire** — an anchor-resolution check is meaningless when no
   anchor was declared in the first place. Treat `resolved: null` (401/403/429) as
   not-determinable per anchor, never as a failure.
9. **Evaluate `CHK-D-027`** (self-inconsistent identity attributes): compare organisation
   name, legal name, phone, and postal address across `pages[].structured_data`,
   `pages[].contact_signals` (footer), and a dedicated contact page, requiring ≥2 observed
   instances before comparing. Ignore pure formatting variance (whitespace, "Ltd" vs.
   "Limited", international phone-prefix notation).
10. **Emit** the envelope for all seven checks.

Full per-check detail lives in [`references/checks.md`](references/checks.md).

## Checks at a glance

| Check | Reads | Strength | Ceiling | Mutually exclusive with |
| --- | --- | --- | --- | --- |
| CHK-D-006 | `pages[].main_text`, `structured_data` | CORRELATIONAL | medium | — |
| CHK-D-007 | `pages[].structured_data.json_ld[]` | THEORETICAL/PRACTITIONER | medium | — |
| CHK-D-008 | `pages[].canonical` | CAUSAL | medium | — |
| CHK-D-012 | `pages[].dates`, `page_type`, URL, `main_text` | THEORETICAL | low | — |
| CHK-D-025 | `pages[].structured_data`, `outbound_profile_links` | CORRELATIONAL | medium | CHK-D-026 (fires instead of it) |
| CHK-D-026 | `anchors.results[]` | HARD-MECHANICAL | high | CHK-D-025 (only runs if D-025 didn't fire) |
| CHK-D-027 | `pages[].structured_data`, `contact_signals` | THEORETICAL | medium | — |

## Scope boundary — what this skill does not, and cannot, check

`docs/research/EVIDENCE-LEDGER.md` declares two limitations under mechanism D that no
read-only, self-contained audit can close without a search or web-scale index API:

- **LIM-01** — whether the wider web actually agrees on the brand's facts. `CHK-D-025` and
  `CHK-D-026` audit only whether the site *declares and successfully anchors* profiles that
  would let corroboration happen — not whether those profiles, or anything else on the web,
  actually corroborate the site's claims.
- **LIM-02** — whether the brand name collides with an unrelated same-named entity
  elsewhere. `CHK-D-027` covers only the site's *internal* self-consistency, which is the
  site-side half of disambiguation, not the collision check itself.

`audit-orchestrator` states both as declared limitations in the final report rather than
omitting them — a report that is silent about what it couldn't check would misrepresent its
own coverage. This skill's job is to make sure the site-side half of disambiguation — the
part that actually is checkable read-only — is done thoroughly, not to gesture at the wider
claim.

## False-positive discipline

`CHK-D-025`/`CHK-D-026` are the one place a 401/403/429 must never read as a broken link —
many identity-profile hosts (social platforms, registries) block automated `HEAD` requests
as a matter of course, and treating that as a dead anchor would punish a site for a third
party's bot policy. `CHK-D-006`/`CHK-D-007` must not fire together as if they were
independent problems: a site with a strong declarative sentence and no JSON-LD, or the
reverse, has one gap, not two — but each is graded on its own evidence, since one plausibly
exists without the other in real markup, not because they're the same defect.
