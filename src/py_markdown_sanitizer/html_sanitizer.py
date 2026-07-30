from __future__ import annotations

import bleach
from bs4 import BeautifulSoup

from .url_normalizer import UrlNormalizer

ALLOWED_TAGS = [
    "strong",
    "b",
    "em",
    "i",
    "code",
    "tt",
    "s",
    "strike",
    "del",
    "ins",
    "sub",
    "sup",
    "a",
    "img",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "blockquote",
    "q",
    "br",
    "hr",
    "pre",
    "samp",
    "kbd",
    "var",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "td",
    "th",
    "dl",
    "dt",
    "dd",
    "details",
    "summary",
    "div",
    "span",
]

ALLOWED_ATTR = [
    "href",
    "title",
    "target",
    "src",
    "alt",
    "width",
    "height",
    "start",
    "reversed",
    "value",
    "colspan",
    "rowspan",
    "headers",
    "open",
    "class",
    "id",
]

_ATTR_MAP = {tag: ALLOWED_ATTR for tag in ALLOWED_TAGS}

# Pass https/http/data through bleach; javascript: is stripped (DOMPurify-like).
# Relative URLs and fragments are kept. URL allow-listing happens afterwards.
_PROTOCOLS = ["http", "https", "mailto", "data"]


class HtmlSanitizer:
    def __init__(self, url_normalizer: UrlNormalizer) -> None:
        self.url_normalizer = url_normalizer

    def sanitize_html(self, html: str) -> str:
        if len(html) > 10000:
            return ""

        cleaned = bleach.clean(
            html,
            tags=ALLOWED_TAGS,
            attributes=_ATTR_MAP,
            protocols=_PROTOCOLS,
            strip=False,
            strip_comments=True,
        )

        soup = BeautifulSoup(cleaned, "html.parser")
        for node in soup.find_all(True):
            if node.has_attr("href"):
                node["href"] = self.url_normalizer.sanitize_url(node.get("href") or "", "href")
            if node.has_attr("src"):
                node["src"] = self.url_normalizer.sanitize_url(node.get("src") or "", "src")
            # Title/alt are too ambiguous — clear them (matches upstream)
            if node.has_attr("alt"):
                node["alt"] = ""
            if node.has_attr("title"):
                node["title"] = ""

        # imgs that lost src (e.g. stripped protocol) → /forbidden
        for img in soup.find_all("img"):
            if not img.get("src"):
                img["src"] = "/forbidden"

        result = str(soup)
        if not result:
            return result
        return result if result.endswith("\n") else result + "\n"
