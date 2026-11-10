# 08 — Decision-log Q&A

`docs/DECISIONS.md` is the numbered, dated record of every design decision: what was done,
why, what it cost, and what is still unresolved. This file turns each into a question.

**Format:** *What did D-NNN settle, and why?*

> **Note on numbering.** The log is chronological by decision, not by number — `D-005` sits
> between `D-013` and `D-014` because it was backfilled. `D-028` exists as a decision;
> `CHK-D-028` as a check ID does not.

---

## Foundations (D-001 – D-005)

### D-001 — Task context lives in repo skills, not in chat history
The handout is copied to `docs/round3-handout.pdf`, distilled into the `round3-spec` skill
with a full transcription, and the working method captured in `project-flow`.
**Why:** the rubric rewards precision about the spec — exactly one entrypoint, required schema
fields, guardrails — and that precision is easy to lose to paraphrase drift across sessions.

### D-002 — Research notes are recorded as mechanisms, never as site examples
`RESEARCH.md` records *mechanism → signal → check → evidence shape → severity → FP guard*. **No
domain names, brands, or site-specific selectors enter the repo.**
**Why:** generalization is a rubric line and is "tested by construction"; site-specific notes
invite hard-coding. **Cost:** any check that can only be expressed against a named site is
rejected or generalized before it ships.

### D-003 — Every shipped check must trace to a documented mechanism
A search-only source is a *lead*, not a justification. A check may not ship until at least one
supporting source is `VERIFIED` and **hand-spot-checked by a human**.

### D-004 — Evidence strength caps severity
The full strength vocabulary, plus the **single-source rule**: a check supported by one
unreplicated study may not be a finding at any severity.

### D-005 — The literature review runs as eight parallel domain agents
Each with a fixed per-source schema and a strict anti-fabrication protocol — a real retrieved
URL required, `VERIFIED` vs `SEARCH-ONLY`, peer-reviewed vs industry, causal vs correlational,
**drop rather than guess**. Briefs stored verbatim so the run is reproducible. ~102 sources
across 6 domains.

---

## Scope and posture (D-006 – D-012)

### D-006 — The audit never queries a live generative engine
**Why:** visibility is a distribution across runs, prompts and time; live querying would break
determinism, runtime and reproducibility at once. Reported as LIM-03.

### D-007 — The prohibited-recommendation list, enforced in eval
A fixed list of advice the marketplace will never emit, each with a reason — and the
enforcement is mechanical, in the meta-evaluation step, not a promise in prose.

### D-008 — The engagement half detects defects, it does not predict engagement
Later **confirmed by the officials** as the expected interpretation, not an under-answer.
Reported as LIM-04.

### D-009 — Findings are conditioned on base rates and page type
Web Data Commons measured 2.39B URLs across 37.4M domains, only 16.5M carrying any structured
data. **Absence of a common-but-not-universal feature is not a finding on its own.** Every
check declares the base rate it is judged against; scoring is per page type, never pooled —
because pooling hides the same failure mode.

### D-010 — Evaluation harness backbone
Written against a measured risk: **we author both the checks and the gold labels, so every
matcher weakness fails silently in our favour.** SWE-Bench+ found 31% of "successful" patches
passed on weak tests, collapsing a 12.47% headline to 3.97%. Established frozen snapshots,
site-as-unit-of-analysis, cluster-bootstrap intervals, and the closed label taxonomy.

### D-011 — `NORMATIVE` is a first-class evidence strength, capped at high
WCAG conformance is normative rather than empirical and shouldn't be forced into a
correlational box — but widening a settled ceiling needed its own decision rather than being
absorbed quietly into the ledger.

### D-012 — Proactive recommendations live outside `findings[]`
`findings[]` = confirmed defects; `recommendations[]` = proactive and demoted items;
`limitations[]` = what wasn't measured. The summary counts from `findings[]` alone.

---

## Architecture (D-013, D-015, D-016, D-025)

### D-013 — Six skills, split by mechanism, with network I/O extracted
The original decomposition, made deliberately after the ledger had *pre-committed* everything
to a single `marketplace_auditor` by default. Later revised by D-025.

### D-015 — No headless browser in the grading sandbox: one-sided re-derivation, not silence
The officials confirmed no browser. Rather than let render-dependent checks silently vanish,
`CHK-D-003` and `CHK-E-019` re-derive a **one-sided static signal capped one tier lower**, and
the rest are declared in `degraded_stages[]`.

