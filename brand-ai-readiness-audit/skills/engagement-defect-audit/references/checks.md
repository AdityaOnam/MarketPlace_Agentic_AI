# Engagement Defect Audit — per-check reference

Full detail for each of the eleven checks owned by `engagement-defect-audit`. For the
procedure summary, inputs, the CHK-E-019 duplication note, the CHK-E-023 two-detector
rule, and the CHK-E-024 single-source routing rule, see the parent [`SKILL.md`](../SKILL.md).
Evidence strings, severity rules, FP guards, and suggested actions below are copied
directly from `docs/research/EVIDENCE-LEDGER.md` — they are not re-derived here.

Per **D-008**: every check in this skill detects a defect known to obstruct access or
comprehension. None of them predict bounce rate, dwell time, conversion, or task success —
those are LIM-04 (not observable read-only).

---

## CHK-E-014 — Machine-detectable WCAG failures

**Mechanism:** E — Accessibility failures that are mechanically detectable from static
HTML and computed styles, covering the most prevalent class of barriers. WebAIM Million
(2024) found ≥95.9% of home pages have at least one WCAG failure; the six sub-checks
below are the most common and unambiguous.

**Evidence strength:** HARD-MECHANICAL (sub-checks a–e) / NORMATIVE (sub-check f, contrast)  
**Severity ceiling:** high (a–e), medium (f)

**Sub-checks (evaluate independently, aggregate per page):**
- **(a)** Missing `lang` attribute on `<html>`: check `pages[].lang == null`.
- **(b)** Images with missing alt: check `images[]` where `alt === null` (not `alt === ""`).
  Decorative images with `alt=""` are correct and must not be flagged.
- **(c)** Links or buttons with no text: check `interactive_empty.links_no_text > 0` or
  `interactive_empty.buttons_no_text > 0`.
- **(d)** Form controls without a label: check `form_controls[]` where `has_label === false`
  and `aria_label === null`.
- **(e)** Iframes without a title: check `iframes[]` where `title === null`.
- **(f)** Low colour contrast: inspect `rendered[].computed_styles.contrast_pairs[]` where
  `ratio < 4.5` for normal text (`font_px < 18` and `bold === false`) or
  `ratio < 3.0` for large text (`font_px >= 18` or `bold === true`).

**Evidence emitted (per page, per sub-check type):**
```
Page {url}: {N} accessibility violation(s) of type {type} (e.g. "missing alt on
{N} non-decorative images"). Violates WCAG 2.2 SC {criterion}.
```

**Severity rule:**
- Sub-checks a–e: high per page (hard-mechanical failures that directly block
  screen-reader or browser fallback access).
- Sub-check f (contrast): medium (normative ceiling — WCAG SC 1.4.3 is real but the
  actual perceptual impact on a given user is not measured read-only).

**FP guard:**
- `alt=""` (empty string, not null) is correct for decorative images. Test
  `image.alt === null`, not `!image.alt` or `image.alt.length === 0`.
- An iframe used for audio embedding may have its title in an `aria-label` on a wrapper;
  check `title` only on the `<iframe>` element itself.
- Contrast: only sample pairs from `computed_styles.contrast_pairs[]` where
  `ratio` is present. If the rendered section is unavailable, sub-check f is
  `not_determinable`.

**Not-determinable:** Sub-check f is `not_determinable` if `rendered.status != "ok"` for
the relevant page (JS-SPA where the render pass did not complete).

**Suggested action:** Standard WCAG fixes by type:
- (a) Add `lang="en"` (or appropriate BCP 47 code) to `<html>`.
- (b) Add descriptive `alt` text to every non-decorative image; add `alt=""` to decorative ones.
- (c) Add visible or `aria-label` text to all links and buttons.
- (d) Associate every form input with a `<label>` or `aria-label`.
- (e) Add `title` attribute to every `<iframe>`.
- (f) Increase foreground/background contrast to ≥4.5:1 (normal) or ≥3:1 (large text).
Priority: high (a–e), medium (f).

**Runtime:** low (static HTML + computed-style pass already collected).

