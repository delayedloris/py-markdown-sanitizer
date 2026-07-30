"""Fuzz: random markdown must not leave image tags when the allow-list is empty."""

from __future__ import annotations

import hashlib
from pathlib import Path

import mistune
from bs4 import BeautifulSoup
from hypothesis import given, settings
from hypothesis import strategies as st

from py_markdown_sanitizer import sanitize_markdown
from tests.vercel.test_bypass_attempts import _md as _bypass_md
from tests.vercel.test_bypass_attempts import _sanitize as _bypass_sanitize
from tests.vercel.test_bypass_attempts import validate_html

BYPASS_DIR = Path(__file__).resolve().parent / "fixtures" / "bypass-attempts"

# Aggressive consumer: same plugins as the sanitizer, no HTML escaping.
_md = mistune.create_markdown(
    escape=False,
    plugins=["strikethrough", "table", "url", "task_lists"],
)

_SAFE_TEXT = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Zs"),
        blacklist_characters="`<>![]()#",
    ),
    min_size=0,
    max_size=40,
)

_URLS = st.one_of(
    st.sampled_from(
        [
            "https://evil.com/t.png",
            "http://evil.com/t.png",
            "https://example.com/ok.png",
            "//evil.com/t.png",
            "/relative.png",
            "./local.png",
            "javascript:alert(1)",
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
            "vbscript:msgbox(1)",
            "https://evil.com/a.png?x=1&y=2",
            "https://evil.com/a.png#frag",
            "HTTPS://EVIL.COM/T.PNG",
            "https://evil.com/t.png ",
            " https://evil.com/t.png",
        ]
    ),
    st.from_regex(r"https?://[a-z0-9.-]{1,20}/[a-z0-9._/-]{0,30}", fullmatch=True),
)

_ALTS = st.one_of(_SAFE_TEXT, st.sampled_from(["", "alt", "x y", "a]b", "图片"]))


@st.composite
def markdown_image(draw) -> str:
    alt, url = draw(_ALTS), draw(_URLS)
    kind = draw(st.integers(0, 5))
    if kind == 0:
        return f"![{alt}]({url})"
    if kind == 1:
        return f'![{alt}]({url} "title")'
    if kind == 2:
        return f"![{alt}](<{url}>)"
    if kind == 3:
        return f'<img src="{url}" alt="{alt}">'
    if kind == 4:
        return f"<IMG SRC='{url}' ALT='{alt}' />"
    ref = draw(st.sampled_from(["ref", "id1", "x"]))
    return f"![{alt}][{ref}]\n\n[{ref}]: {url}"


@st.composite
def random_markdown(draw) -> str:
    """Mix plain text with image-like fragments (md + raw HTML)."""
    parts = draw(
        st.lists(
            st.one_of(_SAFE_TEXT, markdown_image(), st.just("\n"), st.just(" ")),
            min_size=1,
            max_size=12,
        )
    )
    return "".join(parts)


def find_surviving_images(markdown: str) -> list[str]:
    """Lenient HTML parse after markdown render — catches odd/malformed <img> tags."""
    html = _md(markdown)
    soup = BeautifulSoup(html, "html.parser")
    return [str(img) for img in soup.find_all("img")]


def record_bypass_fixture(md: str) -> Path | None:
    """Write a case only if the bypass suite would also fail; dedupe by issues."""
    issues = validate_html(_bypass_md(_bypass_sanitize(md)))
    if not issues:
        return None
    key = hashlib.sha1("\n".join(issues).encode()).hexdigest()[:10]
    path = BYPASS_DIR / f"hypothesis-{key}.md"
    # Prefer shorter input for the same failure signature.
    if path.exists() and len(path.read_text(encoding="utf-8")) <= len(md):
        return path
    path.write_text(md, encoding="utf-8")
    return path


def assert_no_surviving_images(md: str) -> None:
    sanitized = sanitize_markdown(md, allowed_image_prefixes=[])
    survivors = find_surviving_images(sanitized)
    if survivors:
        path = record_bypass_fixture(md)
        note = f"wrote {path.name}" if path else "bypass suite does not fail"
        raise AssertionError(
            f"images survived; {note}\n{survivors}\n---\n{sanitized!r}"
        )


@given(random_markdown())
@settings(max_examples=200, deadline=None)
def test_empty_allowlist_no_images_survive(md: str):
    assert_no_surviving_images(md)
