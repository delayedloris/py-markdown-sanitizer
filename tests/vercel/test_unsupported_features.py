"""Document Vercel features we do not implement (skipped)."""

import pytest

from tests.exclusions import VERCEL_SKIP_REASONS


@pytest.mark.skip(reason=VERCEL_SKIP_REASONS["max_markdown_length"])
def test_max_markdown_length_config():
    raise AssertionError("not implemented")


@pytest.mark.skip(reason=VERCEL_SKIP_REASONS["url_length"])
def test_url_max_length_config():
    raise AssertionError("not implemented")


@pytest.mark.skip(reason=VERCEL_SKIP_REASONS["commonmark_escape_mode"])
def test_sanitize_for_commonmark_mode():
    raise AssertionError("not implemented")


@pytest.mark.skip(reason=VERCEL_SKIP_REASONS["entity_escaping"])
def test_entity_escaping_output():
    raise AssertionError("not implemented")
