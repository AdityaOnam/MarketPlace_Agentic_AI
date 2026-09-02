# Compliance posture — why this audit is lawful, and where the lines are

Answers the question: *we cannot fetch sites that block bots — is that a problem, and is
anything we do legally risky?*

**Short answer: no, and the reason we stop at a block is the same reason the design is
safe. Stopping is the defence, not a limitation.**

> **Not legal advice.** I am not a lawyer and this is not a legal opinion. This is a
> summary of the publicly reported case law and statutes that bear on read-only web
> auditing, written so the submission's design choices can be justified. For anything
> operating commercially or at scale, get actual counsel.
>
> **Verification status (D-003):** every case and statute below is SEARCH-ONLY. Citations
> are given so they can be checked. Nothing in the shipped skills depends on a legal
> claim being precisely characterised here.

---

## 1. The four lines, and which side we are on

| # | Line | Where the risk lives | Where we are |
| --- | --- | --- | --- |
| 1 | Public vs. authenticated | Accessing areas behind a login | **Public only.** `login` pages are never fetched; no credentials are ever supplied |
| 2 | Access vs. circumvention | Engineering a workaround to a technical block | **We stop at the block** and record it |
| 3 | No contract vs. accepted contract | Clicking through ToS, then automating against them | **No account, no click-through, ever** |
| 4 | Polite vs. impairing | Request volume that degrades the service | **Rate-limited, capped, one pass** |

Every one of these was already forced by the brief's own guardrails ("read-only in a
sandbox", "no destructive, authenticated-area, or rate-abusing actions", "respect
robots.txt"). The legal analysis and the rubric point the same way.

---

## 2. Line 1 — public data is the safe side, and it is the side we are on

- **Van Buren v. United States**, 593 U.S. (2021). The Supreme Court read the CFAA's
  "exceeds authorized access" narrowly: liability attaches to obtaining information from
  areas that are **off-limits**, on a gates-up-or-down basis. A terms-of-service breach is
  not, by itself, a CFAA crime.
- **hiQ Labs v. LinkedIn**, 9th Cir. (2022). Scraping **publicly available** data does not
  give rise to CFAA "without authorization" liability. (hiQ still lost on contract — see §4
  — which is precisely the distinction that matters.)
- **Meta Platforms v. Bright Data**, N.D. Cal. (Jan 2024). Summary judgment for Bright
  Data: Meta's terms govern "your use" of the products, and logged-off public scraping was
  not "use". Public, logged-off collection is treated differently from data behind a login.

Our collector fetches only what any browser would receive without signing in. The
procedure never fetches `login`, `signin`, `account` or `register` paths, and holds no
credentials to supply.

---

## 3. Line 2 — circumvention is the bright line, and it is exactly where we stop

This is the important one, and it is where most scraping litigation actually lives.

- **DMCA §1201** (anti-circumvention) risk arises where a site deploys technological
  measures — CAPTCHAs, tokenised access, IP rate limits — and someone engineers a
  workaround.
- **Ryanair v. Booking Holdings**, D. Del. The court indicated a CFAA "intent to defraud"
  theory could be pleaded from conduct undertaken to evade anti-scraping technology,
  specifically naming: rotating or anonymising IP addresses, **changing user-agent
  information**, using CAPTCHA solvers, and entering false login credentials.

**This independently confirms the decision already recorded in
[`FETCH-STRATEGY.md`](FETCH-STRATEGY.md) §3 to cut differential-UA fetching.** That section
rejected UA-spoofing on ethical and measurement-validity grounds. The legal ground is
stronger than both: "changing user agent information" is named in the reported case law as
conduct capable of supporting an intent-to-defraud theory. Sending `User-Agent: GPTBot`
when we are not GPTBot is not a clever trick to be weighed against its usefulness — it is
the single riskiest thing this project could have done, and it is now out on three
independent grounds.

**What we do instead.** One honest user-agent on every request, carrying owner and purpose,
per the IETF crawler best-practices draft (the one source in the fetch-strategy note that
was actually opened and read):

```
Mozilla/5.0 (compatible; BrandAIReadinessAudit/1.0; +<project-url>)
```

When a challenge or block is returned we **record its class and stop**. We never retry
around it, never rotate identity, never solve a challenge. There is no code path in the
collector that could.

---

## 4. Line 3 — we never form the contract that loses these cases

The fact pattern that loses breach-of-contract claims is: register an account, accept terms
banning automation, then automate. hiQ lost on exactly that footing after winning on the
CFAA question — it had agreed to LinkedIn's User Agreement.

We never register, never authenticate, and never click through any agreement. Under
*Bright Data*, logged-off public collection was held not to be "use" governed by those
terms at all.

**robots.txt** is not itself a legally binding contract, and honouring it is not what makes
us lawful. We honour it because (a) the brief requires it, (b) it is the published wish of
the site operator, and (c) ignoring it is the clearest available evidence of bad faith if
anything is ever disputed. It is cheap good faith with real evidentiary value.

