# 09 — Guardrails, compliance, and the officials' constraints

The rubric line is *"deterministic; safe"* under skill-format and engineering hygiene. This
is the file that answers "is it allowed to do that?"

Sources: `site-evidence-collector/SKILL.md` (Safety rules), `docs/COMPLIANCE.md`,
`docs/FETCH-STRATEGY.md`, `docs/OFFICIALS-QA.md`.

---

## A. The hard constraints from the brief

### Q1. List every hard constraint the submission must satisfy.

**A.**
- **Recommend-only** — no skill ever alters a live site; everything runs read-only in a
  sandbox.
- **No destructive, authenticated-area, or rate-abusing actions. Respect `robots.txt`.**
- Each skill **portable** (agentskills.io is provider-neutral) and **declaring its tool needs**.
- The manifest **self-contained** — no external service needed to resolve it.
- **Submission zip ≤ 50 MB**, no pre-trained model weights.
- **Audit runtime < 5 minutes** on a standard machine for a typical website.
- **Exactly one entrypoint** in `marketplace.json`.
- A short **`README.md` at the marketplace root** describing each skill and how the entrypoint
  composes them.

### Q2. How is "recommend-only" *enforced* rather than promised?

**A.** Three layers. (1) Only one skill declares network tools at all; the other four declare
`allowed-tools: ""`. (2) That one skill's safety rules permit `GET` and `HEAD` only — never
`POST`/`PUT`/`PATCH`/`DELETE`, never a form submission, never a click, even while rendering.
(3) The prohibited-recommendation gate in the meta-evaluation step removes any action string
that crosses into manipulation.

---

## B. Politeness and robots

### Q3. What exactly does the collector do about `robots.txt`?

**A.** Fetches and parses it **before anything else**, classifies every declared agent, and
**every subsequent request in the procedure obeys it** — including `crawl-delay`. A disallowed
path is not fetched and is recorded as skipped **with that reason**, so the omission is
visible rather than silent.

### Q4. What are the rate limits?

**A.** At most **2 concurrent requests per host**, with a minimum **250 ms** gap — or the
declared `crawl-delay` if it is longer. Static fetches are capped at 20 pages, renders at 3,
internal-link HEADs at 20, off-site anchor HEADs at 8 (one per host).

### Q5. How does it identify itself?

**A.** Honestly — a descriptive User-Agent naming the audit and a contact URL. Differential-UA
fetching (presenting a different identity to get a different response) was considered and
**dropped**; `FETCH-STRATEGY.md` §3 records why.

### Q6. What does it do when it hits a block?

**A.** Nothing clever. **"A blocked resource is evidence, not an obstacle."** No spoofing a
browser to defeat a challenge, no retrying around a 403, no identity rotation. The block is
recorded and reported; a 401/403/429 is *never re-requested*.

### Q7. Then why does the off-site anchor check ever send a second request?

**A.** Only in the opposite direction, and only for a specific known-wrong-answer case: a
**404/405/410/501 from HEAD alone** is not a failure, because many servers mishandle HEAD —
one major social platform answers HEAD with 404 and GET with 200 for the same profile URL. A
single confirming GET is sent before recording `resolved: false`. **This is not retrying
around a block**: a 401/403/429 is never re-requested.

---

## C. Compliance posture

### Q8. What are the four legal lines `COMPLIANCE.md` draws?

**A.** (1) **Public data is the safe side, and it is the side we are on.** (2)
**Circumvention is the bright line, and it is exactly where we stop.** (3) **We never form
the contract that loses these cases** — no account, no accepted terms of service. (4) Indian
law, since this is an Indian competition.

### Q9. What is "the reframe: a block is a finding, not a failure"?

**A.** The compliance posture and the product design agree: a site that blocks the audit
produces a *report about being unreachable*, not an attempt to get in. That converts the one
thing that would push us over a legal line into the thing the report is supposed to say.

### Q10. Is fetching third-party sites for corroboration allowed?

**A.** Yes, per the officials — *"It is okay that it reaches out to some other websites which
may be used for cross corroboration of facts… But don't assume that you would be using some
externally hosted server for doing computation out of band."* What is banned is standing up
our own server or depending on a private API. The shipped audit uses this allowance
**minimally**: only bounded HEAD checks on URLs the site itself declared.

