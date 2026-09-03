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

from html_tree import Node, parse_html

BOILERPLATE_TAGS = {"nav", "header", "footer", "aside", "script", "style", "noscript", "form"}
MEANINGFUL_TEXT_MIN_LEN = 2  # ignore single-character stray text nodes when counting words

_WORD_RE = re.compile(r"[A-Za-z0-9']+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}")
_DATE_RE = re.compile(
    r"\b(\d{4}-\d{2}-\d{2})\b|"
    r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
    re.IGNORECASE,
)


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


def _main_content_root(root: Node) -> Node:
    """The extraction scope for 'main text': prefer <main>, else <body> minus boilerplate
    tags removed by _strip_boilerplate_text below."""
    main = root.find_first("main")
    if main is not None:
        return main
    body = root.find_first("body")
    return body if body is not None else root


def _strip_boilerplate_text(node: Node) -> str:
    """Same as Node.text() but additionally excludes nav/header/footer/aside/form —
    the boilerplate-removed extraction procedure.md §4 calls for."""
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        elif child.tag not in BOILERPLATE_TAGS:
            parts.append(_strip_boilerplate_text(child))
    return " ".join(p.strip() for p in parts if p.strip())


def _extract_headings(root: Node) -> list[dict]:
    headings = []
    order = 0

    def walk(node: Node):
        nonlocal order
        for child in node.children:
            if isinstance(child, Node):
                if child.tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    headings.append({
                        "level": int(child.tag[1]),
                        "text": child.text(),
                        "order": order,
                    })
                    order += 1
                walk(child)

    walk(root)
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


def _extract_images(root: Node) -> list[dict]:
    images = []
    for img in root.find_all("img"):
        style = img.get("style") or ""
        aspect_match = re.search(r"aspect-ratio\s*:\s*([^;]+)", style)
        images.append({
            "src": img.get("src"),
            "alt": img.get("alt"),  # None if attribute absent; "" if present-but-empty
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
            el_id = el.get("id")
            wrapped_in_label = el.has_ancestor("label")
            controls.append({
                "type": el.get("type") if tag == "input" else tag,
                "id": el_id,
                "has_label": bool(el_id and el_id in labels_for) or wrapped_in_label,
                "aria_label": el.get("aria-label"),
            })
    return controls


def _extract_interactive_empty(root: Node) -> dict:
    def is_empty(el: Node) -> bool:
        if el.get("aria-label") or el.get("title"):
            return False
        if el.text().strip():
            return False
        for img in el.find_all("img"):
            if img.get("alt"):
                return False
        return True

    links_no_text = sum(1 for a in root.find_all("a") if a.get("href") is not None and is_empty(a))
    buttons_no_text = sum(1 for b in root.find_all("button") if is_empty(b))
    return {"links_no_text": links_no_text, "buttons_no_text": buttons_no_text}


def _extract_dates(root: Node, header_last_modified: str | None) -> dict:
    meta_published = None
    meta_modified = None
    for meta in root.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").lower()
        if prop in ("article:published_time", "og:article:published_time", "datepublished"):
            meta_published = meta.get("content")
        elif prop in ("article:modified_time", "og:article:modified_time", "datemodified"):
            meta_modified = meta.get("content")

    visible_dates = [t.get("datetime") for t in root.find_all("time") if t.get("datetime")]
    if not visible_dates:
        body = root.find_first("body")
        text = body.text() if body else root.text()
        visible_dates = [m.group(0) for m in _DATE_RE.finditer(text)][:10]

    return {
        "meta_published": meta_published,
        "meta_modified": meta_modified,
        "visible_dates": visible_dates,
        "header_last_modified": header_last_modified,
    }


def _extract_contact_signals(root: Node) -> dict:
    footer = root.find_first("footer")
    footer_text = footer.text() if footer else ""
    body_text = (root.find_first("body") or root).text()

    email = bool(_EMAIL_RE.search(body_text)) or any(
        (a.get("href") or "").lower().startswith("mailto:") for a in root.find_all("a")
    )
    phone_match = _PHONE_RE.search(footer_text) or _PHONE_RE.search(body_text)

    org_name_footer = None
    if footer is not None:
        # First non-empty text-only child, or the whole footer's first sentence-ish chunk —
        # a heuristic, not a structured-data-backed fact; callers should prefer JSON-LD
        # `name` where available and treat this as a fallback signal only.
        stripped = footer_text.strip()
        if stripped:
            org_name_footer = stripped.split(".")[0][:120].strip() or None

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


def extract_page(
    html_text: str,
    page_url: str,
    canonical_host: str,
    http_status: int,
    headers: dict | None = None,
    page_type: str = "other",
) -> dict:
    """Build one `pages[]` entry per docs/BUNDLE-SCHEMA.md, from raw HTML + response info."""
    headers = headers or {}
    root = parse_html(html_text)

    main_root = _main_content_root(root)
    main_text = _strip_boilerplate_text(main_root)
    main_text_words = _word_count(main_text)

    # procedure.md §4: extraction_ok False (not empty) when extraction yields under 20
    # words from a document over 5KB — distinguishes a genuinely short page from a failed
    # extraction, which is exactly what CHK-D-004's guard needs.
    raw_bytes = len((html_text or "").encode("utf-8"))
    extraction_ok = not (main_text_words < 20 and raw_bytes > 5000)

    title_node = root.find_first("title")
    html_node = root.find_first("html")
    noscript_node = root.find_first("noscript")

    return {
        "url": page_url,
        "final_url": page_url,
        "status": "ok",
        "reason": None,
        "http_status": http_status,
        "page_type": page_type,

        "headers": headers,
        "raw_html": html_text,
        "raw_html_bytes": raw_bytes,

        "main_text": main_text,
        "main_text_words": main_text_words,
        "extraction_ok": extraction_ok,

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
        "dates": _extract_dates(root, headers.get("last-modified")),

        "contact_signals": _extract_contact_signals(root),
        "trigram_hash": _trigram_hash(main_text),
    }