---

## CHK-E-015 — Viewport meta missing or zoom-blocking

**Mechanism:** E — A missing viewport meta tag causes browsers to render a mobile page at
desktop width; `user-scalable=no` or `maximum-scale<2` removes the user's ability to zoom,
which is a WCAG hard failure and prevents users from compensating for small text or elements.

**Evidence strength:** HARD-MECHANICAL / NORMATIVE  
**Severity ceiling:** high (zoom block), medium (missing meta, horizontal overflow)

**Observation (per page, 2–3 pages across `pages[]`):**
- Check `pages[].meta.viewport`: absent, or contains `user-scalable=no`, or contains
  `maximum-scale` with a value < 2.
- Check `rendered[].viewports.mobile_375.horizontal_overflow` for layout overflow.

**Evidence emitted:**
```
Page {url}: missing viewport meta tag — page renders at desktop width on mobile.
```
or
```
Page {url}: viewport meta disables user zoom (user-scalable=no or maximum-scale<2).
Violates WCAG 2.2 SC 1.4.4.
```
or
```
Page {url}: horizontal scroll at 375 px viewport width (content wider than screen).
```

**Severity rule:**
- Zoom disabled (`user-scalable=no` or `max-scale<2`): high (hard normative failure,
  WCAG 2.2 SC 1.4.4 Resize Text).
- Missing viewport meta: medium (layout defect, not a hard accessibility block).
- Horizontal overflow only: medium.

**FP guard:**
- Exclude sites identified as `desktop-only` (no `meta.viewport` on any page, and
  `site.archetype` is not `ecommerce` or mobile-oriented — rare but valid).
- `minimum-scale=1` is not a zoom restriction and must not be flagged.
- Horizontal overflow: exclude if the page has a sticky or fixed navigation that
  intentionally protrudes (check for `body_scroll_locked` as a corroborating signal;
  if absent, overflow is the defect).

**Not-determinable:** For horizontal-overflow sub-check: `not_determinable` if
`rendered.status != "ok"` for the page.

**Suggested action:**
- Add `<meta name="viewport" content="width=device-width, initial-scale=1">`.
- Remove `user-scalable=no` and `maximum-scale` constraints.
- Fix responsive CSS so no element overflows the viewport at 375 px.
Priority: high (zoom block), medium (missing meta / overflow).

**Runtime:** low (static meta check) / high for overflow (uses shared render).

---

## CHK-E-016 — Standalone tap targets below WCAG 2.2 minimum

**Mechanism:** E — Interactive elements that are too small are difficult or impossible to
activate accurately with a finger, creating a physical access barrier on touch devices.
WCAG 2.2 SC 2.5.8 (Target Size Minimum) sets the normative floor at 24×24 CSS px for
standalone targets.

**Evidence strength:** NORMATIVE (WCAG 2.2 SC 2.5.8)  
**Severity ceiling:** medium

**Observation (1–2 pages, mobile_375 viewport):** Inspect
`rendered[].viewports.mobile_375.tap_targets[]` where `standalone == true` and
(`w < 24` or `h < 24`).

`standalone` is computed by the collector (BUNDLE-SCHEMA.md Caveat 3): inline text
links that are part of a sentence are exempt under WCAG 2.2 SC 2.5.8, and the collector
encodes this exemption structurally so the analyser does not need layout geometry.

**Evidence emitted:**
```
{N} standalone interactive element(s) are below the WCAG 2.2 SC 2.5.8 minimum
of 24×24 CSS px (smallest: {w}×{h} px, selector: {selector}).
```

**Severity rule:** medium if N ≥ 1 on ≥1 rendered page.

**FP guard:**
- Only flag elements where `standalone == true`. Inline text links (e.g., a word within a
  paragraph that is a hyperlink) are pre-filtered by the collector and will have
  `standalone == false`.
- Check `spacing_px`: if spacing between adjacent targets is ≥ 24 px in all directions,
  the target qualifies under the spacing exception in WCAG 2.2 SC 2.5.8 — suppress.

