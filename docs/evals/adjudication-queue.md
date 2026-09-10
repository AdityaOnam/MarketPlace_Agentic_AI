# Adjudication queue — model-flagged disagreements, human-decided

`EVALS.md` §1 permits a model to re-read the snapshots and flag check/site cells where it
disagrees with the human label, on one condition: the output is **a queue for human
adjudication, never a label, and never an input to any agreement statistic.** Nothing in
this file has been written into `gold-labels-dev.csv`, and nothing in it should be until a
human has looked.

Raised 2026-09-10 while diagnosing `CHK-D-004`'s false-positive rate (D-030).

---

## Why these are here rather than fixed in code

`CHK-D-006` and `CHK-E-014`'s false positives turned out to be genuine check defects and
were fixed (**D-029**). `CHK-D-004`'s did not — only one of its four was a defect (a misfiled
contact page, fixed in **D-030**). The remaining three look like **imprecision in the gold
labels**, not in the check.

That distinction matters enough to stop at. Continuing to loosen `CHK-D-004` until it agreed
with these three rows would be tuning the product to fit questionable gold data — the same
class of error as D-028's loosened matcher, pointed the other way, and it would show up as
an *improved* score. So: flagged, not fixed, not labelled.

---

## CHK-D-004 — `docs.djangoproject.com` — gold says ABSENT, check fires

**Pages:** `/el/3.1/_modules/` (81 words), `/el/3.1/_modules/django/` (154 words)

**Gold note claims:** "All 10 sampled informational pages … have estimated main_text_words
above 200: minimum 387 (/el/3.1/_modules/)".

**What the evidence shows:** the labeller's 387 and the extractor's 81 are about the *same
URL*. Measured directly against the frozen snapshot `013__el-3-1-modules.html`:
`<main>` contains **52 words**; the whole `<body>` contains **577**. The page is a module
index — a short heading followed by a long list of `django.apps.config`-style link labels.

**The real question:** does link-label text count as content? The extractor counts prose and
gets 81; a human reading the rendered page counts the module names and gets ~387. Both are
defensible; the check has never said which it means. That is a **rubric gap**, and it should
be settled in `checks.md` before either number is called wrong.

---

## CHK-D-004 — `www.smashingmagazine.com` — gold says ABSENT, check fires

**Pages:** `/author/alan-cohen/`, `/author/alexey-kopytin/`, `/author/anastasia-sycheva/` —
66 words each.

**Gold note says:** "Spot-checked the design-principles article (long-form, thousands of
words) and the March wallpapers gallery post (~760 words…) — both well over 200 words."

**Problem:** neither spot-checked page is one of the three that fired. The label generalises
from two long articles to a site whose sampled set also contains three 66-word author
archive pages. On the check's own definition those three *are* thin.

**Suggested resolution:** likely a labelling gap rather than a check defect — but it is the
labeller's call, and it may instead argue author archives are navigational (same question as
the django `_modules` case).

---

## CHK-D-004 — `www.adafruit.com` — gold says ABSENT, check fires

**Page:** `/product/1` (135 words)

**Gold note says:** "I have check all pages and observe all pages has >200 words".

**Problem:** its sibling product pages measure 292 and 401 words; this one measures 135. The
generalisation appears simply not to hold for this page. A product page with 135 words of
description is thin by the check's definition, and this looks like a true positive
mislabelled `ABSENT`.

---

## Standing note on the same pattern elsewhere

The lwn.net gold rows carry a related flag in their own `notes` (calendar and security-alert
index pages under 200 words, labelled `PRESENT`). If the django/smashing cases are resolved
by ruling that index pages are navigational rather than thin, **lwn.net's rows should be
revisited for consistency** — otherwise the corpus will contain both rulings.

---

## CHK-D-002 — `bookshop.org` — gold says ABSENT, check fires (raised 2026-09-10, D-031)

Surfaced by the D-001 parser fix. Previously `CHK-D-001` fired here (wrongly), which
suppressed `CHK-D-002` entirely; with D-001 corrected, D-002 evaluates for the first time
and fires.

**The two gold notes on this site, read together, contradict the D-002 label:**

- The D-001 note says the AI-retrieval agent group is **permitted** at root via `Allow: /$`
  — hence D-001 `ABSENT`. (This was correct, and the parser now agrees.)