---

## D. The officials' constraints, and what each changed

### Q11. What did the officials' Q&A change about the design?

| Constraint | Quote, in short | What it changed |
| --- | --- | --- |
| **No headless browser** | *"Don't assume a browser or a runtime… anything you can extract out of the DOM"* | The single largest change — ~a third of the engagement half was specified against rendered geometry. D-015, D-018 |
| **No disk, no database** | *"Keep it in memory"* | The collector→analyser handoff became an in-memory bundle |
| **5 minutes is wall-clock, including inference** | *"If I run a prompt it should complete in five minutes"* | Context bloat became a direct runtime cost, not just a style issue |
| **No fixed entrypoint, not a CLI** | *"Assume it's a marketplace which would be installed and then used for answering questions"* | Skills must be **legible and self-describing**; `SKILL.md` prose is graded directly |
| **Context efficiency is a scoring axis** | *"…without bloating the context"* | Validated progressive disclosure |
| **Explicit warning about AI-generated bloat** | *"it tends to overdo things… extra skills which don't add value"* | Made the merge test mandatory rather than optional |

### Q12. What did the officials say they are actually looking for?

**A.** Five things, repeated in different words:
1. **Prioritisation is the differentiator.** *"Not just a laundry list of items… The real
   ingenuity lies in how you order them."*
2. **Beat the frontier-model baseline.** *"The common denominator becomes what the frontier
   models produce… The differentiating factor becomes… your net addition on top of that."*
3. **Vertical-specific insight is rewarded.**
4. **Fixes must map to the findings.** *"Let's say they are disconnected — you identified a
   set of problems, but the fixes are not in line with them."*
5. **Recommendations, not fixes.** *"You won't be generating fixes."*

### Q13. What did they say about bot-blocked sites?

**A.** *"Don't worry about them… we will take care that the sites we evaluate against are
sites which actually allow the agent to do its work."* So graceful degradation is still
correct and still worth keeping — robustness reads well when the marketplace is reviewed
statically — but it is **not a scoring risk** and should not consume more build time.

### Q14. What did they say about false positives?

**A.** *"We have our own in-house expertise around what is actually a false positive versus
what really makes sense. We have our own validation sets."* But deliberately no calibration
guidance: *"A poor outcome is very simple boilerplate architecture with no novelty. A good
outcome is someone who's solved the problem and also gone beyond what's in the brief."*

### Q15. Are scripts mandatory?

**A.** No — *"Totally optional. If you can manage without, if your skill and references can
carry it well enough, why not?"* We ship them anyway, because 32 deterministic checks
expressed only in prose would be neither reproducible nor testable.

### Q16. What runtimes and machine should be assumed?

**A.** Python and Node.js only — avoid Go and niche runtimes; keep packages lightweight,
stdlib preferred; bash/curl assumed available. ~16 GB RAM, CPU only, no GPU. No front end.
One submission per team, no deadline extension. Marking is **relative**: same sandbox, same
sites, same prompts for every submission.

---

## E. Safety invariants, as a checklist

### Q17. Give the one-screen version a reviewer can verify.

**A.**

| Invariant | Where it is enforced |
| --- | --- |
| Only one skill can reach the network | `allowed-tools` frontmatter on all five skills |
| GET/HEAD only | collector safety rules |
| No authentication, no cookies, no paywall circumvention | collector safety rules |
| robots.txt + `crawl-delay` obeyed | step 2 of the collection procedure, `robots_parser.py` |
| ≤2 concurrent per host, ≥250 ms gap | collector safety rules |
| No bot-detection evasion | collector safety rules |
| Off-site requests HEAD-only, ≤8, one per host, declared URLs only | step 7 |
| Hard per-stage time budget, abandon rather than overrun | `budget.stages` |
| No persistent storage; bundle discarded after the run | collector "When to use" |
| No prohibited recommendation reaches the report | meta-evaluation hard-drop gate |
| No live generative-engine query | D-006, LIM-03 |
| Severity never exceeds the evidence strength | D-004, enforced per check |
