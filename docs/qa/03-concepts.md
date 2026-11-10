# 03 — Concept-specific Q&A

The *why* behind the design. These are the questions that separate someone who has read the
README from someone who understands the project.

---

## A. The six mechanisms (the task's own ontology)

### Q1. What are mechanisms A–F, and where do they come from?

**A.** They are the Round-2 appendix's explanation of *how these systems behave* — not a
checklist of what to do. Deriving checks and fixes from them is the job.

| Mech | The claim | Which skill serves it |
| --- | --- | --- |
| **A** — search visibility | A crawler must (1) be let in, (2) be able to read the page, (3) be able to pick out the specific fact. Any one failing ⇒ the page doesn't exist for that system | `crawl-access-audit` |
| **B** — how assistants use sources | Assistants search, fetch a few pages, build the answer from what those pages say. Pages that get picked are easy to *reach, read and quote a clear fact from* | `content-engagement-audit` |
| **C** — how machines read a page | Content assembled only after load, or stated implicitly, is invisible to a program not looking the same way. The more **explicitly and unambiguously** a fact is stated in plain readable text, the more likely it is extracted | `content-engagement-audit` |
| **D** — agreement across the web | A fact repeated consistently across independent sources is believed. A claim in one spot is fragile. Related failure: **mistaken identity** when several things share a name | `entity-identity-audit` |
| **E** — personalization / prior context | Assistants weight prior context about the user; part of the answer depends on who's asking | `content-engagement-audit` |
| **F** — why machines drop content | When the substance isn't available as readable text, a summarizer has little to work with and the important part disappears | `content-engagement-audit` |

### Q2. Why was "by mechanism" chosen as the decomposition axis?

**A.** Three axes were considered.

- **By page type** (home/product/article/contact) — rejected: checks would be duplicated
  across skills, and page-type conditioning is already required *within* each check. It
  would smear one concern across every skill.
- **By pipeline stage** (fetch → parse → judge) — rejected as the *primary* axis: it cuts
  every mechanism into three pieces, so no skill can be reasoned about alone, and a
  finding's evidence would be assembled across three boundaries.
- **By mechanism, with network I/O extracted** — chosen. The brief's own appendix is the
  task's ontology, and each mechanism has a genuinely different evidence type, failure mode,
  and severity semantics.

### Q3. Which mechanism is *not* covered, and is that admitted?

**A.** Mechanism D's actual cross-web half is not covered — LIM-01 and LIM-02. The audit
checks the **anchoring the site itself provides** for corroboration, not whether
corroboration has occurred. Both are declared in every report.

---

## B. Evidence discipline

### Q4. Why does evidence strength cap severity?

**A.** Because the alternative is a report whose urgency is a matter of taste. The officials
said prioritisation is the differentiator — *"the real ingenuity lies in how you order
them."* A deterministic rule from measurement → severity, bounded by how well the claim can
be defended, makes that ordering auditable. It also prevents the single most common audit
failure: presenting a WCAG violation as a conversion claim.

### Q5. Why can a WCAG violation never be stated as a conversion claim?

**A.** Because WCAG is `NORMATIVE` evidence — the *standard is the authority*. It licenses
saying "this violates SC 2.5.8"; it does not license saying "this costs you customers." That
second claim needs field data the audit does not have (LIM-04). This is D-008's whole point.

### Q6. What is "detect defects, don't predict engagement"?

