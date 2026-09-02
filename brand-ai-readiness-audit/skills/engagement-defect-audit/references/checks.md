# Check reference — engagement-defect-audit

Full per-check detail for the eleven checks this skill owns. Sourced directly from
`docs/research/EVIDENCE-LEDGER.md`; if the two ever disagree, the ledger wins and this file
is stale.

---

## CHK-E-014 — Machine-detectable WCAG failures

- **Mechanism**: E — these five subtypes are the accessibility failures with the highest
  measured prevalence on the open web and require no human judgment to detect.
- **Strength**: `HARD-MECHANICAL` (a–e) / `NORMATIVE` (contrast). Ceiling: `high` (a–e),
  `medium` (contrast).
- **Reads**: `pages[].lang`, `pages[].images[].alt`, `pages[].interactive_empty`,
  `pages[].form_controls[].has_label`/`aria_label` (3–5 pages); `rendered[].
  computed_styles.contrast_pairs`.
- **Subtypes and severity**: (a) missing `lang` attribute — `high`. (b) `<img>` missing
  `alt` (and not decorative) — `high`. (c) empty links/buttons with no accessible name —
  `high`. (d) unlabelled form input — `high`. (e) contrast ratio below WCAG AA threshold for
  the pair's font size/weight — `medium`.
- **Evidence**: `Page {URL}: {N} accessibility violation(s) of type {type}.`
- **FP guard**: `alt=""` is correct and expected for decorative images — never flagged.
- **Not-determinable**: contrast subtype only, when the page is a JS-SPA and `rendered`
  isn't `ok` → `not_determinable`.
- **Action**: standard WCAG remediation per violation type — add `lang`, add descriptive
  `alt` text, give every interactive element an accessible name, label every form control,
  raise contrast to the AA threshold for the text's size and weight.
- **Runtime**: low.

## CHK-E-015 — Viewport blocking

- **Mechanism**: E — a page that blocks pinch-zoom or overflows horizontally on a phone is
  mechanically harder to read, independent of content quality.
- **Strength**: `HARD-MECHANICAL`/`NORMATIVE` (WCAG 1.4.4 — Resize Text). Ceiling: `high`
  (zoom block), `medium` (missing meta / overflow).
- **Reads**: `pages[].meta.viewport` (2–3 pages); `rendered[].viewports.mobile_375.
  horizontal_overflow`.
- **Severity rule**: `high` if `viewport` contains `user-scalable=no` or
  `maximum-scale` &lt; 2. `medium` if the `viewport` meta is missing entirely, or if
  `horizontal_overflow == true` at 375px.
- **Evidence**: `Missing viewport meta` / `disables user zoom` / `horizontal scroll`.
- **FP guard**: exclude sites explicitly built desktop-only (no responsive breakpoints
  anywhere, a deliberate scope choice, not a defect to flag here). `minimum-scale=1` alone
  is fine — only the zoom-blocking and undersized-maximum-scale patterns fire.
- **Not-determinable**: overflow subtype only, if the headless render didn't complete →
  `not_determinable`.
- **Action**: add a standard responsive viewport meta tag; remove any zoom-blocking
  attributes; fix the CSS causing horizontal overflow.
- **Runtime**: low (meta check) / high (overflow, reads the shared render pass).

## CHK-E-016 — Small tap targets

- **Mechanism**: E — a standalone interactive element smaller than the WCAG 2.2 minimum is
  mechanically harder to activate on a touchscreen.
- **Strength**: `NORMATIVE` (WCAG 2.2 SC 2.5.8 — Target Size Minimum). Ceiling: `medium`.
- **Reads**: `rendered[].viewports.mobile_375.tap_targets[]` (1–2 pages) — `w`, `h`,
  `standalone`, `spacing_px`, all collector-computed.
- **Severity rule**: `medium` if one or more `standalone: true` targets have `w < 24` or
  `h < 24` CSS px.
- **Evidence**: `{N} standalone interactive elements are below WCAG 2.2 SC 2.5.8 minimum.`
- **FP guard**: inline text links are exempt under SC 2.5.8 and are marked
  `standalone: false` by the collector — never flagged here. Targets with adequate
  `spacing_px` from neighbours may also be exempt per the same criterion's spacing
  alternative; treat `standalone` as already encoding this.
- **Not-determinable**: headless render didn't complete → `not_determinable`.
- **Action**: increase the target's touch area (via padding, not necessarily visible size)
  to at least 24×24 CSS px, or ensure adequate spacing from neighbouring targets.
- **Runtime**: high (reads the shared render pass).

## CHK-E-017 — Non-descriptive anchor text

- **Mechanism**: E — "click here" and "read more" carry no information out of context,
  which is exactly the context an assistant summarising or extracting a link loses.
- **Strength**: `NORMATIVE` (WCAG 2.4.4 — Link Purpose) / `THEORETICAL`. Ceiling: `medium`.
- **Reads**: `pages[].links[].text`, `aria_label` (2–3 pages).
- **Severity rule**: `medium` if &gt;10% of a page's links use non-descriptive text
  ("click here", "read more", "learn more", "here", bare "link").
