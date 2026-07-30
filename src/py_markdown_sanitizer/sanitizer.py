from __future__ import annotations

from posixpath import normpath
from urllib.parse import unquote, urljoin, urlsplit

import mistune
from bs4 import BeautifulSoup, Comment, Tag
from markdownify import ATX, markdownify
from mistune.renderers.html import HTMLRenderer

from .types import SanitizeOptions

# Tags markdownify needs for a useful round-trip; everything else is dropped.
_KEEP_TAGS = frozenset(
    {
        "a",
        "p",
        "br",
        "hr",
        "img",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "blockquote",
        "code",
        "pre",
        "strong",
        "em",
        "b",
        "i",
        "del",
        "s",
        "strike",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "th",
        "td",
    }
)


def _eff_port(scheme: str, port: int | None) -> int:
    if port is not None:
        return port
    return 443 if scheme == "https" else 80


def _norm_url_path(path: str) -> str:
    trailing = path.endswith("/") and path != "/"
    out = normpath(unquote(path or "/") or "/")
    if not out.startswith("/"):
        out = "/" + out
    if trailing and not out.endswith("/"):
        out += "/"
    return out


def _http_url(url: str) -> urlsplit | None:
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"}:
        return None
    try:
        if parts.username is not None or parts.password is not None:
            return None
        if not parts.hostname:
            return None
        _ = parts.port  # may raise on garbage netloc
    except ValueError:
        return None
    return parts


def _is_allowed_image(url: str, options: SanitizeOptions) -> bool:
    """Allow only http(s) image URLs whose origin/path matches a prefix.

    Uses parsed host/path (not raw ``startswith``) so
    ``https://example.com.evil.com`` and ``https://example.com@evil.com``
    cannot ride on an ``https://example.com`` allow-list entry.
    """
    if not options.allowed_image_prefixes:
        return False
    raw = (url or "").strip()
    if not raw:
        return False
    target = _http_url(urljoin(options.default_origin, raw))
    if target is None:
        return False
    scheme = target.scheme.lower()
    host = target.hostname.lower()
    port = _eff_port(scheme, target.port)
    path = _norm_url_path(target.path or "/")

    for prefix in options.allowed_image_prefixes:
        pref = _http_url(prefix)
        if pref is None:
            continue
        p_scheme = pref.scheme.lower()
        if p_scheme != scheme or pref.hostname.lower() != host:
            continue
        if _eff_port(p_scheme, pref.port) != port:
            continue
        p_path = pref.path or ""
        if p_path in ("", "/"):
            return True
        npref = _norm_url_path(p_path)
        if p_path.endswith("/"):
            if not npref.endswith("/"):
                npref += "/"
            if path.startswith(npref):
                return True
        elif path == npref or path.startswith(npref + "/"):
            return True
    return False


def _plain(value: object) -> str:
    text = value if isinstance(value, str) else " ".join(value or ())
    return text.replace("<", "").replace(">", "")


def _sanitize_html(html: str, options: SanitizeOptions) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    for tag in list(soup.find_all(True)):
        if tag.name in ("html", "body", "[document]"):
            continue
        if tag.name not in _KEEP_TAGS:
            tag.decompose()

    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue
        src = img.get("src") or ""
        if _is_allowed_image(src, options):
            img.attrs = {
                "src": urljoin(options.default_origin, src.strip()),
                "alt": _plain(img.get("alt", "")),
            }
        else:
            alt = _plain(img.get("alt") or "").strip()
            if alt:
                img.replace_with(alt)
            else:
                img.decompose()

    return str(soup)


class MarkdownSanitizer:
    def __init__(self, options: SanitizeOptions | None = None) -> None:
        self.options = options or SanitizeOptions()
        self._md = mistune.create_markdown(
            renderer=HTMLRenderer(escape=False, allow_harmful_protocols=True),
            plugins=["strikethrough", "table", "url", "task_lists"],
        )

    def sanitize(self, markdown: str) -> str:
        html = self._md(markdown)
        clean = _sanitize_html(html, self.options)
        # escape_misc: neutralize leftover markdown/HTML syntax in text nodes
        # so the HTML→MD round-trip cannot reconstitute imgs or tags (same
        # idea as Vercel's turndown escape hook).
        md = markdownify(clean, heading_style=ATX, escape_misc=True)
        return md.rstrip() + ("\n" if clean.strip() else "")


def sanitize_markdown(
    markdown: str,
    options: SanitizeOptions | None = None,
    *,
    allowed_image_prefixes: list[str] | None = None,
    default_origin: str | None = None,
) -> str:
    if options is None:
        options = SanitizeOptions(
            allowed_image_prefixes=allowed_image_prefixes or [],
            default_origin=default_origin or "https://localhost",
        )
    return MarkdownSanitizer(options).sanitize(markdown)
