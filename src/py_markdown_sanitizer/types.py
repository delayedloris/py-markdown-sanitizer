from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SanitizeOptions:
    """Configuration for markdown sanitization."""

    default_origin: str
    allowed_link_prefixes: list[str] = field(default_factory=list)
    allowed_image_prefixes: list[str] = field(default_factory=list)
    default_link_origin: str | None = None
    default_image_origin: str | None = None
    url_max_length: int | None = None
    max_markdown_length: int | None = None
    sanitize_for_commonmark: bool = False