- **Evidence**: `{N} links ({pct}%) have non-descriptive anchor text.`
- **FP guard**: a link with a non-descriptive visible text but a descriptive `aria-label`
  is excluded — the accessible name is what matters.
- **Not-determinable**: n/a (static text always available if the page is).
- **Action**: replace generic link text with text that describes the destination or
  action, standalone and out of context.
- **Runtime**: low.

## CHK-E-018 — Content-blocking overlay at load

- **Mechanism**: C/E — an overlay covering most of the viewport with the page scrolled-lock
  underneath it, present the instant the page loads, blocks access to everything below it
  before the visitor has done anything.
- **Strength**: `HARD-MECHANICAL`/`NORMATIVE`. Ceiling: `high`.
- **Reads**: `rendered[].viewports.mobile_375.overlays[]` (`z_index`,
  `viewport_coverage_pct`, `dismissible_hint`), `body_scroll_locked` (2–3 pages).
- **Severity rule**: `high` if an overlay has `z_index >= 999`,
  `viewport_coverage_pct >= 50`, and `body_scroll_locked == true`, all present at load
  (not after a scroll or delay trigger).
- **Evidence**: `An overlay covering ~{pct}% of viewport with scroll-lock is present at
  load.`
- **FP guard**: **suppress** where `dismissible_hint` is `cookie` or `age` — a
  cookie-consent banner or an age gate is a required or reasonable interstitial, not a
  defect, even though it matches the same geometric pattern.
- **Not-determinable**: a scroll- or delay-triggered modal isn't observable from a
  load-time snapshot → `not_determinable`, not "absent" (it may exist and simply not have
  fired yet).
- **Action**: trigger promotional or newsletter overlays on user interaction (scroll depth,
  exit intent, a delay past first paint) rather than immediately at load; remove the
  scroll-lock regardless of trigger timing.
- **Runtime**: low (reads the shared render pass; no extra cost).

## CHK-E-019 — Blank first paint, no fallback

- **Mechanism**: C/E — a visitor who arrives before JavaScript finishes executing sees
  nothing, and if there's no server-rendered fallback or loading indicator, "nothing" reads
  as "broken," not "loading."
- **Strength**: `HARD-MECHANICAL`/`CAUSAL`. Ceiling: `high`.
- **Reads**: `pages[].main_text_words`, `pages[].noscript` vs. `rendered[].
  main_text_words`, homepage. Computed independently of `render-extractability-audit`'s
  `CHK-D-003` (same underlying comparison, different skill — see `SKILL.md`).
- **Severity rule**: `high` if the raw-vs-rendered gap is ≥50% **and** no `noscript`
  fallback with substantive content **and** no skeleton/loading-state markup is present.
- **Evidence**: `Homepage: plain HTTP fetch yielded {words} words; no loading indicator or
  noscript present.`
- **FP guard**: suppress if `noscript.words > 50` (a working fallback exists), or if
  skeleton-UI markup (placeholder elements typically classed `skeleton`/`shimmer`/`loading`)
  is present in the raw HTML — a deliberate loading state, not a blank page.
- **Not-determinable**: headless render didn't complete → `not_determinable`.
- **Action**: implement server-side rendering or static generation, or at minimum a
  meaningful loading state and a substantive `noscript` fallback.
- **Runtime**: low (shares the render pass with `CHK-D-003`; no additional cost).

## CHK-E-020 — Autoplaying media with sound

- **Mechanism**: E — unmuted autoplaying audio or video is a direct, immediate obstruction
  the moment the page loads, with no user action involved.
- **Strength**: `NORMATIVE` (WCAG 2.2 SC 1.4.2 — Audio Control; re-grounded from a
  single-study effect size per D-011/R-3). Ceiling: `medium`.
- **Reads**: `pages[].media[]` (`tag`, `autoplay`, `muted`, `controls`, `loop`), 2–3 pages.
- **Severity rule**: `medium` if a `<video>` or `<audio>` element has `autoplay: true`,
  `muted: false`, and no pause/stop control (`controls: false` and no evident custom
  control).
- **Evidence**: `{N} video/audio element(s) autoplay with sound and no pause/stop
  mechanism (WCAG 2.2 SC 1.4.2).`
- **FP guard**: `<video autoplay muted>` is explicitly fine and never flagged.
- **Not-determinable**: media element added dynamically via JS after the collector's
  static parse → `not_determinable` if `rendered` wasn't consulted for this page.
- **Action**: add `muted` to autoplaying video, or remove autoplay from audio entirely and
  require explicit user activation.
- **Runtime**: low.

## CHK-E-021 — Missing image/iframe dimensions (structural CLS cause)

- **Mechanism**: E — an `<img>` or `<iframe>` with no reserved space causes the layout to
  shift when it loads; the shift itself is mechanical, but the engagement harm from that
  shift is not evidenced (Google's own CLS threshold documentation states it has no
  perception research behind it — domain 07).
- **Strength**: `THEORETICAL`, one coherent label per R-3 (not `HARD-MECHANICAL`, since the
  claim being graded is the unevidenced harm, not the mechanical reflow). Ceiling: `medium`,
  **and never higher regardless of how many elements are affected**.
