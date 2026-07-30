from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit, urljoin

from .types import SanitizeOptions

_PROTOCOL_ONLY = re.compile(r"^[a-z][a-z0-9+.-]*:$", re.I)
_PROTOCOL_WITH_SLASHES = re.compile(r"^[a-z][a-z0-9+.-]*://$", re.I)
_MD_URL_CHARS = re.compile(r"[!()\[\]`]")


def _normalize_href(url: str, base: str | None = None) -> str:
    """Approximate WHATWG URL href normalization."""
    href = urljoin(base, url) if base else url
    parts = urlsplit(href)
    if not parts.scheme:
        raise ValueError("invalid URL")
    path = parts.path
    if parts.scheme in ("http", "https") and parts.netloc and path == "":
        path = "/"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def try_parse_url(url: str, default_origin: str | None = None) -> urlsplit | None:
    try:
        href = _normalize_href(url, default_origin)
        return urlsplit(href)
    except (ValueError, TypeError):
        return None


class UrlNormalizer:
    def __init__(self, options: SanitizeOptions) -> None:
        self.options = options
        if self.options.url_max_length is None:
            self.options.url_max_length = 200

    def normalize_url(self, url: str, default_origin: str | None = None) -> str:
        try:
            normalized = _normalize_href(url, default_origin)
            max_len = self.options.url_max_length
            if max_len and len(normalized) > max_len:
                return ""
            return _MD_URL_CHARS.sub(lambda m: f"%{ord(m.group(0)):x}", normalized)
        except (ValueError, TypeError):
            return ""

    def _is_allowed(
        self,
        normalized_url: str,
        default_origin: str,
        allowed_prefixes: list[str],
    ) -> bool:
        if not normalized_url:
            return False

        for prefix in allowed_prefixes:
            if _PROTOCOL_ONLY.match(prefix):
                if normalized_url.lower().startswith(prefix.lower() + "//"):
                    return True
                continue

            if _PROTOCOL_WITH_SLASHES.match(prefix):
                if normalized_url.lower().startswith(prefix.lower()):
                    return True
                continue

            normalized_prefix = self.normalize_url(prefix, default_origin)
            if not normalized_prefix:
                continue
            prefix_parts = try_parse_url(normalized_prefix, default_origin)
            url_parts = try_parse_url(normalized_url, default_origin)
            if not prefix_parts or not url_parts:
                continue
            prefix_origin = f"{prefix_parts.scheme}://{prefix_parts.netloc}"
            url_origin = f"{url_parts.scheme}://{url_parts.netloc}"
            if prefix_origin != url_origin:
                continue
            if normalized_url.startswith(normalized_prefix):
                return True
        return False

    def is_allowed_url(self, normalized_url: str) -> bool:
        origin = self.options.default_link_origin or self.options.default_origin
        return self._is_allowed(
            normalized_url, origin, self.options.allowed_link_prefixes or []
        )

    def is_allowed_image_url(self, normalized_url: str) -> bool:
        origin = self.options.default_image_origin or self.options.default_origin
        return self._is_allowed(
            normalized_url, origin, self.options.allowed_image_prefixes or []
        )

    def sanitize_url(self, url: str, url_type: str) -> str:
        link_origin = self.options.default_link_origin or self.options.default_origin
        image_origin = self.options.default_image_origin or self.options.default_origin

        if url_type == "href" and url.startswith("#"):
            parsed = try_parse_url(url, link_origin)
            if parsed is not None:
                hash_part = f"#{parsed.fragment}" if parsed.fragment else ""
                if hash_part == url:
                    return url

        default_origin = image_origin if url_type == "src" else link_origin
        normalized_url = self.normalize_url(url, default_origin)

        if url_type == "src":
            if not self.is_allowed_image_url(normalized_url):
                return "/forbidden"
        else:
            if not self.is_allowed_url(normalized_url):
                return "#"

        return normalized_url
