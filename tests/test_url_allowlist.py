"""Adversarial allow-list checks: host/userinfo/path must not ride prefixes."""

from __future__ import annotations

import pytest

from py_markdown_sanitizer import sanitize_markdown
from tests.vercel.test_bypass_attempts import _md, validate_html

PREFIXES = [
    "https://example.com",
    "https://images.com",
    "https://prefix.com/prefix/",
]


def _sanitize(md: str) -> str:
    return sanitize_markdown(
        md,
        allowed_image_prefixes=PREFIXES,
        default_origin="https://example.com",
    )


def _assert_blocked(md: str) -> None:
    out = _sanitize(md)
    assert validate_html(_md(out)) == []
    assert "![" not in out


@pytest.mark.parametrize(
    "md",
    [
        "![x](https://example.com.evil.com/t.png)",
        '<img src="https://example.com.evil.com/t.png">',
        "![x](https://example.com@evil.com/t.png)",
        '<img src="https://example.com@evil.com/t.png">',
        "![x](https://example.com:443@evil.com/t.png)",
        r"![x](https://example.com\@evil.com/t.png)",
        "![x](https://example.com%40evil.com/t.png)",
        "![x](https://example.com%2eevil.com/t.png)",
        "![x](https://example.com%2Eevil.com/t.png)",
        "![x](https://prefix.com/prefix/../secret.png)",
        "![x](https://prefix.com/prefix/%2e%2e/secret.png)",
        "![x](https://prefix.com/prefixX.png)",
        "![x](http://example.com/t.png)",
        "![x](//evil.com/t.png)",
    ],
)
def test_blocks_prefix_confusion(md: str):
    _assert_blocked(md)


@pytest.mark.parametrize(
    "md,needle",
    [
        ("![x](https://images.com/a.png)", "https://images.com/a.png"),
        ("![x](https://example.com/a.png)", "https://example.com/a.png"),
        ("![x](https://prefix.com/prefix/a.png)", "https://prefix.com/prefix/a.png"),
        (
            "![x](https://prefix.com/prefix/foo/../bar.png)",
            "https://prefix.com/prefix/",
        ),
        ("![x](/ok.png)", "https://example.com/ok.png"),
        (
            '<img src="https://images.com/safe.jpg" alt="Safe">',
            "https://images.com/safe.jpg",
        ),
    ],
)
def test_keeps_genuine_allows(md: str, needle: str):
    out = _sanitize(md)
    assert needle in out
    assert validate_html(_md(out)) == []
