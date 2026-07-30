from __future__ import annotations

import re
from urllib.parse import urljoin

from .types import SanitizeOptions

# ![alt](url) and ![alt](url "title")
_INLINE_IMAGE = re.compile(
    r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:[^)]*)?\)"
)

# ![alt][ref] or ![alt] shortcut — not ![alt](url)
_REF_IMAGE = re.compile(r"!\[([^\]]*)\](?:\[([^\]]*)\])?(?!\()")

# [ref]: url
_REF_DEF = re.compile(
    r"^\[([^\]]+)\]:\s*<?([^\s>]+)>?",
    re.MULTILINE,
)

# Auto-loading HTML — fetched without a click
_AUTOLOAD_HTML = re.compile(
    r"</?(?:img|iframe|embed|object|video|audio|source|track|link|script|svg)\b[^>]*>",
    re.IGNORECASE,
)


def _is_allowed_image(url: str, options: SanitizeOptions) -> bool:
    prefixes = options.allowed_image_prefixes
    if not prefixes:
        return False
    try:
        normalized = urljoin(options.default_origin, url.strip())
    except ValueError:
        return False
    # Reject obvious non-http(s) schemes that still auto-fetch or are useless
    lower = normalized.lower()
    if lower.startswith(("javascript:", "vbscript:", "data:")):
        return False
    return any(normalized.startswith(p) for p in prefixes)


class MarkdownSanitizer:
    def __init__(self, options: SanitizeOptions | None = None) -> None:
        self.options = options or SanitizeOptions()

    def sanitize(self, markdown: str) -> str:
        refs = {m.group(1): m.group(2) for m in _REF_DEF.finditer(markdown)}

        def replace_inline(m: re.Match) -> str:
            alt, url = m.group(1), m.group(2)
            if _is_allowed_image(url, self.options):
                return m.group(0)
            return alt  # drop fetch, keep text

        # Inline images first so we don't double-process their ![
        out = _INLINE_IMAGE.sub(replace_inline, markdown)

        def replace_ref(m: re.Match) -> str:
            alt, ref = m.group(1), m.group(2)
            key = ref if ref is not None else alt
            # Bare ![alt] with no [] is shortcut ref; ![alt][] uses alt as key
            if ref == "":
                key = alt
            url = refs.get(key)
            if url is None:
                return m.group(0)  # not a resolvable image ref
            if _is_allowed_image(url, self.options):
                return m.group(0)
            return alt

        out = _REF_IMAGE.sub(replace_ref, out)
        out = _AUTOLOAD_HTML.sub("", out)
        return out


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
