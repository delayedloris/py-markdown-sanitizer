from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SanitizeOptions:
    """Image allow-list for blocking zero-click exfiltration."""

    allowed_image_prefixes: list[str] = field(default_factory=list)
    """Only these image URL prefixes stay as images. Empty = all images → links."""

    default_origin: str = "https://localhost"
    """Base origin for resolving relative image URLs."""
