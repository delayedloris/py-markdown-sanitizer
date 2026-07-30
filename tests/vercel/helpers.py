"""Helpers mirroring Vercel markdown-to-markdown-sanitizer test defaults."""

from __future__ import annotations

from py_markdown_sanitizer import sanitize_markdown


def sanitize(
    input_md: str,
    *,
    allowed_image_prefixes: list[str] | None = None,
    default_origin: str = "https://example.com",
) -> str:
    """Default allow-lists match Vercel basic-sanitization.test.ts."""
    return sanitize_markdown(
        input_md,
        allowed_image_prefixes=allowed_image_prefixes
        if allowed_image_prefixes is not None
        else ["https://example.com", "https://images.com"],
        default_origin=default_origin,
    )