**Not-determinable:** If `rendered.status != "ok"` for the sampled pages, or if the
render pass was abandoned.

**Suggested action:** Increase target size or padding to at least 24×24 CSS px. For small
icons or compact navigation items, add transparent padding rather than resizing visible
elements. Priority: medium.

**Runtime:** high (uses shared render pass; but no additional rendering cost — reads
pre-computed geometry from the bundle).

---

## CHK-E-017 — Non-descriptive anchor text

**Mechanism:** E — Links with text like "click here", "read more", or "learn more" do not
describe their destination, making them inaccessible to screen-reader users navigating by
link list, and meaningless to AI systems parsing link text for topical signals.

**Evidence strength:** NORMATIVE / THEORETICAL  
**Severity ceiling:** medium

**Observation (2–3 pages):** Count `pages[].links[]` where `text` (or `aria_label`, if
present) matches the non-descriptive pattern list: "click here", "here", "read more",
"more", "learn more", "this link", "details", "info", "click", "tap", "view", "see".
Compute the fraction against total links on the page.

**Evidence emitted:**
```
Page {url}: {N} link(s) ({pct}%) have non-descriptive anchor text
(e.g. "{example}"). Violates WCAG 2.2 SC 2.4.4.
```

**Severity rule:** medium if >10% of links on ≥1 page have non-descriptive text.

**FP guard:**
- If `link.aria_label` is non-null and descriptive, the link passes regardless of
  visible text. Test `aria_label` first.
- Count only links with `internal == true` or links where the destination is within the
  site. External "read more" on a press clipping is lower impact.

**Not-determinable:** n/a (static HTML check; never `not_determinable` unless no pages
were successfully fetched).

**Suggested action:** Replace non-descriptive anchor text with text that describes the
link destination or action (e.g., "Read our privacy policy" instead of "click here").
Use `aria-label` where changing visible text would break layout. Priority: medium.

**Runtime:** low (static link-text scan).

---

## CHK-E-018 — Content-blocking overlay at load

**Mechanism:** C/E — A full-screen overlay present at page load that locks scroll
effectively removes the page's content from view. AI systems fetching a rendered page will
see the overlay, not the content; users with assistive technology may be unable to dismiss
it or navigate past it.

**Evidence strength:** HARD-MECHANICAL / NORMATIVE  
**Severity ceiling:** high

**Observation (2–3 pages, mobile_375 viewport):** Inspect
`rendered[].viewports.mobile_375.overlays[]` for elements where
`viewport_coverage_pct >= 50` **and** `rendered[].viewports.mobile_375.body_scroll_locked
== true`.

**Evidence emitted:**
```
An overlay covering ~{pct}% of the 375 px viewport with scroll-lock is present
at page load on {url}. Content is inaccessible until the overlay is dismissed.
```

**Severity rule:** high if coverage ≥ 50% + scroll locked. Medium if coverage ≥ 50%
without scroll lock (content may be accessible via scroll).

**FP guard (critical):**
- Check `overlay.dismissible_hint`. Suppress when value is `"cookie"` or `"age"` —
  cookie-consent banners and age-verification gates are legal compliance requirements,
  not defects.
- Suppress purely decorative or partially transparent overlays that do not prevent
  reading the underlying content.

**Not-determinable:** If `rendered.status != "ok"` for the relevant pages, or if the
render pass was abandoned. Scroll-triggered modals that do not appear at load are
`not_determinable` (the collector only captures load state).

**Suggested action:** Trigger modals via user interaction (scroll, click, timer after
interaction), not at page load. Remove scroll-lock from any overlay that is not a
cookie or age gate. If an overlay is necessary at load, ensure it is keyboard-dismissible,
does not lock scroll, and covers <50% of the viewport. Priority: high.

**Runtime:** low (reads pre-computed overlay geometry from the bundle; shared render).

---

## CHK-E-019 — Blank first paint without JavaScript

**Mechanism:** C/E — When an AI system or user with JavaScript disabled fetches a page
and receives no content (low word count, no meaningful noscript fallback), the page
appears blank. This directly blocks access for both non-rendering AI retrievers and users
in constrained environments.

