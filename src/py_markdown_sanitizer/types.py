from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SanitizeOptions:
    """Image allow-list for blocking zero-click exfiltration."""

    allowed_image_prefixes: list[str] = field(default_factory=list)
    """Only image URLs with these prefixes are kept. Empty = block all images."""

    default_origin: str = "https://localhost"
    """Base origin for resolving relative image URLs."""
