# Engagement checks — full logic

Core assumption: **the visitor arrived deep, from an AI answer, with no
context.** Every check tests whether the page survives that entry.

---

## EN-01 — No usable H1

**Trigger:** no `<h1>`, multiple competing `<h1>`s, or an `<h1>` under 3 words
that names neither the page subject nor the brand — on ≥ 50% of pages.
**Evidence:** `5/8 pages have no <h1>; /pricing's only h1 is "Welcome".`
**Why:** the H1 is the first orientation cue for both the reader and the
retrieval chunker. Without it, a deep-landing visitor cannot tell where they
are, and an extracted chunk has no title to attach to.
**Fix:** one descriptive H1 per page naming the subject, e.g.
"Acme Robotics Pricing" not "Welcome".

## EN-02 — Value proposition absent above the fold

**Trigger:** the first 200 words of body text contain no sentence stating what
the organisation does. Detected by absence of any verb-object pattern near the
brand name and absence of category nouns in the opening block.
**Evidence:** `The first 200 words of the homepage are a slogan ("Think different. Build faster.") and navigation labels; no sentence states what the company sells or who it serves.`
**Why:** both humans and extractors take the opening block as the page's
thesis. A slogan is not a fact — nothing quotable, nothing to orient on.
**Fix:** open with one plain sentence: `<Brand> is a <category> that helps
<audience> <outcome>.` Keep the slogan after it.

## EN-03 — No primary call to action

**Trigger:** no button/link matching action intent (start, try, buy, book,
contact, demo, sign up, download, subscribe) in the main content of ≥ 50% of
content pages.
**Evidence:** `6/8 content pages contain no action link; the only CTA on the site is in the footer.`
**Why:** an AI-referred visitor is mid-funnel and ready to act but has no
journey behind them. A page with no next step ends the session.
**Fix:** one primary action per page matched to that page's intent, visible
without scrolling, plus a secondary lower-commitment option.

## EN-04 — Dead-end pages

**Trigger:** < 3 outbound internal links in main content, excluding global
nav/footer. Exempt `/(contact|privacy|terms|legal|thank-you)`.
**Evidence:** `4/8 pages link to fewer than 3 other pages from their body content; /blog/post-2 has 0 in-content internal links.`
**Why:** deep-landing visitors explore laterally, not via the nav they never
saw. In-content links are also how relevance flows between pages.
**Fix:** add 2–4 contextual links per page to genuinely related content, with
descriptive anchor text (never "click here").

## EN-05 — No hierarchy signal

**Trigger:** URL depth ≥ 2 with no breadcrumb markup, no `BreadcrumbList`
schema, and no visible parent link.
**Evidence:** `/docs/api/auth is 3 levels deep with no breadcrumb element, no BreadcrumbList JSON-LD, and no link to a parent section.`
**Why:** breadcrumbs answer "where am I and what is this part of" — the exact
question a context-free arrival has.
**Fix:** render breadcrumbs on every page below the top level and mark them up
as `BreadcrumbList`.

## EN-06 — State not in the URL

**Trigger:** a listing/filter/tab UI is present (form controls, `role="tab"`,
facet links) but interactive state is not reflected in query params or path.
**Evidence:** `/products renders 6 filter controls whose selections are held in client state only; the URL never changes, so a filtered view cannot be linked, reloaded or cited.`
**Why:** state held only in memory cannot be shared, bookmarked, cited by an
assistant, or returned to — every reload dumps the visitor at the start.
**Fix:** encode filters, tabs, pagination and search in the URL; make those
URLs restore the same view server-side.

## EN-07 — Substance locked in non-text

**Trigger:** ≥ 40% of page area is image/video/canvas while text word count
< 200, or key facts (pricing, specs) appear only in image filenames/alt.
**Evidence:** `/pricing contains 3 images and 74 words of text; the price tiers appear only inside pricing-table.png, which has empty alt text.`
**Why:** a fact inside an image is invisible to extraction *and* to screen
readers and search-in-page. It cannot be quoted, so it cannot be cited.
**Fix:** render facts as real text (HTML tables for pricing/specs); keep images
as illustration only; give every meaningful image descriptive alt text.

## EN-08 — Page assumes prior context

**Trigger:** main content opens with deixis ("we", "our", "this", "it") and the
brand/product name does not appear in the first 100 words or any heading.
**Evidence:** `/features opens "Our platform makes it simple..." — the brand and product names appear nowhere in the first 100 words or in any heading on the page.`
**Why:** retrieval returns *chunks*, not sites. A chunk lifted from mid-page
loses the header; if the subject only lives in the nav, the chunk is
unattributable and gets dropped.
**Fix:** name the entity explicitly at least once per page and per major
section — "Acme's deployment pipeline", not "our pipeline".

## EN-09 — No search affordance

**Trigger:** > 30 distinct internal links discovered and no search input
anywhere.
**Evidence:** `41 internal URLs discovered; no <input type="search"> or search form on any sampled page.`
**Why:** past ~30 pages, browsing stops scaling; a visitor who cannot find the
one page they need leaves.
**Fix:** add site search reachable from every page.

## EN-10 — Images missing alt text

**Trigger:** > 50% of `<img>` lack non-empty `alt`, with ≥ 5 images sampled.
**Evidence:** `47/62 images across 8 pages have empty or missing alt attributes.`
**Why:** alt text is the only textual representation of an image for
assistive tech and for extraction. Missing alt is content that does not exist.
**Fix:** describe the image's information, not its appearance; leave `alt=""`
only for purely decorative images.