**Evidence strength:** HARD-MECHANICAL / CAUSAL  
**Severity ceiling:** high

**Observation:** Compare `pages[].main_text_words` (raw HTTP fetch, no JS) against
`rendered[].main_text_words` for the same URL. Also check `pages[].noscript.present`
and `pages[].noscript.words`.

This check independently recomputes the same raw-vs-rendered gap that
`render-extractability-audit`'s CHK-D-003 also computes. The duplication is deliberate —
analysers are blind to each other by design. The orchestrator handles deduplication when
both fire on a JS-only site.

**Evidence emitted:**
```
Homepage plain HTTP fetch yielded {raw_words} words of main text; no loading
indicator or noscript fallback present. Rendered DOM contains {rendered_words} words.
AI retrievers and no-JS users see effectively no content.
```

**Severity rule:** high if raw words < 50 **and** noscript.words < 50 **and**
rendered words ≥ 200. Medium if raw words < 200 but noscript provides a meaningful
fallback (words ≥ 50).

**FP guard:**
- Suppress if `noscript.words >= 50` — the fallback carries substantive content.
- Suppress if a skeleton-UI pattern is detectable (the rendered page shows a structural
  shell with loading indicators rather than fully blank). The collector's
  `rendered[].h1_count` and `rendered[].main_text_words` together indicate this: if
  rendered has ≥1 h1 but minimal text, it may be a skeleton rather than a gap.
- Do not fire this check if the render pass was abandoned — static HTML alone cannot
  establish the gap direction.

**Not-determinable:** If `rendered.status != "ok"` for the homepage, or if the render
pass was abandoned.

**Suggested action:** Implement server-side rendering (SSR) or static-site generation
(SSG) so the primary content is present in the raw HTTP response. As a fallback, add a
meaningful `<noscript>` block with at least a brief description of the site and
navigation links. Priority: high.

