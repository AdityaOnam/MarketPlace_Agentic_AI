"""
Minimal, stdlib-only fetch/parse helpers shared by this skill's check scripts.
No third-party dependencies (portable, no install step, no model weights).
Read-only: issues GET requests only, respects robots.txt, rate-limits itself,
and caps how much it reads/crawls so a full audit finishes well under 5 minutes.
"""
import time
import json
import urllib.request
import urllib.error
import urllib.robotparser
import urllib.parse
from html.parser import HTMLParser

USER_AGENT = "BrandAIReadinessAuditBot/1.0 (+read-only site audit; respects robots.txt)"
TIMEOUT = 10
MAX_PAGES = 8
CRAWL_DELAY = 0.4
MAX_BYTES = 2_000_000


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.title = ""
        self.meta = {}
        self.h1s = []
        self.jsonld_blocks = []
        self.text_chunks = []
        self.canonical = None
        self.lang = None
        self.script_count = 0
        self.script_src_count = 0
        self.img_no_alt = 0
        self.img_total = 0
        self.has_nav = False
        self.has_search_input = False
        self._in_title = False
        self._in_jsonld = False
        self._jsonld_buf = []
        self._in_h1 = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and "lang" in a:
            self.lang = a.get("lang")
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = a.get("name") or a.get("property")
            if name:
                self.meta[name.lower()] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "script":
            self.script_count += 1
            if a.get("src"):
                self.script_src_count += 1
            if a.get("type") == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_buf = []
        if tag == "h1":
            self._in_h1 = True
        if tag == "img":
            self.img_total += 1
            if not (a.get("alt") or "").strip():
                self.img_no_alt += 1
        if tag == "nav":
            self.has_nav = True
        if tag == "input" and (a.get("type") == "search" or "search" in (a.get("name") or "").lower()):
            self.has_search_input = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            self.jsonld_blocks.append("".join(self._jsonld_buf))
        if tag == "h1":
            self._in_h1 = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_jsonld:
            self._jsonld_buf.append(data)
        if self._in_h1:
            self.h1s.append(data.strip())
        s = data.strip()
        if s:
            self.text_chunks.append(s)

    def word_count(self):
        return sum(len(c.split()) for c in self.text_chunks)


def fetch(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_BYTES)
            charset = resp.headers.get_content_charset() or "utf-8"
            html = raw.decode(charset, errors="replace")
            return {
                "ok": True, "status": resp.status, "url": resp.geturl(),
                "html": html, "headers": dict(resp.headers),
            }
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read(MAX_BYTES).decode("utf-8", errors="replace")
        except Exception:
            pass
        return {"ok": False, "status": e.code, "url": url, "error": str(e), "html": body}
    except Exception as e:
        return {"ok": False, "status": None, "url": url, "error": str(e), "html": ""}


def get_robots(base_url):
    parsed = urllib.parse.urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    res = fetch(robots_url)
    raw_text = res.get("html", "") if res.get("ok") else ""
    try:
        rp.parse(raw_text.splitlines())
    except Exception:
        pass
    return rp, raw_text, robots_url, res.get("status")


def can_fetch(rp, url, ua=USER_AGENT):
    try:
        return rp.can_fetch(ua, url)
    except Exception:
        return True


def discover_pages(base_url, max_pages=MAX_PAGES):
    """Fetch the homepage, then a capped set of same-domain internal-link pages.
    Skips anything robots.txt disallows for '*' and rate-limits itself."""
    rp, robots_txt, robots_url, robots_status = get_robots(base_url)
    pages = []
    seen = set()
    parsed_base = urllib.parse.urlparse(base_url)
    home = fetch(base_url)
    pages.append((base_url, home))
    seen.add(base_url.rstrip("/"))
    if home.get("ok"):
        p = PageParser()
        try:
            p.feed(home["html"])
        except Exception:
            pass
        for href in p.links:
            if len(pages) >= max_pages:
                break
            full = urllib.parse.urljoin(base_url, href).split("#")[0]
            pu = urllib.parse.urlparse(full)
            if pu.netloc != parsed_base.netloc or pu.scheme not in ("http", "https"):
                continue
            if full.rstrip("/") in seen:
                continue
            if not can_fetch(rp, full):
                continue
            seen.add(full.rstrip("/"))
            time.sleep(CRAWL_DELAY)
            pages.append((full, fetch(full)))
    return pages, {"robots_txt": robots_txt, "robots_url": robots_url, "robots_status": robots_status, "parser": rp}


def parse_html(html):
    p = PageParser()
    try:
        p.feed(html)
    except Exception:
        pass
    return p


def emit(findings):
    print(json.dumps({"findings": findings}, indent=2))
