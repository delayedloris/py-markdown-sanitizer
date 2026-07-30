from __future__ import annotations

import re
from urllib.parse import urljoin

import mistune
from bs4 import BeautifulSoup, Comment, Tag
from markdownify import ATX, markdownify
from mistune.renderers.html import HTMLRenderer

from .types import SanitizeOptions

_AUTOLOAD_TAGS = frozenset(
    {
        "iframe",
        "embed",
        "object",
        "video",
        "audio",
        "source",
        "track",
        "script",
        "svg",
        "style",
        "base",
        "meta",
        "noscript",
        "template",
        "slot",
        "form",
        "input",
        "button",
        "textarea",
        "select",
    }
)
# <link> can prefetch; keep only if it has no href fetch risk — simpler to drop all
_DROP_TAGS = _AUTOLOAD_TAGS | {"link"}

# Markdown image: ![alt](url) or ![alt](<url> "title")
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
# Raw HTML tag openers (not autolinks like <https://...> which use scheme:)
_RAW_HTML_LT_RE = re.compile(
    r"<(?=!--|!\[CDATA|/?[A-Za-z][A-Za-z0-9-]*(?=[\s/>]))",
)
_CDATA_RE = re.compile(r"<!\[CDATA\[.*?\]\]>", re.DOTALL | re.IGNORECASE)
_FENCE_OR_CODE_RE = re.compile(r"(```[\s\S]*?```|`[^`\n]+`)")


def _is_allowed_image(url: str, options: SanitizeOptions) -> bool:
    if not options.allowed_image_prefixes:
        return False
    raw = (url or "").strip()
    if not raw:
        return False
    normalized = urljoin(options.default_origin, raw)
    lower = normalized.lower()
    if lower.startswith(("javascript:", "vbscript:", "data:")):
        return False
    return any(normalized.startswith(p) for p in options.allowed_image_prefixes)


def _image_url_from_md_parens(inner: str) -> str:
    """Extract the URL from the inside of markdown image parentheses."""
    inner = inner.strip()
    if not inner:
        return ""
    if inner.startswith("<"):
        end = inner.find(">")
        if end != -1:
            return inner[1:end].strip()
        return inner[1:].strip()
    # Title-only remnant: ![alt]( "title") — empty destination
    if inner[0] in "\"'":
        return ""
    # URL ends at first whitespace before an optional title
    parts = inner.split(None, 1)
    return parts[0] if parts else ""


def _sanitize_html(html: str, options: SanitizeOptions) -> str:
    html = _CDATA_RE.sub("", html)
    soup = BeautifulSoup(html, "html.parser")

    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    for tag in soup.find_all(_DROP_TAGS):
        tag.decompose()

    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue
        src = img.get("src") or ""
        if _is_allowed_image(src, options):
            # keep only safe attrs
            alt = img.get("alt", "")
            if not isinstance(alt, str):
                alt = " ".join(alt)
            # neutralize angle brackets so markdownify cannot re-emit raw HTML
            alt = alt.replace("<", "").replace(">", "")
            src = urljoin(options.default_origin, src.strip())
            img.attrs = {"src": src, "alt": alt}
        else:
            # no fetch — leave plain alt text if any (never reintroduce tags)
            alt = img.get("alt") or ""
            if not isinstance(alt, str):
                alt = " ".join(alt)
            alt = BeautifulSoup(alt, "html.parser").get_text().strip()
            alt = alt.replace("<", "").replace(">", "")
            if alt:
                img.replace_with(alt)
            else:
                img.decompose()

    return str(soup)


def _escape_raw_html_in_markdown(markdown: str) -> str:
    """Stop markdownify round-trips from turning text into raw HTML tags."""
    parts = _FENCE_OR_CODE_RE.split(markdown)
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
        else:
            out.append(_RAW_HTML_LT_RE.sub("&lt;", part))
    return "".join(out)


def _filter_markdown_images(markdown: str, options: SanitizeOptions) -> str:
    """Drop markdown images whose URLs fail the allow-list (parser leftovers)."""

    def repl(match: re.Match[str]) -> str:
        alt, inner = match.group(1), match.group(2)
        url = _image_url_from_md_parens(inner)
        if _is_allowed_image(url, options):
            return match.group(0)
        return alt

    parts = _FENCE_OR_CODE_RE.split(markdown)
    out: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
        else:
            out.append(_MD_IMAGE_RE.sub(repl, part))
    return "".join(out)


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
        md = _escape_raw_html_in_markdown(md)
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