### D-016 — The JS-only four-way root-cause dedup is removed: proven unreachable
`CHK-D-003` and `CHK-E-019` both require the homepage's main text **<50 words**; `CHK-D-005`
requires **>500** on the same page. Those thresholds cannot both hold. The collapse was dead
code, **provably so from the check definitions** rather than something a corpus had to
discover — removed rather than kept as an untested claim.

### D-025 — Two analysers merged into `content-engagement-audit`
The merge test ran against all 42 available sites and came back **byte-identical**. The
boundary bought nothing measurable, so six skills became five. This is the decision that makes
"why not eight or ten" concrete rather than assumed.

---

## Officials' Q&A fallout (D-014, D-017, D-018)

### D-014 — `llms.txt`: keep the refusal, surface it visibly
The officials said recommending it is acceptable; our evidence says 97% of existing files are
never requested. **Resolution:** keep the refusal and state it as LIM-05, because silently
omitting it is indistinguishable from having missed it.

### D-017 — Phase 4 runs a reduced, single-labeller protocol; D-010's human-scaled components are cut, not deferred
Three of D-010's components were also invalidated by later evidence: the officials said
run-to-run determinism isn't graded; D-015 removed `rendered[]`, halving what a snapshot
contains; and the abstention-calibration metrics were specified against a probabilistic system
these discrete checks aren't. **The cuts are recorded as losses, not rebranded as
simplifications.**

### D-018 — `CHK-E-023` (mobile ad density) is cut
Render-dependent with no static proxy, so it emitted *nothing at all* in a graded run — and it
was already the ledger's most false-positive-prone row. **The ledger row is struck, not
deleted:** a deleted row reads as an oversight, a struck one reads as a decision.

---

## Report shape (D-019)

### D-019 — Findings are rolled up per defect, not per page
Stage B produced 48, 47 and 44 findings on three sites. The cause was **repetition, not
over-detection** — one shared-template defect emitting one finding per sampled page. *Every one
of them was true, and the report was still wrong.* This is the rubric line the officials were
most explicit about.

---

## False positives found by measurement (D-020 – D-024, D-026, D-027)

### D-020 — Four false-positive mechanisms found by the Stage B screen, repaired at source
**Eight of twelve** curated-clean sites fired inside their own clean dimension. Each firing was
traced to the site's actual HTML rather than judged in aggregate — and **the split is the
useful part**: in one case the check was right and *the corpus was wrong* (a site listed as
clean on `entity_identity` turned out to have zero `application/ld+json` blocks; the curation
was an assumption, never verified).

### D-021 — Archetype classifier: a schema-mismatch bug made every JSON-LD signal dead code
Stage B' measured **17% archetype accuracy** with 5 confidently-wrong labels — the dangerous
failure mode, since `unknown` is safe by design but a wrong confident label activates
suppression rules written for a different kind of site. The bug was fixed and **the resulting
accuracy was accepted without further corpus-fitting**, explicitly declining to add path
patterns against the same 36 sites.

### D-022 — Stage C: five flagged checks resolved
Re-measured across the full 34-site corpus, not just the 12-site screen, and each traced to its
actual HTML/regex behaviour. *The count decides which checks are worth tracing; it does not
decide the verdict.* Outcomes included capping `CHK-D-007` at `low` on base-rate grounds,
excluding the homepage from `CHK-D-004`, and demoting `CHK-D-010` and `CHK-E-021` to
recommendation-only.

### D-023 — A failed fetch was scored as a page with genuinely no content
`http://www.gnu.org`'s request failed outright and the report still emitted **six `present`
findings** — "raw fetch contains 0 words", "missing lang attribute", "no h1 element found", "no
rel=canonical found"… The fix: a page with `extraction_ok: false` is excluded per page.
**Found on the adversarial set, before any gold label was written.**

### D-024 — The harness's own crawl-gate ignored every `Allow` rule
`excalidraw.com` returned a 0-URL inventory — not even the homepage. Its robots.txt declares
`Allow: /$`, `Allow: /`, `Allow: /sitemap.xml`, `Disallow: /`. The **shipped** parser computed
`allowed_root: True` correctly; the harness's *separate* crawl decision did not. A useful
reminder that a second implementation of a rule is a second place for it to be wrong.

### D-026 — The negative-control set's missing seventh dimension closed
`CHK-D-025/026/027` were only ever screened incidentally, and `CHK-D-026` had **no clean site
anywhere in the corpus** whose declared anchors were known to resolve. The set went 12 → 15
sites, with **every row verified by fetch before it was written**.

### D-027 — R-1 hand-verification completed; `CHK-D-011` and `CHK-D-013` demoted
Every cited source for both was opened by hand; **none discusses the check's actual claim**. A
genuine evidence gap, not a citation mismatch. Demoted to recommendation-only rather than cut,
since the underlying advice stands on its own terms.