- The D-002 note says robots.txt "has an explicit training-class group blocking every major
  training-class crawler at root: `User-agent: GPTBot`…"

Training-class blocked at root **and** retrieval intact is the exact condition `CHK-D-002`
is defined to fire on. By the check's own rule that is `PRESENT`, but the row says `ABSENT`.

**Likely cause:** the label was set while assuming D-001 would fire and suppress this check.
**Suggested resolution:** re-label to `PRESENT`. Not changed here.

---

## CHK-D-010 — `www.heise.de`, `www.sacher.com` — gold PRESENT, check now declines to judge

**These two rows were labelled by a model (this session, 2026-09-10) and are circular.**

D-031 added a language guard: `CHK-D-010`'s three evidence-shape detectors are English-only,
so on a declared non-English page the check now returns `not_determinable` rather than
claiming the page contains no definition, numeric fact, or comparison.

Both sites are German. Both rows are labelled `PRESENT` with the note "*N page(s) lack a
definition/number/comparison sentence*" — and that label was produced **by running those same
English-only regexes**. The gold data therefore encodes the identical defect the check just
had removed, which is why fixing the check made recall *fall* (0.75 → 0.25): two rows that
scored as true positives were only ever agreeing with a bug.

This is the failure mode `EVALS.md` §1's no-model-authored-labels rule exists to prevent,
observed directly rather than in principle. It also implies the risk is not confined to
`CHK-D-010`: any model-authored row on a non-English site may carry the same English-only
assumption.

**Suggested resolution:** both rows re-labelled by a human who reads German, from the frozen
snapshots — or set to `UNMEASURABLE`, which is what the check now says. Not changed here.

**Wider check worth doing:** audit the model-authored rows on `www.heise.de`, `www.asahi.com`,
`www.sacher.com` and `www.thalia.de` for other English-only reasoning.

---

## CHK-E-015 — `franklinbbq.com`, `www.tartinebakery.com` — gold PRESENT, check structurally cannot fire (raised 2026-09-10, D-032)

Both rows are `PRESENT` on the strength of the **overflow sub-check** — a human resized to
375 px and saw a horizontal scrollbar. The tool cannot reach that verdict: `rendered` is
empty for every site in this harness run, so `CHK-E-015`'s overflow branch never executes.
Its viewport-meta branch *did* run and found nothing wrong, correctly.

The check is behaving properly. **The gold schema is what fails here:** `CHK-E-015` has two
sub-checks with different measurability — viewport meta (static, measurable) and 375 px
overflow (rendered, unmeasurable corpus-wide) — and the CSV has one row per check, forcing a
single label to stand for both. `PRESENT` was the honest answer about the site and is
unscoreable against the tool; `UNMEASURABLE` would be honest about the measurement and would
discard a real observation.

This is why `CHK-E-015` shows recall 0.00: two false negatives, both of them the harness
lacking a renderer rather than the check missing anything.

**Suggested resolution:** add a `subcheck` column to the gold CSV (the analyser envelopes
already carry one — `CHK-E-014` uses it to separate its static and contrast judgments), or
rule that a row resting solely on an unmeasurable sub-check is `UNMEASURABLE`. Either way it
is a schema decision, not a label edit. Not changed here.

---

## CHK-E-021 — `www.smashingmagazine.com` — gold says ABSENT, check fires (raised 2026-09-10, D-032)

**Gold note:** "Every `<img>` on the homepage (author photos, wallpaper cat art, logo) has
explicit width+height attributes."

**Verified — and the note is correct about the homepage.** Measured: 25 images on the
homepage, **0** lacking dimensions.

But the check counts across all 12 sampled pages, and the 32 offending elements are
distributed as:

| page | elements lacking width/height/aspect-ratio |
| --- | --- |
| `/2026/02/desktop-wallpaper-calendars-mar…` | **31** |
| `/author/newsletter-team/` | 1 |
| homepage | 0 |

A wallpaper gallery with 31 undimensioned images is exactly the layout-shift case this check
exists for. The label generalises from one clean page to a site that has a page-scale
problem elsewhere — the same pattern as this site's `CHK-D-004` row.

**Suggested resolution:** re-label `PRESENT`. The check looks right. Not changed here.