**A.** D-008, confirmed correct by the officials (*"Don't assume that you have analytics.
It's purely on the site content and structure that you have to infer the problems"*). The
engagement half detects **known-obstructive defects** — accessibility failures, zoom
blocking, overlays, autoplay with sound, broken structure. It never predicts bounce rate,
dwell time, scroll depth, or conversion. Those are field outcomes, not observables.

### Q7. Why were checks demoted rather than deleted when their citations failed?

**A.** Two categories were handled differently. `CHK-D-011` (pronoun-saturated claims) and
`CHK-D-013` (near-duplicate content) had every cited source opened by hand; **none discussed
the check's actual claim** — a genuine evidence gap, not a citation mismatch. They were
demoted to recommendation-only rather than cut, because the underlying advice stands on its
own terms even without academic support. `CHK-E-023` was **cut outright** (D-018), because it
was both render-dependent and already the most false-positive-prone row in the ledger.

### Q8. What is the "prohibited recommendations" list and why does it exist?

**A.** A fixed list of advice this marketplace will never emit, each with a documented reason
(D-007), and **mechanically enforced** in the meta-evaluation step:

- hidden or retriever-directed text
- bulk generated content
- `llms.txt` as a substantive fix
- any promise of citation outcomes
- "improve visual design to build trust"
- reading-grade / Flesch targets
- blanket popup removal
- Lighthouse-100 chasing
- "accessible sites convert better"
- the 3-second-bounce myth, the 9.2 mm tap-target figure, above-the-fold rules

It exists because these are exactly the confident, fashionable things a checklist-shaped
system emits, and none of them survives contact with evidence.

### Q9. Why does the `llms.txt` refusal appear in the report at all?

**A.** Because the officials said recommending it is acceptable, so **silence would be
indistinguishable from having missed it**. D-014's resolution: keep the evidence-based
refusal, and state it visibly as LIM-05. That converts a possible perceived miss into a
demonstrated piece of judgement.

---

## C. False-positive discipline

### Q10. Why is false-positive rate treated as the number most likely to sink the submission?

**A.** The rubric asks for detection accuracy *"with few misses and few false positives"*,
and the officials said they have **in-house validation sets** — *"we have our own expertise
around what is actually a false positive versus what really makes sense."* A recall miss is
invisible to a grader; a false positive is visible on every site they run.

### Q11. Give three concrete false-positive guards and what each prevents.

**A.**
1. **`alt=""` is not missing alt text.** Empty alt on a decorative image is *correct* per
   WCAG. The test is `image.alt === null`, not `!image.alt`.
2. **401/403/429 means bot-blocked, not broken.** An off-site anchor that rejects a HEAD
   request records `resolved: null`, never `false`. A 404/405/410/501 from HEAD alone is
   also not a failure — one major social platform answers HEAD with 404 and GET with 200 for
   the same profile URL, so a single GET must confirm before `resolved: false` is recorded.
3. **A training-crawler block is not a defect.** Many organisations block training crawlers
   as considered policy. The retrieval/training split exists precisely so the audit does not
   lecture them about a deliberate choice.

### Q12. What is the base-rate argument, and where does it bite?

**A.** D-009: findings must be conditioned on base rates and page type. The sharpest case is
`CHK-D-007` (Organization JSON-LD): Web Data Commons measured structured data on 44.1% of
domains and the Web Almanac put Organization JSON-LD at 7.16% of pages — **"no JSON-LD" is
the majority condition of the open web.** Its measured 0.50 clean-site FP rate is therefore a
base rate, not a bug, and its severity was capped at `low` for that reason. It was
deliberately left untouched rather than tuned.

### Q13. Why was a link-density detector for index pages rejected?

**A.** It was measured and rejected because `page.links` counts site chrome, so the ratio
just restates thinness — and it would have suppressed a genuinely thin page. A fix that
launders one signal into another is worse than the disagreement it resolves.

### Q14. What is the "unfetchable page read at face value" bug?

**A.** D-023. A page whose own fetch failed was being scored as a page that genuinely had no
content — false-positiving **six to ten checks at once**. The fix: within a section, a page
with `extraction_ok: false` is excluded *per page*, not read as empty. Never infer from a
partial page set what the missing pages would have shown.

---

## D. Composition & architecture

### Q15. Why is the collector the load-bearing boundary?

**A.** Four reasons, in order of how much work each does:

1. **It enforces the runtime budget structurally.** The shared render pass across several
   checks would otherwise be a convention any future check could silently break. Here it's
   impossible to break: analysers have no network tool declared.
2. **It makes analysers deterministic and unit-testable.** Same bundle in, same findings out.
3. **It localises every guardrail** — robots compliance, rate limiting, page caps, timeouts,
   the no-authenticated-areas rule — in one auditable place.
4. **It matches how the eval works.** A frozen snapshot *is* a bundle, so analysers run
   identically against live collection or a fixture.

### Q16. Why five skills and not one?

**A.** A single well-built skill scores fully on the composition rubric line, so this needs a
real answer. The honest one: the collector boundary buys enforceable determinism and an
enforceable budget regardless of analyser count; and `crawl-access-audit` (reads a text file,
emits hard-mechanical verdicts) and `entity-identity-audit` (reads structured data and
cross-page text, emits mostly theoretical/practitioner verdicts) remain genuinely different
in **evidence type and severity semantics** from `content-engagement-audit` and from each
other.

### Q17. Why not eight or ten skills?

**A.** Splitting `entity-identity-audit` into identity / canonical / freshness, or splitting
`content-engagement-audit` per WCAG criterion, produces skills that share the same evidence,
the same severity semantics, and the same fix vocabulary. That is the definition of padding —
and it now has a concrete illustration, because it is exactly the shape of split the merge
test found unjustified and reversed.

### Q18. What is the single strongest argument that the split isn't just taste?

**A.** That **the axis which failed the test didn't survive it.** Six skills became five on
measured evidence, not intuition. A design that never merges anything has never tested its
own boundaries.

### Q19. What does "analysers are blind to each other" mean, and what does it cost?

**A.** No analyser reads another's output; each is a pure function from the bundle. The cost
is that any genuinely cross-check relationship must be reconciled by a layer above. There was
exactly one such relationship (O-1: `CHK-E-019` defers to `CHK-D-003`) — and when the two
checks' owning skills merged, it became in-skill and the cross-skill surface went to zero.

### Q20. If cross-skill suppression is gone, is the orchestrator just a concatenator?

**A.** It was two claims larger than it is now, and the retraction is recorded rather than
hidden. What survives is **genuinely structural**: report assembly (severity ordering, the
site-wide rollup, meta-evaluation) and budget arbitration. Some layer has to sort, dedupe by
page, and translate `budget.stages` into `limitations[]`, whether it composes three analysers
or thirty. That is a narrower claim than the design originally made, and it is the honest one.

### Q21. Why is Step 3 of the procedure kept in the numbering while empty?

**A.** So its absence is a **documented decision rather than a silent gap**. The next finding
that turns out to need cross-analyser reconciliation is exactly the case that would populate
it again.

---

## E. Determinism, degradation, budget

### Q22. Is determinism claimed as a guarantee?

**A.** Carefully, no. *"Same input against the same site state yields the same report"* is a
**design goal in service of reproducibility, not a claim that a live website is a fixed
object."* Where content or origin behaviour changes between runs, the report says so —
`degraded_stages`, `not_determinable`, per-stage timings — rather than presenting one run's
luck as a settled result.

### Q23. How is page sampling made deterministic?

**A.** The sample is seeded from a **hash of the sorted inventory**, never from wall-clock or
random state, and is stratified across `page_type` so per-page-type scoring is possible
downstream.

### Q24. What is the degradation rule, exactly?

**A.** When a stage exhausts its budget it is abandoned, its bundle section is marked
`partial` or `unavailable` with a reason, and collection continues. **Never extend a stage by
borrowing from another.** Analysers must emit `not_determinable` for any evidence that is not
`ok`. *A bundle that says what it could not collect is worth more than one that guessed.*

### Q25. What does the budget actually promise?

**A.** It bounds how long the audit will **wait**, not how fast the site responds. Time spent
waiting on an external origin is outside our control and is *capped by* the clock, not
excluded from it. So the <5-minute figure is a guarantee about the audit's own behaviour, and
`budget.stages[].actual_s` records where the time went so a slow run is attributable rather
than mysterious.

### Q26. Why record a render stage that never started?

**A.** Because `not_determinable` findings are dropped before the report is assembled. Without
a `render_pass` entry marked `abandoned: true` — even at zero elapsed time — a no-browser run
would produce a report that **looks complete while a third of the engagement half never ran**.
Recording the stage is what lets `degraded_stages[]` name the affected checks.

### Q27. Why is the bundle in memory only?

**A.** Two reasons. The officials said *"Don't assume you would be having some database or
some local disk access… Keep it in memory."* And it makes the no-persistent-storage guarantee
real: nothing is cached, and **no run can be influenced by a previous one**.

---

## F. Reporting philosophy

### Q28. Why separate `findings[]` from `recommendations[]`?

**A.** D-012. `findings[]` holds **confirmed defects only**, and `summary` counts from it
alone. `recommendations[]` holds beyond-defect proactive improvements and checks demoted
under the evidence rules. Mixing them would let unproven advice inflate the severity counts —
which is precisely how an audit flatters itself.

### Q29. Why roll up site-wide defects?

**A.** A site template is shared. One unnamed link in a header, or one missing `<main>` in a
layout, otherwise produces one finding per page — **seventeen findings for one fix** on a
twenty-page sample. Every one of them is true and the report is still wrong, because a reader
cannot tell seventeen problems from one problem seen seventeen times. *Ordering cannot fix a
list in which one defect holds seventeen of the slots.*

### Q30. Why is rollup severity the worst, not the average?

**A.** A defect is as serious as its worst instance. Averaging would let a template defect
that is critical on the checkout page get diluted by twelve harmless blog pages.

### Q31. Why does the report say what it could *not* measure?

**A.** Because omitting it silently misrepresents coverage. A reader who sees no finding for
cross-web corroboration would reasonably conclude corroboration is fine. LIM-01…05 and
`degraded_stages[]` make absence of measurement visible rather than inferable.

### Q32. Why are meta-evaluation warnings never silently corrected?

**A.** *"A report that edits itself until its own audit passes is the failure mode this
project is most careful about."* A surviving warning is the system working. The four
hard-drop gates are the only exception, and each one records what it removed.

### Q33. What makes the recommendations more than an issue → fix lookup?

**A.** Three things a lookup table cannot do:
1. **Urgency is capped at the strength of the evidence behind it.**
2. **Wording is conditioned on the site's vertical and page type** — "add a canonical tag"
   means something different on a faceted 10,000-SKU catalogue than on a six-page brochure
   site.
3. **It refuses the fashionable advice a checklist would confidently emit**, mechanically,
   not merely as a promise.

### Q34. What is the "context carry-over" gap the officials raised?

**A.** Satya's airline example: a visitor arriving from a "Delhi to Mumbai" query lands on a
generic page. He framed the whole problem as three stages — *does my site appear → does it
get cited → can I act on that citation, and is it contextual?* Our engagement half is
**entirely stage-agnostic defect detection**. Candidate read-only proxies (deep-link
behaviour, self-contained landing context, query-parameter preservation, title/meta vs
content mismatch) are identified in `OFFICIALS-QA.md` §4 but unproven and unshipped. It is
the clearest "beyond the common denominator" opening left on the table.
