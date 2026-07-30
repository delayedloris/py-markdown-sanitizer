from __future__ import annotations

import logging
import re

import mistune
from markdownify import ATX, MarkdownConverter
from mistune.renderers.html import HTMLRenderer

from .html_sanitizer import HtmlSanitizer
from .types import SanitizeOptions
from .url_normalizer import UrlNormalizer

logger = logging.getLogger(__name__)

_MARKDOWN_SYNTAX_CHARS = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
_ENTITY_ESCAPE_CHARS = re.compile(r"""[<>&"'\[\]:=/!()\\@.]""")


def commonmark_escape(s: str) -> str:
    """Escape markdown syntax characters per CommonMark (backslash escapes)."""
    result: list[str] = []
    i = 0
    while i < len(s):
        char = s[i]
        if char == "\\":
            if i + 1 < len(s) and s[i + 1] == "\\":
                result.append("\\\\")
                i += 2
                continue
            if i + 1 < len(s) and s[i + 1] in _MARKDOWN_SYNTAX_CHARS:
                result.append(s[i] + s[i + 1])
                i += 2
                continue
            result.append(char)
            i += 1
        elif char in _MARKDOWN_SYNTAX_CHARS:
            result.append("\\" + char)
            i += 1
        else:
            result.append(char)
            i += 1
    return "".join(result)


class _SanitizingConverter(MarkdownConverter):
    """Turndown-equivalent converter with aggressive entity escaping."""

    def __init__(self, sanitize_for_commonmark: bool = False, **options):
        self._sanitize_for_commonmark = sanitize_for_commonmark
        super().__init__(**options)

    def escape(self, text, parent_tags):
        if not text:
            return ""
        if self._sanitize_for_commonmark:
            return commonmark_escape(text)
        if _ENTITY_ESCAPE_CHARS.search(text):
            return "".join(
                f"&{ord(c):x};" if _ENTITY_ESCAPE_CHARS.match(c) else c for c in text
            )
        return super().escape(text, parent_tags)


class MarkdownSanitizer:
    def __init__(self, options: SanitizeOptions) -> None:
        if not options.default_origin:
            raise ValueError("default_origin is required")
        self.options = options

        renderer = HTMLRenderer(escape=False, allow_harmful_protocols=True)
        self._md_to_html = mistune.create_markdown(
            renderer=renderer,
            plugins=["strikethrough", "table", "url", "task_lists"],
        )

        self._html_to_md = _SanitizingConverter(
            sanitize_for_commonmark=options.sanitize_for_commonmark,
            heading_style=ATX,
            bullets="-",
            strong_em_symbol="*",
            escape_asterisks=False,
            escape_underscores=False,
            escape_misc=False,
        )

        self.url_normalizer = UrlNormalizer(options)
        self.html_sanitizer = HtmlSanitizer(self.url_normalizer)

    def sanitize(self, markdown: str) -> str:
        max_length = (
            100_000
            if self.options.max_markdown_length is None
            else self.options.max_markdown_length
        )
        if max_length > 0 and len(markdown) > max_length:
            markdown = markdown[:max_length]

        try:
            html = self._md_to_html(markdown)
            sanitized_html = self.html_sanitizer.sanitize_html(html)
            result = self._html_to_md.convert(sanitized_html)
            if result and not result.endswith("\n"):
                result += "\n"
            return result
        except Exception:
            logger.exception("Markdown sanitization failed")
            return ""


def sanitize_markdown(markdown: str, options: SanitizeOptions) -> str:
    return MarkdownSanitizer(options).sanitize(markdown)
