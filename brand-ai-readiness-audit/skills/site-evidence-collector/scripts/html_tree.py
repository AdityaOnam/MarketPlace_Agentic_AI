"""A minimal HTML DOM tree built on stdlib html.parser.HTMLParser.

Not a spec-compliant HTML5 tree builder — real browsers do error recovery this doesn't
attempt. It is enough for read-only extraction of already-served markup, which is this
marketplace's actual job; a page too malformed for this to parse reasonably is exactly the
kind of page CHK-D-004/extraction_ok is designed to flag as `extraction_ok: false`, not
something worth a full HTML5 parser dependency to rescue.
"""
from __future__ import annotations

from html.parser import HTMLParser

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}

# Elements whose text content should never be walked into by a naive "all text" pass.
RAW_TEXT_ELEMENTS = {"script", "style"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag: str, attrs: dict, parent: "Node | None" = None):
        self.tag = tag
        self.attrs = attrs
        self.children: list["Node | str"] = []
        self.parent = parent

    def get(self, name: str, default=None):
        return self.attrs.get(name, default)

    def find_all(self, tag: str) -> list["Node"]:
        out: list[Node] = []
        for child in self.children:
            if isinstance(child, Node):
                if child.tag == tag:
                    out.append(child)
                out.extend(child.find_all(tag))
        return out

    def find_first(self, tag: str) -> "Node | None":
        matches = self.find_all(tag)
        return matches[0] if matches else None

    def text(self) -> str:
        """All descendant text, concatenated with single spaces, script/style excluded."""
        parts: list[str] = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            elif child.tag not in RAW_TEXT_ELEMENTS:
                parts.append(child.text())
        return " ".join(p.strip() for p in parts if p.strip())

    def has_ancestor(self, tag: str) -> bool:
        node = self.parent
        while node is not None:
            if node.tag == tag:
                return True
            node = node.parent
        return False


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {})
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), parent=self._stack[-1])
        self._stack[-1].children.append(node)
        if tag not in VOID_ELEMENTS:
            self._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, dict(attrs), parent=self._stack[-1])
        self._stack[-1].children.append(node)

    def handle_endtag(self, tag):
        # Pop back to (and including) the matching open tag, tolerating unclosed tags —
        # real-world HTML is not always well-formed and this must not crash on it.
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                return

    def handle_data(self, data):
        if data.strip():
            self._stack[-1].children.append(data)

    def error(self, message):  # pragma: no cover - HTMLParser API, no longer called in py3.10+
        pass


def parse_html(html_text: str) -> Node:
    builder = _TreeBuilder()
    try:
        builder.feed(html_text or "")
    except Exception:
        # A single malformed byte sequence should not take down extraction for the whole
        # page — whatever was parsed before the failure is still usable evidence.
        pass
    return builder.root
