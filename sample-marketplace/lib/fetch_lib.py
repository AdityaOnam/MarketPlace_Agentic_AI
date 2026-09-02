"""
Shared, stdlib-only fetch/parse helpers used by every skill's check scripts.

Design constraints (these are contest requirements, not preferences):
  * No third-party dependencies -> portable, no install step, no model weights.
  * Read-only -> GET only, never POST/forms/auth.
  * Respects robots.txt -> disallowed paths are skipped, never fetched.
  * Rate-limited and page-capped -> a full audit finishes well under 5 minutes.

Every check script imports from here so the site is crawled ONCE and the same
page set is handed to all checks.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

USER_AGENT = "BrandAIReadinessAuditBot/1.0 (+read-only site audit; respects robots.txt)"
TIMEOUT = 10          # seconds per request
MAX_PAGES = 8         # hard cap on pages fetched per audit
CRAWL_DELAY = 0.4     # seconds between requests - politeness floor
MAX_BYTES = 2_000_000 # never read more than 2 MB from one response


# --------------------------------------------------------------------------
# HTML parsing
# --------------------------------------------------------------------------
class PageParser(HTMLParser):
    """Collects the signals every check needs, in one pass over the HTML."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta = {}
        self.links = []
        self.h1s = []
        self.headings = []          # (level, text)
        self.jsonld_blocks = []
        self.text_chunks = []
        self.canonical = None
        self.lang = None
        self.script_count = 0
        self.img_total = 0
        self.img_no_alt = 0
        self.has_nav = False
        self.has_main = False
        self.has_breadcrumb = False
        self.has_search_input = False
        self.has_time_tag = False
        self.microdata_attrs = 0
        self._in_title = False
        self._in_jsonld = False
        self._jsonld_buf = []
        self._heading_level = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").lower()

        if tag == "html" and "lang" in a:
            self.lang = a["lang"]
        elif tag == "title":
            self._in_title = True
        elif tag == "a" and "href" in a:
            self.links.append(a["href"])
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key.lower()] = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "script":
            self.script_count += 1
            if a.get("type") == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_buf = []
        elif tag in ("h1", "h2", "h3", "h4"):
            self._heading_level = int(tag[1])
        elif tag == "img":
            self.img_total += 1
            if not (a.get("alt") or "").strip():
                self.img_no_alt += 1
        elif tag == "nav":
            self.has_nav = True
            if "breadcrumb" in cls or "breadcrumb" in (a.get("aria-label") or "").lower():
                self.has_breadcrumb = True
        elif tag == "main":
            self.has_main = True
        elif tag == "time":
            self.has_time_tag = True
        elif tag == "input":
            if a.get("type") == "search" or "search" in (a.get("name") or "").lower():
                self.has_search_input = True

        if "itemprop" in a or "itemtype" in a or "typeof" in a:
            self.microdata_attrs += 1
        if "breadcrumb" in cls:
            self.has_breadcrumb = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            self.jsonld_blocks.append("".join(self._jsonld_buf))
        elif tag in ("h1", "h2", "h3", "h4"):
            self._heading_level = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_jsonld:
            self._jsonld_buf.append(data)
            return
        text = data.strip()
        if not text:
            return
        if self._heading_level:
            self.headings.append((self._heading_level, text))
            if self._heading_level == 1:
                self.h1s.append(text)
        self.text_chunks.append(text)

    # -- derived signals ---------------------------------------------------
    def word_count(self):
        return sum(len(c.split()) for c in self.text_chunks)

    def parsed_jsonld(self):
        """Returns (valid_objects, malformed_count)."""
        objects, malformed = [], 0
        for block in self.jsonld_blocks:
            try:
                data = json.loads(block)
            except Exception:
                malformed += 1
                continue
            objects.extend(data if isinstance(data, list) else [data])
        return objects, malformed


def parse_html(html):
    p = PageParser()
    try:
        p.feed(html)
    except Exception:
        pass  # tolerate malformed markup; partial signals still useful
    return p


# --------------------------------------------------------------------------
# Network
# --------------------------------------------------------------------------
def fetch(url, timeout=TIMEOUT):
    """GET a URL. Never raises - always returns a result dict."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_BYTES)
            charset = resp.headers.get_content_charset() or "utf-8"
            return {
                "ok": True,
                "status": resp.status,
                "url": resp.geturl(),
                "redirected": resp.geturl().rstrip("/") != url.rstrip("/"),
                "html": raw.decode(charset, errors="replace"),
                "headers": {k.lower(): v for k, v in resp.headers.items()},
                "elapsed": round(time.time() - started, 2),
                "bytes": len(raw),
            }
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(MAX_BYTES).decode("utf-8", errors="replace")
        except Exception:
            pass
        return {"ok": False, "status": e.code, "url": url, "error": str(e),
                "html": body, "headers": {}, "elapsed": round(time.time() - started, 2)}
    except Exception as e:
        return {"ok": False, "status": None, "url": url, "error": str(e),
                "html": "", "headers": {}, "elapsed": round(time.time() - started, 2)}


def get_robots(base_url):
    parsed = urllib.parse.urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    res = fetch(robots_url)
    raw = res.get("html", "") if res.get("ok") else ""
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.parse(raw.splitlines())
    except Exception:
        pass
    return {"parser": rp, "text": raw, "url": robots_url, "status": res.get("status")}


def can_fetch(rp, url, ua="*"):
    try:
        return rp.can_fetch(ua, url)
    except Exception:
        return True  # fail open only for parser errors, never for an explicit Disallow


def crawl(base_url, max_pages=MAX_PAGES):
    """Homepage + capped same-domain internal links, robots-filtered and rate-limited.

    Returns (pages, robots) where pages is a list of (url, fetch_result).
    This is the ONE crawl the whole audit shares.
    """
    robots = get_robots(base_url)
    rp = robots["parser"]
    base_host = urllib.parse.urlparse(base_url).netloc

    home = fetch(base_url)
    pages = [(base_url, home)]
    seen = {base_url.rstrip("/")}

    if not home.get("ok"):
        return pages, robots

    for href in parse_html(home["html"]).links:
        if len(pages) >= max_pages:
            break
        full = urllib.parse.urljoin(base_url, href).split("#")[0]
        pu = urllib.parse.urlparse(full)
        if pu.scheme not in ("http", "https") or pu.netloc != base_host:
            continue
        if full.rstrip("/") in seen:
            continue
        if not can_fetch(rp, full):
            continue  # robots.txt says no -> we do not fetch it
        seen.add(full.rstrip("/"))
        time.sleep(CRAWL_DELAY)
        pages.append((full, fetch(full)))

    return pages, robots


def normalise(url):
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    p = urllib.parse.urlparse(url)
    return f"{p.scheme}://{p.netloc}/", p.netloc


def emit(findings):
    """Check scripts print exactly this shape on stdout."""
    print(json.dumps({"findings": findings}, indent=2))
