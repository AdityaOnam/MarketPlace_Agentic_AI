# Proactive recommendations playbook

The rubric rewards suggestions that go *beyond* detected defects. Emit up to
five of these as `severity: "info"`, `proactive: true`, only where relevant to
the site type observed. Never emit one that duplicates a real finding.

Each entry states the **mechanism** — why it moves the needle — because a
recommendation without a causal story is not actionable.

---

## P-01 — Publish a canonical, quotable facts block

**When:** any site.
**Do:** add a single `/about` or `/facts` page carrying the brand's atomic
facts in short declarative sentences — legal name, founding year, HQ, what it
sells, who it serves, pricing model, leadership, contact.
**Mechanism:** assistants build answers from spans they can quote verbatim. A
fact spread across a hero video and a PDF has no quotable span; the same fact
in one clean sentence does. This also gives every other site one consistent
source to copy, which is how corroboration starts.

## P-02 — Make every claim self-contained on the page it lives on

**When:** content sites, docs, blogs.
**Do:** ensure each page restates the entity it is about at least once
("Acme Robotics' Model X…" not "our Model X"), and carries a visible date.
**Mechanism:** retrieval returns *chunks*, not sites. A chunk lifted from
mid-page loses the header context; if the subject only appears in the nav, the
chunk is unattributable and gets dropped.

## P-03 — Build the sameAs identity graph

**When:** any brand with a name shared by other entities.
**Do:** link official profiles (LinkedIn, Crunchbase, Wikidata, GitHub, app
stores) from `Organization.sameAs`, and make each of those profiles link back.
**Mechanism:** disambiguation is a graph problem. Mutual links between
independent sources are what let a system decide which "Apex" you are.

## P-04 — Seed independent corroboration

**When:** brand facts appear only on the brand's own domain.
**Do:** get the same phrasing of the core facts onto sources the brand does
not control — industry directories, a Wikipedia/Wikidata entry if notable,
press coverage, conference bios, partner pages.
**Mechanism:** single-source claims are treated as fragile. Repetition across
unrelated domains is the strongest trust signal a machine has.

## P-05 — Add "last updated" and keep it honest

**When:** pricing, docs, policy, comparison pages.
**Do:** show a visible date plus `dateModified` in schema, and actually revise
the content when you bump it.
**Mechanism:** freshness is a tiebreaker between competing sources. An undated
page loses to a dated rival even when its content is newer.

## P-06 — Answer the questions people actually ask, in their words

**When:** any site.
**Do:** add an FAQ using real query phrasing, with the answer in the first
sentence after the question, marked up as `FAQPage`.
**Mechanism:** question-shaped headings match question-shaped queries, and an
answer-first paragraph is directly liftable as a citation.

## P-07 — Serve a clean text path

**When:** JS-heavy apps.
**Do:** ensure meaningful server-rendered HTML for every indexable route, and
consider publishing plain-text or Markdown equivalents of key docs.
**Mechanism:** many fetchers do not execute JavaScript. Whatever is in the
raw HTML response is the whole of what they see.

## P-08 — Give the visitor one obvious next step per page

**When:** any site.
**Do:** every page ends with a single primary action matched to its intent,
plus 2–4 contextual links to genuinely related pages.
**Mechanism:** arrival from an AI answer is context-free and mid-funnel — the
visitor lands deep, without the journey. A page that assumes prior navigation
strands them.

## P-09 — Preserve context across the journey

**When:** multi-step sites, docs, catalogues.
**Do:** persist breadcrumbs, keep filter/search state in the URL, and make
back/forward and deep links restore the same view.
**Mechanism:** state held only in memory cannot be shared, cited, or returned
to — every reload dumps the visitor at the start.

## P-10 — Declare your crawler policy deliberately

**When:** any site.
**Do:** decide explicitly which AI crawlers may read the site and state it in
`robots.txt`; keep a valid `sitemap.xml` with accurate `lastmod`.
**Mechanism:** the default is often an accident — a blanket block copied from
a template. An explicit policy makes visibility a choice rather than a side
effect.