- **Reads**: `pages[].images[]` (`width_attr`, `height_attr`, `css_aspect_ratio`), 
  `pages[].iframes[]` (`width_attr`, `height_attr`), 2–3 pages.
- **Severity rule**: `medium` if ≥10 affected elements appear across ≥2 pages; `low`
  otherwise (fewer elements, or all on one page). Requires N≥3 to fire at all.
- **Evidence**: `{N} image(s)/iframe(s) lack explicit width/height or aspect-ratio, so
  content reflows during load.`
- **FP guard**: exclude responsive `<picture>` elements, which manage their own reflow
  behaviour correctly by design.
- **Not-determinable**: CSS-computed dimensions couldn't be resolved (e.g. dimensions set
  entirely by an external stylesheet the collector didn't parse) → `not_determinable`.
- **Action**: add explicit `width`/`height` attributes or a CSS `aspect-ratio` to reserve
  layout space before the resource loads. Frame the suggested action as "this reflows the
  layout," never as "this hurts engagement" — the latter claim isn't supported.
- **Runtime**: low.

## CHK-E-022 — Missing landmark/heading integrity

- **Mechanism**: E — a page with no `<main>` landmark, zero or multiple `<h1>` elements, or
  heading levels that skip, breaks the structural navigation both assistive technology and
  a machine reader rely on to understand a page's organisation.
- **Strength**: `NORMATIVE`/`PRACTITIONER`. Ceiling: `high` (no h1), `medium` (skips/missing
  `<main>`).
- **Reads**: `pages[].landmarks` (`main`, `nav`, `header`, `footer` counts),
  `pages[].headings[]` (level, order), 3–5 pages.
- **Severity rule**: `high` if `landmarks.main == 0` or the page has zero or more than one
  `<h1>`. `medium` if heading levels skip (e.g. h2 directly to h4) or `<main>` is missing
  but an `<h1>` is present and unambiguous.
- **Evidence**: `Violation: {description}. Violates structural conventions.`
- **FP guard**: exclude heading-level skips on user-generated-content pages (forum posts,
  comment sections), where structure is author-controlled, not template-controlled.
- **Not-determinable**: n/a — structure is always available in static HTML if the page is.
- **Action**: add exactly one `<main>` landmark, ensure exactly one `<h1>` per page, and fix
  any heading-level skips so levels descend one at a time.
- **Runtime**: low.

## CHK-E-023 — Mobile ad/promo density above 30%

- **Mechanism**: E — the Better Ads Standards' 30%-mobile / 50%-desktop thresholds are the
  only published, numeric, mechanically-applicable ad-density limits available; density
  above them is a defined violation of an industry-adopted standard, not a subjective
  aesthetic judgment.
- **Strength**: `CORRELATIONAL`/`NORMATIVE`. Ceiling: `medium`.
- **Reads**: `rendered[].viewports.mobile_375.ad_regions[]` (`area_pct`, `detector`),
  `ad_area_pct_total`, 1–2 pages. **Requires ≥2 independent detectors to agree** on each
  counted region — see `SKILL.md`'s "The weakest check".
- **Severity rule**: `medium` if `ad_area_pct_total > 30` at 375px, counting only regions
  with cross-detector agreement.
- **Evidence**: `First viewport: ~{pct}% of visible area occupied by advertisements.`
- **FP guard**: suppress entirely if no ad regions are detected anywhere on the site (a
  clean site with zero ads is not evaluated against a density it doesn't have).
- **Not-determinable**: headless render didn't complete, **or** detectors disagree and no
  region reaches 2-detector agreement → `not_determinable` rather than a low-confidence
  finding.
- **Action**: reduce ad density below the Better Ads mobile threshold, or move ad regions
  below the first viewport.
- **Runtime**: high (reads the shared render pass).

## CHK-E-024 — Missing trust signals (recommendation only)

- **Mechanism**: E — visible contact information, an organisation name, HTTPS, and byline
  dates are commonly cited as trust signals for commercial and news content.
- **Strength**: `CORRELATIONAL`, single unreplicated study (P-07.13; P-06.11 also
  unverified at time of review). **Under the single-source rule, this check may never be
  emitted as a scored finding at any severity.**
- **Reads**: `pages[].contact_signals`, `site.scheme`, `pages[].dates`, commercial/
  service/news archetypes only, 2–3 pages.
- **Disposition**: emit with `severity: null`, `recommendation_only: true`. The evidence
  string and suggested action are still populated normally — only the severity/finding
  status changes.
- **Evidence**: `Commercial site: no detectable {signal}.`
- **FP guard**: apply only to commercial/service/news archetypes; exclude personal/hobby
  sites entirely, where these signals carry no equivalent expectation.
- **Not-determinable**: HTTPS check times out → `not_determinable` for that signal only.
- **Action**: add visible contact information, the organisation's name in the footer,
  serve over HTTPS, and add byline dates to news/article content.
- **Runtime**: low.
- **Promotion path**: if P-07.13 is hand-verified against its primary source (not merely
  agent-reported) and a second independent source is found, this check may be promoted to
  a `low` finding. Until then it stays a recommendation.
