# 01 — Basics

Plain questions with plain answers. If you can answer everything here, you can explain the
project to anyone in five minutes.

---

### Q1. What is this project, in one sentence?

**A.** An **Agent Skill Marketplace** called `brand-ai-readiness-audit` that takes a website
URL and produces a single structured JSON report explaining why AI assistants can't find,
read or correctly cite that brand, and why visitors who do arrive hit obstacles — every
finding backed by evidence, with a prioritized suggested fix. *(→ `brand-ai-readiness-audit/README.md`)*

### Q2. What competition is it for, and which round?

**A.** Adobe University Hackathon 2026, **Round 3 — "Build the Agent Skill Marketplace."**
416 teams reached this round. It is a take-home round, and AI assistance is explicitly
allowed. *(→ `.claude/skills/round3-spec/SKILL.md`, `docs/OFFICIALS-QA.md`)*

### Q3. How does Round 3 relate to Round 2?

**A.** Round 2 tested the reasoning *on paper*: why a brand is invisible, stale, or bouncing
in AI apps. Round 3 tests whether that reasoning can be **encoded into reusable agent
skills**, so a general agent pointed at any website can run the audit automatically.

### Q4. What exactly is submitted?

**A.** A zip of the marketplace root directory — `brand-ai-readiness-audit/` — containing
`marketplace.json`, every skill folder, and a root `README.md` describing what each skill
does and how the entrypoint composes them. Everything else in the repo (research, harness,
decision log) is the evidence trail, not the deliverable.

### Q5. What are the two halves of the problem it must cover?

**A.**
1. **Off-site discoverability** — why the brand isn't found or cited by AI assistants.
2. **On-site engagement** — why visitors who do arrive don't stay.

Both must be covered by the entrypoint's final report.

### Q6. How many skills are in the marketplace, and what are they?

**A.** Five.

| Skill | Role |
| --- | --- |
| `audit-orchestrator` | **Entrypoint.** Drives the run, assembles and self-checks the report |
| `site-evidence-collector` | The only skill with network access; emits the evidence bundle |
| `crawl-access-audit` | robots.txt / AI-crawler policy (2 checks) |
| `content-engagement-audit` | Content substance + on-page defects (17 checks) |
| `entity-identity-audit` | Who-are-you, structured data, identity anchors (13 checks) |

### Q7. How many checks are there?

**A.** **32**, disjoint — no check is owned by two skills. The authoritative list is the
`CHECK_TITLES` dictionary in
`skills/audit-orchestrator/scripts/compose_report.py` (verified: 32 entries).

### Q8. Which skill is the entrypoint, and how does a runtime know?

**A.** `audit-orchestrator`, marked `"entrypoint": true` in `marketplace.json`. Exactly one
skill may carry that flag — it is a hard rule of the contest's manifest convention.

### Q9. What are the inputs?

**A.** `target` (a URL or bare domain, required) and `budget_s` (optional, default `300` —
the hard ceiling on collection time).

### Q10. What is the output?

**A.** One JSON report: `site`, `audited_at`, `preamble`, `summary`, `findings[]`,
`recommendations[]`, `checks_passed[]`, `strengths[]`, `limitations[]`, `degraded_stages[]`,
`top_priorities[]`, `meta_evaluation`. The contest's required floor is
`site` + `audited_at` + `summary` + `findings[]` with `id`/`title`/`severity`/`evidence`/
`suggested_action`; everything else is an allowed extension. *(→ `references/report-schema.md`)*

### Q11. Does it ever change the website it audits?

**A.** No. **Recommend-only** is a hard constraint of the brief and of the design: `GET` and
`HEAD` only, never `POST`/`PUT`/`PATCH`/`DELETE`, never a form submission, never a click.
Suggested actions are recommendations for a human, never applied changes.

### Q12. What is the runtime limit?

**A.** Under **5 minutes** wall-clock for a typical site — and per the officials, that
includes model inference time, not just fetching. The collector enforces it with a hard
per-stage budget: robots+discovery 15s, static fetches 45s, render pass 75s, internal links
25s, off-site anchors 20s, plus an 80s reserve.

### Q13. What happens if a site is too slow to finish in time?

**A.** The affected stage is **abandoned**, its bundle section is marked `partial` or
`unavailable` with a reason, and collection continues. The report then says which checks
could not be evaluated. *A slow site produces a partial report on time, never a complete
report late.*

