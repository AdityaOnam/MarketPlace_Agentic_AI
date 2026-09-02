# Derived checklists — Round 3

These are **derived from** the handout (they are not in it). The handout deliberately
provides no checklist of website checks; that part is our own work and lives in the
marketplace skills themselves. What's here is compliance and self-review scaffolding.

## A. Submission compliance (hard gate — run before any packaging step)

- [ ] Zip is of the **marketplace root directory** itself (containing `marketplace.json`
      and every skill folder), not a parent wrapper.
- [ ] `marketplace.json` at the root: has `name`, `version`, `skills[]` with `id` +
      `path` for every skill folder present.
- [ ] **Exactly one** skill has `"entrypoint": true`. Not zero. Not two.
- [ ] Every `path` in the manifest resolves to a real folder containing `SKILL.md`.
- [ ] Every skill folder listed is independently agentskills.io-valid (`name`,
      `description` in YAML frontmatter; body with instructions).
- [ ] Optional sanity check if available: `skills-ref validate ./skills/<folder>`.
- [ ] Root `README.md` exists and describes **what each skill does** and **how the
      entrypoint composes them**.
- [ ] Manifest is **self-contained** — resolving it needs no external service.
- [ ] Zip ≤ 50 MB; no pre-trained model weights bundled.
- [ ] Nothing in the package requires network credentials or private endpoints to run.

## B. Safety / guardrail gate (every skill, every script)

- [ ] Recommend-only: no skill mutates a live site, submits forms, posts, or logs in.
- [ ] Read-only, sandbox-safe operations only.
- [ ] `robots.txt` fetched and respected before crawling; disallowed paths skipped.
- [ ] No authenticated areas; no paywall/login bypass.
- [ ] Rate limiting / polite crawl delay; bounded page count; no rate-abuse.
- [ ] Bounded total runtime: **< 5 minutes** for a typical website on a standard machine.
      Every crawl loop has an explicit page cap and per-request timeout.
- [ ] Each `SKILL.md` **declares its tool needs** (allowed-tools).
- [ ] Deterministic: same site + same inputs ⇒ same findings and severities.

## C. Report-schema gate (entrypoint output)

- [ ] Top level: `site`, `audited_at` (ISO-8601 UTC), `summary`.
- [ ] `summary` carries `total_findings` plus counts by severity; counts **equal** the
      actual findings array (no drift).
- [ ] Every finding has: `id`, `title`, `severity`, `evidence`, `suggested_action`.
- [ ] `suggested_action` has at least `summary` and `priority`.
- [ ] `evidence` is **concrete and quantitative** where possible ("0/12 product pages
      contain schema.org markup"), never a restatement of the title.
- [ ] Severity vocabulary is fixed and documented; used consistently across skills.
- [ ] Findings are stably ordered (e.g. by severity then id) so runs are comparable.
- [ ] Beyond-problem **proactive recommendations** are present and clearly distinguished
      from defect-driven findings.
- [ ] Report is readable by a **non-expert** — each suggested action says what to change
      and how.

## D. Coverage gate (both halves of the problem)

- [ ] **Off-site discoverability** covered: reachability/crawl admission, machine
      readability of the page, extractability of specific facts, corroboration across the
      wider web, entity disambiguation, freshness.
- [ ] **On-site engagement** covered: what happens to a visitor who *does* arrive.
- [ ] Each check traces back to a **mechanism** in the appendix (A–F), not to a
      memorized site quirk.
- [ ] Every check states its **false-positive guard** — the condition under which the
      finding must *not* be raised. (Rubric penalizes false positives explicitly.)

## E. Generalization self-test (no example sites are given)

- [ ] No hard-coded domains, brand names, or site-specific selectors anywhere in the
      skills or scripts.
- [ ] Checks degrade gracefully: missing sitemap, JS-only site, tiny site, huge site,
      non-English site, SPA, blocked crawler — each has defined behavior, not a crash.
- [ ] Absence of a signal is distinguished from **inability to measure** it (report
      "not determinable" rather than a false finding).
- [ ] Dry-run the entrypoint mentally against 3 wildly different site archetypes
      (docs site, e-commerce, single-page marketing site) and confirm the findings would
      be sensible for each.

## F. Composition gate (marketplace design)

- [ ] Each non-entrypoint skill owns **one concern**; its name and description say which.
- [ ] No two skills duplicate the same check.
- [ ] The entrypoint's job is genuinely **composition** — it defines inputs, invokes the
      others, merges, dedupes, prioritizes, and emits the single report.
- [ ] Decomposition is defensible as separation of concerns, not padding. If a skill
      can't justify its own existence in one sentence, merge it.
- [ ] `SKILL.md` files are **lean**; detailed checklists live in `references/`,
      executable checks in `scripts/` (progressive disclosure).
