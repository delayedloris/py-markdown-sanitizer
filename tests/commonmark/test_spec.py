"""CommonMark 0.31.2: sanitize must not change CM-rendered HTML (excl. known gaps)."""

from __future__ import annotations

import json
from pathlib import Path

import commonmark
import pytest
from bs4 import BeautifulSoup

from py_markdown_sanitizer import sanitize_markdown
from tests.exclusions import COMMONMARK_EXCLUDE

SPEC_PATH = Path(__file__).with_name("spec.json")
_SPEC = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

_parser = commonmark.Parser()
_renderer = commonmark.HtmlRenderer()


def _norm(html: str) -> str:
    return BeautifulSoup(html, "html.parser").decode_contents().strip()


def _render(markdown: str) -> str:
    return _renderer.render(_parser.parse(markdown))


def _cases():
    for ex in _SPEC:
        yield pytest.param(
            ex,
            id=f"ex{ex['example']}-{ex['section'].replace(' ', '_')}",
        )


@pytest.mark.parametrize("example", list(_cases()))
def test_commonmark_sanitize_preserves_render(example: dict):
    num = example["example"]
    if num in COMMONMARK_EXCLUDE:
        pytest.skip("MD→HTML→MD round-trip differential")

    markdown = example["markdown"]
    before = _render(markdown)
    sanitized = sanitize_markdown(
        markdown,
        allowed_image_prefixes=["http://", "https://"],
        default_origin="http://example.com",
    )
    after = _render(sanitized)
    assert _norm(after) == _norm(before)


def test_exclusion_list_is_current():
    """Fail if exclusions are stale (too many or include passers)."""
    unexpected_pass = []
    unexpected_fail = []
    for ex in _SPEC:
        num = ex["example"]
        markdown = ex["markdown"]
        before = _render(markdown)
        sanitized = sanitize_markdown(
            markdown,
            allowed_image_prefixes=["http://", "https://"],
            default_origin="http://example.com",
        )
        after = _render(sanitized)
        ok = _norm(after) == _norm(before)
        if num in COMMONMARK_EXCLUDE and ok:
            unexpected_pass.append(num)
        if num not in COMMONMARK_EXCLUDE and not ok:
            unexpected_fail.append(num)
    assert unexpected_fail == [], f"new failures need exclusions: {unexpected_fail}"
    assert unexpected_pass == [], f"exclusions now pass, remove: {unexpected_pass}"