### Q14. What is the size limit?

**A.** The submission zip must be **≤ 50 MB**, with no pre-trained model weights. The
marketplace is Python **stdlib-only** with a hand-built HTML tree, so nothing heavy is
bundled.

### Q15. What language is the check logic written in, and why stdlib-only?

**A.** Python 3, stdlib-only. No `pip install` step means the marketplace is self-contained
and portable — the officials said to assume Python and Node.js runtimes and to keep packages
lightweight. HTML parsing is a hand-built DOM tree on `html.parser` rather than a bundled
dependency.

### Q16. Do I run it as a CLI?

**A.** No — and deliberately not. The officials said: *"Don't assume that you have to provide
some sort of a CLI. Assume it's a marketplace which would be installed and then used for
answering questions."* The marketplace is loaded into an agent harness and invoked with a
prompt. `harness/` is a local driver for *our* evaluation only, and is git-ignored — it is
not part of the submission.

### Q17. How does a run actually proceed, end to end?

**A.** Seven steps in `audit-orchestrator/SKILL.md`:

1. **Collect** — invoke `site-evidence-collector` once; get the evidence bundle.
2. **Analyse** — run the three analysers against that bundle, in parallel; they are blind to
   each other.
3. **Cross-skill suppression** — intentionally empty (D-025).
4. **Root-cause dedup** — removed as provably unreachable (D-016).
5. **Separate** findings from recommendations from limitations; **5b** roll up site-wide defects.
6. **Assemble** — sort by severity then check ID, count the summary, record the archetype.
7. **Meta-evaluate** — a self-check over the finished report; warnings are reported, not
   silently corrected.

### Q18. Why is there a separate "collector" skill at all?

**A.** Because it is the **load-bearing boundary**. It is the only skill with network tools
declared, which makes three guarantees structural instead of promised: the read-only rule,
the time budget, and the determinism of every analyser (same bundle in → same findings out).
Analysers literally cannot fetch — they have no tool to do it with.

### Q19. What does "evidence bundle" mean?

**A.** One in-memory JSON document with sections `site`, `robots`, `discovery`, `pages[]`,
`rendered[]`, `links`, `anchors`, `budget`. The collector builds it; every analyser reads it
read-only and may not extend it. It is discarded at the end of the run — there is no cache
and no persistent store anywhere in the marketplace.

### Q20. What does the audit deliberately *not* measure?

**A.** Five declared limitations, always present in every report:

| ID | What is not measured |
| --- | --- |
| LIM-01 | Whether the wider web actually agrees with the brand's own claims |
| LIM-02 | Whether the brand name collides with a same-named entity elsewhere |
| LIM-03 | Whether any AI assistant currently cites the brand |
| LIM-04 | Field engagement outcomes — bounce, dwell, scroll depth, conversion |
| LIM-05 | `llms.txt` — deliberately not recommended as a substantive fix |

### Q21. Why is `llms.txt` refused?

**A.** A 137k-domain measurement found **97% of existing `llms.txt` files were never
requested**. Recommending it would be advice with no measured mechanism. The officials said
recommending it is acceptable, so silence would read as a miss — hence LIM-05 states the
refusal *visibly*, with the reason (D-007, made visible by D-014).

### Q22. Has it actually been tested, or just designed?

**A.** Measured. 624 gold-label cells across 24 dev sites hand-labelled from frozen
snapshots before seeing tool output; 15 negative-control sites; 6 adversarial sites; a
leave-one-skill-out ablation and a merge test on 36 real sites; k=3 stability on 5 live
sites. Details in [07-evaluation.md](07-evaluation.md).

### Q23. Who built it?

**A.** Aditya Onam ([@AdityaOnam](https://github.com/AdityaOnam)) — architecture, research,
skill authoring, evaluation harness, packaging; with Aditya Gupta
([@code-epic-adi](https://github.com/code-epic-adi)) and Varada Patel
([@Varada2908](https://github.com/Varada2908)) contributing.

### Q24. What licence?

**A.** Apache-2.0, declared in each `SKILL.md` frontmatter.

### Q25. What is the single most distinctive thing about this submission?

**A.** That it refuses to assert what it cannot support. Severity is capped by evidence
strength; checks with unverifiable citations were demoted to recommendations rather than
quietly kept; the report declares what it could not measure; and the self-check reports
warnings rather than editing the report until it passes its own audit.