---

## 5. Line 4 — Indian law, since this is an Indian competition

The **Information Technology Act, 2000** is the relevant domestic statute:

- **§43** — civil liability for accessing a computer, computer system or network **without
  permission of the owner**. No intent required; compensation up to ₹1 crore.
- **§66** — the same conduct becomes a criminal offence *only* where done with **dishonest
  or fraudulent intent** (mens rea), attracting up to 3 years' imprisonment and/or a fine
  up to ₹5 lakh.

Two observations, offered as reasoning rather than as a legal conclusion:

1. **§43 turns on "without permission."** A page published on the open web and served to
   any HTTP client that asks for it is a materially different thing from a protected system
   accessed without permission. Honouring robots.txt is the operator's own published
   permission signal, and we follow it.
2. **§66 requires dishonest or fraudulent intent.** An auditor that identifies itself
   honestly, obeys the published exclusion rules, requests nothing behind a login, and
   stops the moment it is refused, is close to the opposite of that. Every UA-spoofing or
   challenge-solving technique we declined would have moved us toward the mens rea
   question rather than away from it.

Indian case law specific to scraping is thin, which is a reason for conservatism, not
confidence. Being conservative costs us nothing here.

**Personal data.** We collect page structure, HTTP headers, markup, headings, link targets
and rendered geometry. We do not collect, store, or process personal data, which keeps the
DPDP Act 2023 and GDPR largely out of scope. Any future check that would read personal data
off a page should be treated as a new decision, not an extension of an existing one.

---

## 6. The reframe: a block is a finding, not a failure

"We cannot audit sites that block bots" sounds like a gap. It is not, for three reasons.

1. **Legally, stopping is the whole defence.** The conduct that generates liability in
   every case above is *continuing after refusal* — evading, rotating, spoofing, solving.
   A tool that stops has no exposure to that line of argument because it never crosses it.
2. **For this audit's purpose, the block is the measurement.** If our polite, honest,
   robots-compliant request is refused, that is substantially what an AI assistant's
   retrieval fetcher meets. We are not failing to observe the site — we are observing the
   most consequential fact about it. This is CHK-D-001/D-002 today and the proposed
   CHK-D-028 (robots-allows / edge-blocks) tomorrow.
3. **The rubric rewards it.** "Deterministic; safe" is a graded criterion, and "few false
   positives" is the headline one. A tool that reports `not_determinable` on evidence it
   could not obtain is what safe and deterministic look like. A tool that guesses past a
   block would be manufacturing false positives on a site it never saw — the worst failure
   mode available to us.

---

## 7. What to put in the submission

These cost nothing and make the posture explicit to a grader:

1. **Root `README.md` — an "Intended use and safety" section.** State that the audit is
   designed to be run by a site owner on their own site, or by someone with the owner's
   permission; that it is read-only and recommend-only; that it never authenticates, never
   circumvents access controls, honours robots.txt and rate limits, and stops when refused.
2. **`audit-orchestrator` — the limitations block.** The report already carries
   `limitations[]`. Sites that block automated clients belong there by name, with the block
   class, so the reader understands *why* a section is `not_determinable`.
3. **`site-evidence-collector` — make the guarantee structural, not promised.** It is
   already the only skill declaring network tools (ARCHITECTURE §3). Say plainly in its
   `SKILL.md` that it holds no credentials, performs no retry-around-block, and has no
   identity-rotation path — so the guarantee is auditable by reading one file.
4. **Keep the honest UA and the `+url` contact.** It is what the IETF draft asks for and it
   gives any site operator a way to identify and contact us.

---

## 8. Sources

VERIFIED (opened and read):
- IETF, *Crawler Best Practices* (draft-illyes-aipref-cbcp-00) —
  https://www.ietf.org/archive/id/draft-illyes-aipref-cbcp-00.html

SEARCH-ONLY (case law and statute summaries; verify before relying on any characterisation):
- *Van Buren v. United States*, 593 U.S. (2021)
- *hiQ Labs v. LinkedIn*, 9th Cir. (2022) — https://calawyers.org/privacy-law/ninth-circuit-holds-data-scraping-is-legal-in-hiq-v-linkedin/
- *Meta Platforms v. Bright Data*, N.D. Cal. (Jan 2024) — https://www.fbm.com/publications/major-decision-affects-law-of-scraping-and-online-data-collection-meta-platforms-v-bright-data/
- *Ryanair v. Booking Holdings*, D. Del. — discussed in https://www.quinnemanuel.com/the-firm/publications/the-legal-landscape-of-web-scraping/
- Information Technology Act, 2000 (India), §§43, 66 — https://www.worldlawdigest.com/india/information-technology-act-2000-section-43
- DMCA §1201 circumvention risk in scraping — https://www.quinnemanuel.com/the-firm/publications/the-legal-landscape-of-web-scraping/
