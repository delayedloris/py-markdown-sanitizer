"""Port of Vercel bypass-attempts.test.ts (image / auto-load threat model)."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import mistune
import pytest
from bs4 import BeautifulSoup

from py_markdown_sanitizer import sanitize_markdown

BYPASS_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bypass-attempts"

ALLOWED_ELEMENTS = {
    "a",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "img",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "hr",
    "table",
    "tbody",
    "thead",
    "tfoot",
    "tr",
    "td",
    "th",
    "span",
    "br",
    "div",
    "html",
    "body",
    "head",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "s",
    "sup",
    "sub",
    "small",
    "big",
    "del",
    "strike",
    "input",
}
ALLOWED_ATTRIBUTES = {
    "href",
    "src",
    "alt",
    "title",
    "class",
    "type",
    "checked",
    "disabled",
    "start",
}
TRUSTED_ORIGINS = (
    "https://example.com",
    "https://trusted.org",
    "https://images.com",
    "https://prefix.com",
)
PREFIX_PATH = "https://prefix.com/prefix/"

_md = mistune.create_markdown(
    escape=False,
    plugins=["strikethrough", "table", "url", "task_lists"],
)


def _is_dangerous_src(url: str) -> str | None:
    if url in {"/forbidden", "#"} or url.startswith("#"):
        return None
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return "bad protocol"
    if not parsed.scheme:
        # relative / opaque leftovers
        if url.startswith("/") or url.startswith("./"):
            return "untrusted relative"
        return "bad protocol"
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin == "https://prefix.com":
        if not url.startswith(PREFIX_PATH):
            return "prefix bypass"
        return None
    if not any(url.startswith(t) for t in TRUSTED_ORIGINS):
        return "untrusted origin"
    return None


def validate_html(html: str) -> list[str]:
    """Like Vercel validateHtml, but skip href checks (links pass through)."""
    soup = BeautifulSoup(html, "html.parser")
    issues: list[str] = []

    for el in soup.find_all(True):
        name = el.name.lower()
        if name not in ALLOWED_ELEMENTS:
            issues.append(f"Forbidden element: {name}")
        for attr, value in el.attrs.items():
            attr_l = attr.lower()
            if attr_l not in ALLOWED_ATTRIBUTES:
                issues.append(f"Illegal attribute: {attr}")
            if attr_l == "src":
                src = value if isinstance(value, str) else " ".join(value)
                reason = _is_dangerous_src(src)
                if reason:
                    issues.append(f"Dangerous src ({reason}): {src}")
    return issues


def _sanitize(markdown: str) -> str:
    return sanitize_markdown(
        markdown,
        allowed_image_prefixes=[
            "https://example.com",
            "https://images.com",
            "https://prefix.com/prefix/",
        ],
        default_origin="https://example.com",
    )


def _bypass_files() -> list[str]:
    return sorted(p.name for p in BYPASS_DIR.glob("*.md"))


@pytest.mark.parametrize("filename", _bypass_files())
def test_bypass_attempt(filename: str):
    markdown = (BYPASS_DIR / filename).read_text(encoding="utf-8")
    sanitized = _sanitize(markdown)
    html = _md(sanitized)
    assert validate_html(html) == []


class TestValidateHtmlSanity:
    def test_detects_script(self):
        assert any("script" in i.lower() for i in validate_html("<script>x</script>"))

    def test_detects_iframe(self):
        assert any(
            "iframe" in i.lower()
            for i in validate_html('<iframe src="https://example.com"></iframe>')
        )

    def test_detects_bad_image_src(self):
        issues = validate_html('<img src="https://evil.com/xss.png">')
        assert any("untrusted" in i for i in issues)

    def test_allows_trusted_image(self):
        assert validate_html('<img src="https://images.com/a.png" alt="a">') == []