---

## Measurement repairs (D-028 – D-032)

### D-028 — The matching rule drops both evidence-text conditions
Because they pinned all 26 checks at 0.00. The retired gates become **reported diagnostics**
printed under every precision figure, so the loosening is always visible next to the number it
benefits.

### D-029 — Two false-positive mechanisms fixed; three sites voided
`CHK-D-006`'s definition regex accepted exactly one sentence shape; `CHK-E-014` read a hidden
`rel="me"` verification anchor as an unnamed control — *the very construct `CHK-D-025` asks
sites to add*. Three sites voided for evidence mismatch between the snapshot and the audit.

### D-030 — `CHK-D-004` gets a URL fallback; three disagreements go to adjudication
One of four false positives was a real defect (a contact page misfiled as `product`). The other
three are index/listing pages where **the disagreement is with the gold labels, not the check**
— so they went to the queue rather than into a code change. A link-density detector was measured
and **rejected** because it would have suppressed genuinely thin pages.

### D-031 — robots.txt gains RFC 9309 metacharacter support; `CHK-D-010` stops judging pages it cannot read
A `critical`-severity check was reporting a site as *blocking* crawlers it explicitly allowed.
And `CHK-D-010`'s English-only detectors were asserting "no numeric fact" about German text
carrying `Ab 9 €/Monat`. **It also exposed a circularity**: two gold rows had been model-authored
by running the same regexes the check used, so they agreed with a bug.

### D-032 — `CHK-E-015` and `CHK-E-021` diagnosed; neither is a check defect
And the gold CSV's one-row-per-check schema is identified as a **real limitation** — a check
with several sub-checks cannot record per-sub-check truth in one row.

---

## Later phases (D-033 – D-037)

### D-033 — Phase 6: judge-driven fixes across collector, checks, and report shape
An external judge review returned 8 confirmed code bugs and 20 design problems. One —
WAF/blocked-site detection — was **deliberately dropped** per the officials: blocked sites are
out of scope, and the tool's job is to state that a site is unreachable, not to fingerprint the
challenge page.

### D-034 — Archetype classification rebuilt as additive evidence scoring
An 84-site run returned `unknown` for 51 sites (61%) and `brochure` for 28 — **almost every
`brochure` was wrong** (ebay, etsy, booking, linkedin), because `total <= 5 → brochure` fires
whenever *discovery* found five URLs, which is what a JS-rendered homepage looks like. Four
archetypes were added, and bot walls no longer produce labels. *Not yet validated on a blind
list.*

### D-035 — Phase 10 tier 1: honest-reporting fixes
Across `checks_passed`, loci, wording, the doc contract, identity anchors, duplicate pairs, and
unmeasurable content — eight residual defects a static read of a report would still surface.
Verified across 90 reports.

### D-036 — The classifier receives the complete collected evidence contract
The local evaluation driver was reducing each page to six fields before calling the
already-capable classifier, discarding nested JSON-LD, links, title/meta and static content —
making well-sampled SaaS sites `unknown`. The inverse risk was then guarded: **vocabulary alone
cannot establish institutional or SaaS identity**, because vocabulary can describe an article's
topic rather than the site's own nature.

### D-037 — Decoded `go` redirect utilities are excluded from static-page sampling
`?go=https%3A%2F%2F…` could still be selected as a content page. Rejected **only when the
decoded value is URL-shaped** — `?go=5` remains eligible. A selection-only correction: it makes
no requests and changes no robots behaviour.

---

## Meta-questions about the log

### Q. What pattern runs through D-016, D-025 and the ARCHITECTURE §7 tests?
**A.** Claims were written down *as falsifiable* before they were tested, and then two of them
failed and were retracted in the document that made them. A design that never retracts anything
has never tested its own boundaries.

### Q. What pattern runs through D-020, D-023, D-029, D-030 and D-031?
**A.** Every false-positive fix was traced to the site's **actual HTML**, and the outcome was
split into "the check was wrong", "the corpus was wrong", and "the gold label was wrong" —
with the last category sent to adjudication **unchanged** rather than quietly relabelled.

### Q. Which decisions were *cost-recorded* rather than presented as wins?
**A.** D-017 (evaluation components cut, recorded as losses), D-029 (`CHK-D-006` recall fell
0.73 → 0.55 buying precision — **both numbers reported**), D-028 (a loosening labelled as a
loosening), and D-034 (applied but explicitly *not yet validated on a blind list*).
