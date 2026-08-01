"""Selected ports from Vercel edge-cases/*.test.ts."""

from tests.vercel.helpers import sanitize


class TestWeirdParsing:
    def test_unclosed_image(self):
        # mistune won't parse an unclosed image; leftover text may still mention the URL
        result = sanitize("![alt](https://evil.com/t.png")
        assert result is not None
        assert "<img" not in result.lower()

    def test_nested_brackets_in_alt(self):
        result = sanitize("![a [b] c](https://images.com/a.png)")
        assert "https://images.com/a.png" in result

    def test_image_with_title(self):
        result = sanitize('![alt](https://images.com/a.png "title")')
        assert "https://images.com/a.png" in result

    def test_unicode_in_alt(self):
        result = sanitize("![图片](https://images.com/a.png)")
        assert "https://images.com/a.png" in result

    def test_empty_alt_blocked_image(self):
        result = sanitize("![](https://evil.com/t.png)")
        assert "![" not in result
        assert "https://evil.com/t.png" in result


class TestMalformedMarkdown:
    def test_does_not_crash_on_heavy_nesting(self):
        md = "[" * 50 + "x" + "]" * 50 + "(https://example.com)"
        assert sanitize(md) is not None

    def test_null_bytes_tolerated(self):
        result = sanitize("![x](https://images.com/a.png\x00)")
        assert result is not None

    def test_mixed_html_comment_and_image(self):
        result = sanitize(
            "<!-- ![x](https://evil.com/t.png) -->\n![y](https://images.com/a.png)"
        )
        assert "https://images.com/a.png" in result