**Runtime:** low (uses data shared with CHK-D-003's render comparison).

---

## CHK-E-020 — Autoplaying media with sound and no pause/stop control

**Mechanism:** E — Audio that plays automatically without user consent disrupts assistive
technology (screen readers announce page content alongside unexpected audio), and is a
normative WCAG violation. Muted autoplay video is excluded — the issue is specifically
unsolicited sound.

**Evidence strength:** NORMATIVE (WCAG 2.2 SC 1.4.2 Audio Control)  
**Severity ceiling:** medium

**Observation (2–3 pages):** Inspect `pages[].media[]` for entries where
`tag ∈ {"video", "audio"}` **and** `autoplay == true` **and** `muted == false`,
and check that `controls == false` (no browser-native pause/stop control exposed).

**Evidence emitted:**
```
{N} video/audio element(s) autoplay with sound and provide no pause/stop
mechanism (WCAG 2.2 SC 1.4.2). Selector(s): {selectors}.
```

**Severity rule:** medium (normative ceiling — WCAG 2.2 SC 1.4.2 is real but the
perceptual impact varies; audio control violations are not a hard access block for
most users).

**FP guard:**
- `video autoplay muted` is correct and common (background decorative video). Only flag
  when `muted == false`.
- If `controls == true`, the user can pause — suppress (browser native controls satisfy
  SC 1.4.2).
- Autoplay media added via JavaScript after load may not appear in `pages[].media[]`;
  if the rendered DOM shows them and the static HTML does not, flag the discrepancy as
  `not_determinable` for this specific element.

**Not-determinable:** If the `<video>` or `<audio>` elements are injected entirely via
JavaScript and the static page has none.

**Suggested action:** Add `muted` attribute to `<video autoplay>` elements (decorative
background video). Remove `autoplay` from `<audio>` elements entirely, or provide a
visible play/pause control. Reference WCAG 2.2 SC 1.4.2. Priority: medium.

**Runtime:** low (static media-element scan).

---

## CHK-E-021 — Images and iframes without explicit dimensions

**Mechanism:** E — Images and iframes without `width` and `height` attributes (or CSS
`aspect-ratio`) cause content reflow as they load: later elements shift position, producing
layout instability. The reflow is mechanical and deterministic from the HTML; the
engagement harm is explicitly unevidenced (Google's own CLS threshold documentation states
there is no perception research behind it).

Per D-008: this is reported as a structural defect detectable from the markup, not as an
engagement outcome prediction.

**Evidence strength:** THEORETICAL  
**Severity ceiling:** medium (≥10 affected elements across ≥2 pages), low otherwise.
**Never higher** — the engagement harm is unevidenced.

**Observation (2–3 pages):** Count `pages[].images[]` where `width_attr === null` **and**
`height_attr === null` **and** `css_aspect_ratio === null`. Similarly count `iframes[]`
with the same pattern.

**Evidence emitted:**
```
{N} image(s)/iframe(s) lack explicit width/height or aspect-ratio CSS, so content
reflows as they load. Structural defect across {page_count} pages.
```

**Severity rule:**
- N ≥ 10 missing-dimension elements across ≥ 2 pages: medium
- N ≥ 3 but below threshold: low
- N < 3: `absent` (below noise floor)

**FP guard:**
- Exclude `<picture>` elements with responsive sources — the `in_picture` field in
  `images[]` identifies these. Responsive `<picture>` images often omit fixed dimensions
  intentionally.
- Require N ≥ 3 before emitting anything (below 3 is noise).
- If the dimensions are present only in CSS (not as attributes), the collector's
  `css_aspect_ratio` field captures this — suppress if present.

**Not-determinable:** `not_determinable` if dimensions are set via JavaScript-generated
inline styles (cannot be read from static HTML).

**Suggested action:** Add `width` and `height` attributes to all `<img>` and `<iframe>`
elements matching their natural or rendered dimensions, or use CSS `aspect-ratio` on the
element. This allows the browser to reserve the correct space before the asset loads.
Priority: medium (if ≥10 elements) / low (otherwise).

**Runtime:** low (static attribute scan).

---

## CHK-E-022 — Missing landmark or heading integrity violation

**Mechanism:** E — Missing `<main>` landmark, multiple or zero `<h1>` elements, and
skipped heading levels all violate document structural conventions. These patterns break
screen-reader navigation and signal to AI systems that the page's content hierarchy
cannot be trusted.

**Evidence strength:** NORMATIVE / PRACTITIONER  
**Severity ceiling:** high (no `<h1>`), medium (skips or missing `<main>`)

**Observation (3–5 pages):** Inspect `pages[].landmarks` and `pages[].headings[]`:
- `landmarks.main == 0`: no `<main>` element.
- Count occurrences of `heading.level == 1` in `headings[]`. Zero or >1 h1: violation.
- Heading level sequence: check for skips (e.g., h2 directly to h4 with no h3).

**Evidence emitted:**
```
Page {url}: {violation description}. Violates structural accessibility conventions
(WCAG 2.2 SC 1.3.1 / 2.4.6).
```

**Severity rule:**
- Zero `<h1>` on ≥1 page: high (a page with no heading is navigationally broken for
  screen-reader users).
- Multiple `<h1>` (>1) or missing `<main>` on ≥1 page: medium.
- Heading level skips on ≥1 page: medium.

**FP guard:**
- Heading skips on user-generated content pages (e.g., blog comments, wiki edits) may
  reflect user-authored content rather than a site-level defect. Suppress on pages where
  `page_type == "other"` and the heading skip is isolated to one heading sequence.
- A page that uses `role="main"` on a `<div>` satisfies the landmark requirement even
  if `<main>` is absent — the `landmarks.main` count covers this if the collector
  inspects `role` attributes.

**Not-determinable:** n/a (static HTML check; `not_determinable` only if pages were
not fetched).

**Suggested action:**
- Add `<main>` (or `role="main"`) to each page to wrap the primary content.
- Ensure exactly one `<h1>` per page naming the page's primary topic.
- Fix heading level skips so the outline is sequential (h1 → h2 → h3).
Priority: high (no h1), medium (other violations).

**Runtime:** low (static heading and landmark scan).

---

## CHK-E-023 — Ad/promo density exceeds 30% of mobile viewport

**Mechanism:** E — When advertising or promotional elements occupy >30% of the visible
mobile viewport, they interfere with content access. The Better Ads Standards (Coalition
for Better Ads, 2022) define 30% mobile / 50% desktop as the empirically-derived
thresholds above which intrusion complaints spike. These are the only published numeric
thresholds applicable mechanically.

**Evidence strength:** CORRELATIONAL / NORMATIVE (Better Ads Standards)  
**Severity ceiling:** medium

**Observation (1–2 pages, mobile_375 viewport):** Read
`rendered[].viewports.mobile_375.ad_area_pct_total`. Also inspect
`rendered[].viewports.mobile_375.ad_regions[].detector` to determine how many
independent detector types fired.

**⚠ Two-detector rule (mandatory FP guard, see SKILL.md):** Collect the set of distinct
`detector` values across all `ad_regions[]` entries. If only one detector type appears
(e.g., only `iframe_thirdparty`), emit `not_determinable` with reason "only one
detection method agrees — insufficient confidence." A finding requires ≥2 distinct
detector types to agree.

**Evidence emitted (when ≥2 detectors agree):**
```
First viewport at 375 px: ~{pct}% of visible area occupied by advertisements
(detected by: {detectors}). Exceeds the Better Ads Standard threshold of 30%.
```

**Severity rule:** medium if `ad_area_pct_total > 30` and ≥2 detector types agree.

**FP guard:**
- Suppress if no ads are detected site-wide (all ad region lists empty across all
  sampled pages) — a clean site should not trigger this check.
- Require ≥2 independent detector types to agree; otherwise `not_determinable`.
- This check is explicitly noted in BUNDLE-SCHEMA.md (Caveat 1) as the most
  false-positive-prone check in the entire marketplace. Apply the two-detector rule
  without exception.

**Not-determinable:**
- Render pass abandoned.
- Only one detector type fires.
- `rendered.status != "ok"` for the sampled pages.

**Suggested action:** Reduce advertising density so no more than 30% of the visible
mobile viewport is occupied by ads (Better Ads Standard threshold). Move dense ad
placements below the fold. Consolidate multiple small ad units. Priority: medium.

**Runtime:** high (uses shared render pass, but no additional rendering cost).

---

## CHK-E-024 — Missing trust signals *(recommendation-only)*

> **⚠ This check must never appear in `findings[]` at any severity.** It ships
> exclusively as a recommendation under the single-source rule (D-004). The envelope
> must carry `"route": "recommendations"` so the orchestrator places it in
> `recommendations[]`. If the supporting sources (P-07.13, P-06.11) are later
> hand-verified and a second independent source is confirmed, update the Evidence Ledger
> first; only then may this check be promoted.

**Mechanism:** E — Commercial and news sites that lack detectable contact information,
organisation name, HTTPS, or byline dates are harder for users and AI systems to assess
as credible. Trust signals are proactive improvements, not defects for which a causal
pathway has been established.

**Evidence strength:** CORRELATIONAL, single-study (single-source rule applies)  
**Ships as:** proactive recommendation only.

**Observation (2–3 pages):** On pages where `page_type ∈ {"home", "about", "contact"}`,
check `contact_signals` for email, phone, and postal_address. Check `site.scheme == "https"`.
Check `pages[].dates` for bylines on article/news pages.

**Evidence emitted (in recommendation, not finding):**
```
Commercial site: no detectable {signal}. Adding {signal} may improve perceived
credibility. (Proactive — not a confirmed defect.)
```

**Suggested action:** Add contact information (email, phone, or postal address) in the
footer. Include the organisation name in the footer. Ensure HTTPS is used site-wide.
Add byline dates to articles and news content. Priority: low.

**FP guard:**
- Only apply to `archetype ∈ {"ecommerce", "saas_marketing", "news_editorial",
  "local_business"}`.
- Do not apply to `archetype ∈ {"personal", "hobby", "portfolio"}`.

**Runtime:** low (static field check).
