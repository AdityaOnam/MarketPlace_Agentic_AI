"""Per-page static extraction: main text, headings, structured data, links, images, forms,
dates, contact signals, trigram hash — the `pages[]` entry fields.

Reference: procedure.md §4 "Per-page extraction", docs/BUNDLE-SCHEMA.md `pages[]`.
Pure function over already-fetched HTML text plus response headers; no network access.
"""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urljoin, urlparse

from html_tree import RAW_TEXT_ELEMENTS, Node, parse_html

BOILERPLATE_TAGS = {"nav", "header", "footer", "aside", "script", "style", "noscript", "form"}
MEANINGFUL_TEXT_MIN_LEN = 2  # ignore single-character stray text nodes when counting words

_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}")
_MONTHS = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
_DATE_RE = re.compile(
    r"\b(\d{4}-\d{2}-\d{2})\b|"
    r"\b(\d{1,2}\s+" + _MONTHS + r"\s+\d{4})\b|"
    # Month-first ("October 31, 2024") -- the dominant format on US-English sites and the
    # one this regex lacked until a squarespace.com press page with a visible date, JSON-LD
    # datePublished and /2024/10/31/ in its URL was reported as undated (2026-09-12).
    r"\b(" + _MONTHS + r"\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
_URL_DATE_RE = re.compile(r"/((?:19|20)\d{2})/(\d{2})(?:/(\d{2}))?(?:/|$)")


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _registrable_domain(host: str) -> str:
    """Crude eTLD+1 approximation: last two labels, or three for common two-part public
    suffixes. Good enough to decide "same organisation's domain", not a full PSL lookup —
    a full Public Suffix List is unnecessary weight for a same-origin/off-origin decision
    that only ever needs to be roughly right, and every check reading this field treats a
    borderline miss as `not_determinable`-safe rather than load-bearing on its own."""
    host = (host or "").lower().split(":")[0]
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    two_part_suffixes = {"co.uk", "com.au", "co.in", "co.jp", "com.br"}
    last_two = ".".join(labels[-2:])
    if last_two in two_part_suffixes and len(labels) >= 3:
        return ".".join(labels[-3:])
    return last_two


MAIN_CONTENT_MIN_WORDS = 50
# Bytes of HTML per word of extracted text above which the page is almost certainly
# delivering its content through JavaScript rather than markup. A 100 KB document with
# under 50 words is a hydration shell, not a thin page.
JS_RENDER_MIN_BYTES = 100_000
JS_RENDER_MAX_WORDS = 50
JS_PAYLOAD_BYTES_PER_WORD = 250
JS_PAYLOAD_MIN_BYTES = 50_000

_FALLBACK_CONTAINER_TAGS = ("article", "aside", "section", "td", "div")
_FALLBACK_SCAN_CAP = 400


def _main_content_root(root: Node) -> tuple[Node, str]:
    """The extraction scope for 'main text', plus a label saying how it was chosen.

    Order: <main>, then any element with role="main", then the largest <article>, then
    <body> minus boilerplate. When that last scope is thin (< MAIN_CONTENT_MIN_WORDS) the
    page's content may be sitting inside a tag this extractor treats as boilerplate --
    kernel.org puts its release tables inside <aside id="featured"><article>, so the
    body-minus-boilerplate scope returned 25 words of blogroll and CHK-D-003 reported a
    famously plain static site as a JavaScript shell (judge review, 2026-09-13). In that
    case the largest container found anywhere under <body> is used if it is at least
    three times richer than the boilerplate-stripped body.
    """
    main = root.find_first("main")
    if main is not None:
        return main, "main"
    for tag in ("div", "section", "article"):
        for node in root.find_all(tag):
            if (node.get("role") or "").lower() == "main":
                return node, "role_main"
    body = root.find_first("body")
    if body is None:
        return root, "root"

    body_words = _word_count(_strip_boilerplate_text(body))

    # An <article> is the page's content only when it carries most of the page's text. A
    # homepage made of twenty <article> cards (developer.mozilla.org: largest card 66
    # words against 630 in the body) is not an article page, and taking the biggest card
    # would call the homepage thin.
    articles = body.find_all("article")
    if articles:
        best = max(articles, key=lambda a: _word_count(_strip_boilerplate_text(a)))
        best_words = _word_count(_strip_boilerplate_text(best))
        if best_words >= MAIN_CONTENT_MIN_WORDS and best_words * 2 >= body_words:
            return best, "article"

    if body_words >= MAIN_CONTENT_MIN_WORDS:
        return body, "body"

    best_node, best_words = None, 0
    scanned = 0
    for tag in _FALLBACK_CONTAINER_TAGS:
        for node in body.find_all(tag):
            scanned += 1
            if scanned > _FALLBACK_SCAN_CAP:
                break
            words = _word_count(_strip_boilerplate_text(node))
            if words > best_words:
                best_node, best_words = node, words
        if scanned > _FALLBACK_SCAN_CAP:
            break
    if best_node is not None and best_words >= max(MAIN_CONTENT_MIN_WORDS, 3 * body_words):
        ident = best_node.get("id") or (best_node.get("class") or "").split(" ")[0] or ""
        return best_node, f"fallback:{best_node.tag}" + (f"#{ident}" if ident else "")
    return body, "body"


def _strip_boilerplate_text(node: Node) -> str:
    """Same as Node.text() but additionally excludes nav/header/footer/aside/form —
    the boilerplate-removed extraction procedure.md §4 calls for.

    Iterative for the same reason `html_tree.Node.text` is (2026-09-04): a real site's
    markup produced a ~1000-level-deep tree and the recursive version raised
    RecursionError out of the collector, aborting the audit instead of degrading it.
    Document order is preserved by pushing children in reverse onto the stack.
    """
    parts: list[str] = []
    stack: list = list(reversed(node.children))
    while stack:
        child = stack.pop()
        if isinstance(child, str):
            if child.strip():
                parts.append(child.strip())
        elif child.tag not in BOILERPLATE_TAGS and child.tag not in RAW_TEXT_ELEMENTS:
            stack.extend(reversed(child.children))
    return " ".join(parts)


def _extract_headings(root: Node) -> list[dict]:
    """Headings in document order. Iterative (2026-09-04) — see `html_tree.Node.find_all`
    for why every tree walk in this collector had to stop recursing."""
    headings = []
    stack: list = [c for c in reversed(root.children) if isinstance(c, Node)]
    order = 0
    while stack:
        node = stack.pop()
        if node.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            headings.append({"level": int(node.tag[1]), "text": node.text(), "order": order})
            order += 1
        stack.extend(c for c in reversed(node.children) if isinstance(c, Node))
    return headings


def _extract_structured_data(root: Node) -> dict:
    json_ld = []
    for script in root.find_all("script"):
        if (script.get("type") or "").lower() != "application/ld+json":
            continue
        raw_text = "".join(c for c in script.children if isinstance(c, str))
        try:
            parsed = json.loads(raw_text)
        except (json.JSONDecodeError, ValueError):
            json_ld.append({"type": None, "raw": raw_text, "fields_present": [],
                             "parse_error": True})
            continue
        candidates = parsed if isinstance(parsed, list) else [parsed]
        for item in candidates:
            if isinstance(item, dict) and "@graph" in item and isinstance(item["@graph"], list):
                candidates_extra = item["@graph"]
            else:
                candidates_extra = []
            for entry in [item, *candidates_extra]:
                if not isinstance(entry, dict):
                    continue
                json_ld.append({
                    "type": entry.get("@type"),
                    "raw": entry,
                    "fields_present": sorted(k for k in entry.keys() if not k.startswith("@")),
                })
    return {"json_ld": json_ld, "microdata_types": [], "rdfa_types": []}


def _extract_links(root: Node, page_url: str, canonical_host: str) -> tuple[list[dict], list[str]]:
    links = []
    outbound_profile_links = []
    page_domain = _registrable_domain(canonical_host)

    for a in root.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        absolute = urljoin(page_url, href)
        parsed = urlparse(absolute)
        internal = _registrable_domain(parsed.netloc) == page_domain if parsed.netloc else True
        rel = a.get("rel")
        entry = {
            "href": absolute,
            "text": a.text(),
            "rel": rel,
            "internal": internal,
            "aria_label": a.get("aria-label"),
        }
        links.append(entry)

        if not internal and (a.has_ancestor("header") or a.has_ancestor("footer")
                              or (rel and "me" in rel.split())):
            outbound_profile_links.append(absolute)

    return links, outbound_profile_links


def _is_decorative(el: Node) -> bool:
    """ARIA-equivalent of alt="": the element is explicitly removed from the a11y tree.

    Added 2026-09-04 after the Stage B negative-control screen: an accessibility-exemplar
    site marks its own header/footer icons `aria-hidden="true"`, which is correct practice,
    and CHK-E-014 was reporting every one of them as a missing-alt violation.
    """
    if (el.get("aria-hidden") or "").lower() == "true":
        return True
    return (el.get("role") or "").lower() in ("presentation", "none")


# Class names that conventionally mean `display:none` in the frameworks this corpus uses.
# Deliberately excludes `sr-only` / `visually-hidden` / `screen-reader-text`: those are
# visually hidden but *present in the accessibility tree*, so an unnamed control carrying
# one is still a real defect and must keep failing CHK-E-014.
_DISPLAY_NONE_CLASSES = {"hidden", "is-hidden", "d-none", "u-hidden", "display-none"}


def _is_hidden(el: Node) -> bool:
    """Statically-evident non-rendering. Not a substitute for computed styles -- it only
    catches what the HTML itself declares -- but a `style="display: none"` mobile-nav
    trigger is not a control a user can fail to perceive.

    Class-name heuristic added by D-029 (2026-09-10). Without it, CHK-E-014's
    accessible-name sub-check reported `<a rel="me" href="https://mastodon.social/@..."
    class="hidden"></a>` on www.smashingmagazine.com as a "link with no accessible name" on
    every one of 12 sampled pages. That anchor is a Mastodon/IndieWeb identity-verification
    link: empty and CSS-hidden by design, never encountered by a user -- and the very
    construct CHK-D-025 asks sites to add. One check was penalising what another rewards.

    This is a heuristic over class names, not CSS resolution, so it is deliberately narrow:
    see `_DISPLAY_NONE_CLASSES`.
    """
    if "hidden" in el.attrs:
        return True
    classes = {c.lower() for c in (el.get("class") or "").split()}
    if classes & _DISPLAY_NONE_CLASSES:
        return True
    style = (el.get("style") or "").replace(" ", "").lower()
    return "display:none" in style or "visibility:hidden" in style


def _alt_value(img: Node) -> str | None:
    """`None` only when the attribute is genuinely absent.

    `<img alt>` is a valueless HTML attribute and browsers treat it exactly as `alt=""` --
    a correct decorative marking. `html.parser` reports its value as `None`, which made it
    indistinguishable from an absent attribute, so CHK-E-014's documented guard ("test
    `alt === null`, not `!alt`") could not work no matter how carefully the analyser was
    written. Found on a WCAG-authoring site during the Stage B screen."""
    if "alt" not in img.attrs:
        return None
    return img.attrs.get("alt") or ""


def _extract_images(root: Node) -> list[dict]:
    images = []
    for img in root.find_all("img"):
        style = img.get("style") or ""
        aspect_match = re.search(r"aspect-ratio\s*:\s*([^;]+)", style)
        images.append({
            "src": img.get("src"),
            "alt": _alt_value(img),  # None only if the attribute is absent
            "decorative_hint": _is_decorative(img),
            "width_attr": img.get("width"),
            "height_attr": img.get("height"),
            "css_aspect_ratio": aspect_match.group(1).strip() if aspect_match else None,
            "in_picture": img.has_ancestor("picture"),
        })
    return images


def _extract_iframes(root: Node) -> list[dict]:
    return [
        {
            "src": f.get("src"),
            "width_attr": f.get("width"),
            "height_attr": f.get("height"),
            "title": f.get("title"),
        }
        for f in root.find_all("iframe")
    ]


def _extract_media(root: Node) -> list[dict]:
    media = []
    for tag in ("video", "audio"):
        for el in root.find_all(tag):
            media.append({
                "tag": tag,
                "autoplay": el.get("autoplay") is not None,
                "muted": el.get("muted") is not None,
                "controls": el.get("controls") is not None,
                "loop": el.get("loop") is not None,
            })
    return media


def _extract_form_controls(root: Node) -> list[dict]:
    labels_for = {lbl.get("for") for lbl in root.find_all("label") if lbl.get("for")}
    controls = []
    for tag in ("input", "textarea", "select"):
        for el in root.find_all(tag):
            if tag == "input" and (el.get("type") or "text").lower() in ("hidden", "submit", "button"):
                continue
            # A CSS-hidden control is not one a user can fail to perceive. Spam honeypots
            # (`<input name="9P8yG" style="display:none !important">`) are the common case;
            # one was reported as an unlabelled form control on adrianroselli.com/contact.
            if _is_hidden(el):
                continue
            el_id = el.get("id")
            wrapped_in_label = el.has_ancestor("label")
            controls.append({
                "type": el.get("type") if tag == "input" else tag,
                "id": el_id,
                "has_label": (bool(el_id and el_id in labels_for) or wrapped_in_label
                              or bool(el.get("aria-labelledby"))),
                "aria_label": el.get("aria-label"),
            })
    return controls


def _extract_interactive_empty(root: Node) -> dict:
    def is_empty(el: Node) -> bool:
        # An element the page has explicitly hidden, or removed from the accessibility
        # tree, is not a control anyone can encounter without a name.
        if _is_hidden(el) or _is_decorative(el):
            return False
        # aria-labelledby names the control from another element's text -- a valid
        # accessible name per the accname spec. Missed on adrianroselli.com (2026-09-12):
        # `<button aria-labelledby="mnu2095">` on every page was counted as unnamed.
        if el.get("aria-label") or el.get("aria-labelledby") or el.get("title"):
            return False
        if el.text().strip():
            return False
        for img in el.find_all("img"):
            if _alt_value(img):
                return False
        # An inline <svg> with a <title> names its parent control just as alt text does.
        for svg in el.find_all("svg"):
            if svg.find_first("title") is not None:
                return False
        return True

    def is_identity_anchor(a: Node) -> bool:
        """`rel="me"` with no content is the IndieWeb/Mastodon verification pattern: a
        machine-readable identity claim, not a control. D-029."""
        rel = (a.get("rel") or "").lower().split()
        return "me" in rel and not a.text().strip()

    links_no_text = sum(1 for a in root.find_all("a")
                        if a.get("href") is not None and not is_identity_anchor(a)
                        and is_empty(a))
    buttons_no_text = sum(1 for b in root.find_all("button") if is_empty(b))
    return {"links_no_text": links_no_text, "buttons_no_text": buttons_no_text}


def _jsonld_dates(root: Node) -> tuple[str | None, str | None]:
    """First `datePublished` / `dateModified` found in any ld+json block, walking nested
    objects and `@graph` arrays. Tolerant of invalid JSON (returns nothing)."""
    published = modified = None

    def walk(obj):
        nonlocal published, modified
        if isinstance(obj, dict):
            if published is None and isinstance(obj.get("datePublished"), str):
                published = obj["datePublished"]
            if modified is None and isinstance(obj.get("dateModified"), str):
                modified = obj["dateModified"]
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for script in root.find_all("script"):
        if (script.get("type") or "").lower() != "application/ld+json":
            continue
        try:
            walk(json.loads(script.text()))
        except (ValueError, TypeError):
            continue
    return published, modified


def _extract_dates(root: Node, header_last_modified: str | None, page_url: str = "") -> dict:
    meta_published = None
    meta_modified = None
    for meta in root.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").lower()
        if prop in ("article:published_time", "og:article:published_time", "datepublished"):
            meta_published = meta.get("content")
        elif prop in ("article:modified_time", "og:article:modified_time", "datemodified"):
            meta_modified = meta.get("content")

    jsonld_published, jsonld_modified = _jsonld_dates(root)

    visible_dates = [t.get("datetime") for t in root.find_all("time") if t.get("datetime")]
    if not visible_dates:
        body = root.find_first("body")
        text = body.text() if body else root.text()
        visible_dates = [m.group(0) for m in _DATE_RE.finditer(text)][:10]

    url_date = None
    m = _URL_DATE_RE.search(urlparse(page_url).path if page_url else "")
    if m:
        url_date = "-".join(x for x in m.groups() if x)

    return {
        "meta_published": meta_published,
        "meta_modified": meta_modified,
        "jsonld_published": jsonld_published,
        "jsonld_modified": jsonld_modified,
        "visible_dates": visible_dates,
        "url_date": url_date,
        "header_last_modified": header_last_modified,
    }


_COPYRIGHT_MARKER_RE = re.compile(r"(?:©|\(c\)|copyright)", re.I)
_LEADING_YEAR_RE = re.compile(r"^\s*(?:\d{4}(?:\s*[-–]\s*\d{4})?)?\s*(?:by\s+)?", re.I)
_NAME_TERMINATOR_RE = re.compile(r"[.|·•\n\r]|all rights reserved", re.I)
# A legal suffix ends the name even with no punctuation after it: "Square, Inc English
# Español Dansk" is "Square, Inc" followed by a language selector (weebly.com, 2026-09-12).
_LEGAL_SUFFIX_END_RE = re.compile(
    r"\b(Inc|Incorporated|Ltd|Limited|LLC|L\.L\.C|PLC|GmbH|AG|S\.A|S\.p\.A|B\.V|N\.V|Pty|"
    r"Corp|Corporation|Co|Company|Foundation|Association|Trust|LLP|LP)\.?(?=\s|$)", re.I)
# Footer nav labels that are never part of an organisation name. A candidate made mostly
# of these is a menu, not a name ("Terms Privacy Status Pricing", github.com, 2026-09-12).
_NAV_WORDS = {"terms", "privacy", "status", "pricing", "contact", "about", "home", "help",
              "support", "legal", "cookies", "cookie", "careers", "blog", "docs", "security",
              "sitemap", "policy", "settings", "login", "sign", "press", "faq", "accessibility"}


def _footer_org_name(footer_text: str) -> str | None:
    """The organisation name a footer states, or None.

    Rewritten 2026-09-04 after the Stage B negative-control screen. This used to take the
    footer's text up to its first full stop, capped at 120 characters. A modern footer is a
    navigation menu and contains no full stop, so on every site with one it returned 120
    characters of link labels -- "Home Contact Help Support us Legal & Policies..." -- and
    CHK-D-027 dutifully reported that as one of the organisation's competing names. It was
    the single largest false-positive source the screen found.

    A footer states its organisation's name in one reliable place: the copyright line.
    Everything else in a footer is navigation. Returning None when there is no copyright
    line is the correct answer rather than a gap -- CHK-D-027 already handles having too
    few names to compare, and its own docstring always said this field was a fallback.
    """
    if not footer_text:
        return None
    marker = _COPYRIGHT_MARKER_RE.search(footer_text)
    if marker is None:
        return None
    tail = footer_text[marker.end():]
    tail = _LEADING_YEAR_RE.sub("", tail, count=1)
    end = _NAME_TERMINATOR_RE.search(tail)
    name = (tail[:end.start()] if end else tail[:60])
    suffix = _LEGAL_SUFFIX_END_RE.search(name)
    if suffix:
        name = name[:suffix.end()]
    name = re.sub(r"\s+", " ", name).strip(" ,-–©")
    words = name.split()
    if len(name) < 2 or len(name) > 60 or len(words) > 8:
        return None
    if len(words) >= 2 and sum(w.lower().strip(".,") in _NAV_WORDS for w in words) * 2 >= len(words):
        return None
    return name


def _extract_contact_signals(root: Node) -> dict:
    footer = root.find_first("footer")
    footer_text = footer.text() if footer else ""
    body_text = (root.find_first("body") or root).text()

    email = bool(_EMAIL_RE.search(body_text)) or any(
        (a.get("href") or "").lower().startswith("mailto:") for a in root.find_all("a")
    )
    phone_match = _PHONE_RE.search(footer_text) or _PHONE_RE.search(body_text)

    org_name_footer = _footer_org_name(footer_text)

    return {
        "email": email,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "postal_address": None,  # not reliably extractable without structured data; see
                                  # structured_data.json_ld for PostalAddress instead
        "org_name_footer": org_name_footer,
    }


def _extract_canonical(root: Node, page_url: str) -> dict:
    link = None
    for l in root.find_all("link"):
        if (l.get("rel") or "").lower() == "canonical":
            link = l
            break
    if link is None or not link.get("href"):
        return {"href": None, "self_referential": False, "cross_domain": False}

    href = urljoin(page_url, link.get("href"))
    page_parsed = urlparse(page_url)
    canon_parsed = urlparse(href)

    def _norm(p):
        return (p.scheme, p.netloc.lower(), p.path.rstrip("/") or "/")

    self_referential = _norm(page_parsed) == _norm(canon_parsed)
    cross_domain = _registrable_domain(canon_parsed.netloc) != _registrable_domain(page_parsed.netloc)
    return {"href": href, "self_referential": self_referential, "cross_domain": cross_domain}


def _extract_meta(root: Node) -> dict:
    viewport = description = robots = None
    for meta in root.find_all("meta"):
        name = (meta.get("name") or "").lower()
        if name == "viewport":
            viewport = meta.get("content")
        elif name == "description":
            description = meta.get("content")
        elif name == "robots":
            robots = meta.get("content")
    return {"viewport": viewport, "description": description, "robots": robots}


def _extract_landmarks(root: Node) -> dict:
    def count(tag: str, role: str) -> int:
        n = len(root.find_all(tag))
        n += sum(1 for el in root.find_all("div") if (el.get("role") or "").lower() == role)
        return n

    return {
        "main": count("main", "main"),
        "nav": count("nav", "navigation"),
        "header": count("header", "banner"),
        "footer": count("footer", "contentinfo"),
    }


def _trigram_hash(text: str) -> str:
    words = _WORD_RE.findall(text.lower())
    trigrams = {" ".join(words[i:i + 3]) for i in range(len(words) - 2)} if len(words) >= 3 else set()
    digest = hashlib.sha256("\n".join(sorted(trigrams)).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


_HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")


def unavailable_page(page_url: str, reason: str, http_status: int | None = None,
                     page_type: str = "other", final_url: str | None = None) -> dict:
    """A `pages[]` entry for a URL that yielded no auditable HTML document.

    Every analyser guards on `extraction_ok` (D-023), so a page shaped like this produces
    `not_determinable` envelopes and never a finding. Used for non-2xx responses, non-HTML
    content types, and empty bodies -- a 404 in a stale sitemap, a redirect stub, a gzipped
    child sitemap are not pages and must not be graded as if they were.
    """
    return {"url": page_url, "final_url": final_url or page_url, "status": "unavailable",
            "reason": reason, "http_status": http_status, "page_type": page_type,
            "headers": {}, "raw_html": None, "raw_html_bytes": 0, "main_text": "",
            "main_text_words": 0, "main_content_source": None, "extraction_ok": False,
            "js_render_suspected": False, "js_payload_heavy": False, "title": None, "meta": {},
            "lang": None, "canonical": {}, "headings": [], "landmarks": {},
            "structured_data": {}, "links": [], "outbound_profile_links": [], "images": [],
            "iframes": [], "media": [], "form_controls": [], "interactive_empty": {},
            "noscript": {"present": False, "words": 0}, "dates": {},
            "contact_signals": {}, "trigram_hash": None}


def extract_page(
    html_text: str,
    page_url: str,
    canonical_host: str,
    http_status: int,
    headers: dict | None = None,
    page_type: str = "other",
    final_url: str | None = None,
) -> dict:
    """Build one `pages[]` entry per docs/BUNDLE-SCHEMA.md, from raw HTML + response info.

    `final_url` is the URL after redirects; it becomes the finding locus so a `/about` that
    302s to `/in/about` is reported where it actually lives.
    """
    headers = headers or {}
    final_url = final_url or page_url

    if http_status is None or not (200 <= http_status < 300):
        return unavailable_page(page_url, f"http_{http_status}", http_status, page_type, final_url)
    content_type = (headers.get("content-type") or headers.get("Content-Type") or "").lower()
    if content_type and not any(content_type.startswith(t) for t in _HTML_CONTENT_TYPES):
        return unavailable_page(page_url, f"non_html:{content_type.split(';')[0]}",
                                http_status, page_type, final_url)
    if not (html_text or "").strip():
        return unavailable_page(page_url, "empty_body", http_status, page_type, final_url)

    root = parse_html(html_text)

    main_root, main_content_source = _main_content_root(root)
    main_text = _strip_boilerplate_text(main_root)
    main_text_words = _word_count(main_text)

    # procedure.md §4: extraction_ok False (not empty) when extraction yields under 20
    # words from a document over 5KB — distinguishes a genuinely short page from a failed
    # extraction, which is exactly what CHK-D-004's guard needs.
    raw_bytes = len((html_text or "").encode("utf-8"))
    extraction_ok = not (main_text_words < 20 and raw_bytes > 5000)

    # Two flags for "the content is not in the markup", read by the content-density
    # checks (D-004, D-005, D-010, D-013), which must answer not_determinable rather than
    # call a hydration shell thin or two identical shells duplicates. CHK-D-003 is the one
    # check whose job is to report this condition, so it reads the raw numbers instead.
    js_render_suspected = main_text_words < JS_RENDER_MAX_WORDS and raw_bytes > JS_RENDER_MIN_BYTES
    js_payload_heavy = (raw_bytes > JS_PAYLOAD_MIN_BYTES
                        and raw_bytes / max(main_text_words, 1) > JS_PAYLOAD_BYTES_PER_WORD)

    title_node = root.find_first("title")
    html_node = root.find_first("html")
    noscript_node = root.find_first("noscript")

    return {
        "url": page_url,
        "final_url": final_url,
        "status": "ok",
        "reason": None,
        "http_status": http_status,
        "page_type": page_type,

        "headers": headers,
        "raw_html": html_text,
        "raw_html_bytes": raw_bytes,

        "main_text": main_text,
        "main_text_words": main_text_words,
        "main_content_source": main_content_source,
        "extraction_ok": extraction_ok,
        "js_render_suspected": js_render_suspected,
        "js_payload_heavy": js_payload_heavy,

        "title": title_node.text() if title_node else None,
        "meta": _extract_meta(root),
        "lang": html_node.get("lang") if html_node else None,
        "canonical": _extract_canonical(root, page_url),

        "headings": _extract_headings(root),
        "landmarks": _extract_landmarks(root),

        "structured_data": _extract_structured_data(root),

        "links": _extract_links(root, page_url, canonical_host)[0],
        "outbound_profile_links": _extract_links(root, page_url, canonical_host)[1],

        "images": _extract_images(root),
        "iframes": _extract_iframes(root),
        "media": _extract_media(root),

        "form_controls": _extract_form_controls(root),
        "interactive_empty": _extract_interactive_empty(root),

        "noscript": {
            "present": noscript_node is not None,
            "words": _word_count(noscript_node.text()) if noscript_node else 0,
        },
        "dates": _extract_dates(root, headers.get("last-modified"), final_url),

        "contact_signals": _extract_contact_signals(root),
        "trigram_hash": _trigram_hash(main_text),
    }
