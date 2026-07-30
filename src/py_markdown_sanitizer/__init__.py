"""Sanitize markdown against zero-click image exfiltration."""

from .sanitizer import MarkdownSanitizer, sanitize_markdown
from .types import SanitizeOptions

__all__ = ["MarkdownSanitizer", "SanitizeOptions", "sanitize_markdown"]
