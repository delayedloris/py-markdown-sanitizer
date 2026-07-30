from __future__ import annotations

from urllib.parse import urljoin

import mistune
from bs4 import BeautifulSoup, Tag
from markdownify import ATX, markdownify
from mistune.renderers.html import HTMLRenderer

from .types import SanitizeOptions

_AUTOLOAD_TAGS = frozenset(
    {"iframe", "embed", "object", "video", "audio", "source", "track", "script", "svg"}
)
# <link> can prefetch; keep only if it has no href fetch risk — simpler to drop all
_DROP_TAGS = _AUTOLOAD_TAGS | {"link"}


def _is_allowed_image(url: str, options: SanitizeOptions) -> bool:
    if not options.allowed_image_prefixes:
        return False
    normalized = urljoin(options.default_origin, (url or "").strip())
    lower = normalized.lower()
    if lower.startswith(("javascript:", "vbscript:", "data:")):
        return False
    return any(normalized.startswith(p) for p in options.allowed_image_prefixes)


def _sanitize_html(html: str, options: SanitizeOptions) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(_DROP_TAGS):
        tag.decompose()

    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue
        src = img.get("src") or ""
        if _is_allowed_image(src, options):
            # keep only safe attrs
            alt = img.get("alt", "")
            img.attrs = {"src": urljoin(options.default_origin, src.strip()), "alt": alt}
        else:
            # no fetch — leave alt text if any
            alt = (img.get("alt") or "").strip()
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
        return markdownify(clean, heading_style=ATX).rstrip() + (
            "\n" if clean.strip() else ""
        )


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
