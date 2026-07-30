from __future__ import annotations

import re
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

_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
# Unresolved refs left as text (e.g. glued defs) can re-parse into <img>.
_MD_REF_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
# Escape tag-like `<` but keep autolinks: <https://...>
_RAW_HTML_LT_RE = re.compile(r"<(?=!--|!\[CDATA|/?[A-Za-z][A-Za-z0-9-]*(?=[\s/>]))")
_CODE_RE = re.compile(r"(```[\s\S]*?```|`[^`\n]+`)")


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
    if raw.lower().startswith(("javascript:", "vbscript:", "data:")):
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


def _md_image_url(inner: str) -> str:
    inner = inner.strip()
    if not inner or inner[0] in "\"'":
        return ""
    if inner.startswith("<"):
        end = inner.find(">")
        return inner[1 : end if end != -1 else None].strip()
    return inner.split(None, 1)[0]


def _outside_code(markdown: str, transform) -> str:
    parts = _CODE_RE.split(markdown)
    return "".join(p if i % 2 else transform(p) for i, p in enumerate(parts))


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


def _filter_markdown_images(markdown: str, options: SanitizeOptions) -> str:
    def repl(match: re.Match[str]) -> str:
        alt, inner = match.group(1), match.group(2)
        return (
            match.group(0) if _is_allowed_image(_md_image_url(inner), options) else alt
        )

    return _outside_code(markdown, lambda part: _MD_IMAGE_RE.sub(repl, part))


def _strip_ref_images(markdown: str) -> str:
    """Drop leftover ![alt][id] — allowed imgs already became ![alt](url)."""
    return _outside_code(
        markdown, lambda part: _MD_REF_IMAGE_RE.sub(lambda m: m.group(1), part)
    )


def _escape_raw_html(markdown: str) -> str:
    return _outside_code(markdown, lambda part: _RAW_HTML_LT_RE.sub("&lt;", part))


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
        md = markdownify(clean, heading_style=ATX)
        md = _filter_markdown_images(md, self.options)
        md = _strip_ref_images(md)
        md = _escape_raw_html(md)
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
