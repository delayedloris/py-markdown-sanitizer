"""Port of Vercel basic-sanitization.test.ts — adapted to image-only scope."""

from tests.vercel.helpers import sanitize


class TestImageSanitization:
    def test_allows_trusted_images(self):
        result = sanitize("![Alt text](https://images.com/photo.jpg)")
        assert "https://images.com/photo.jpg" in result
        assert "![" in result

    def test_blocks_untrusted_images(self):
        result = sanitize("![Evil](https://evil.com/tracker.gif)")
        assert "evil.com" not in result
        assert "Evil" in result

    def test_handles_relative_image_paths(self):
        result = sanitize("![Local](/images/local.png)")
        assert "https://example.com/images/local.png" in result

    def test_blocks_data_uri_images(self):
        result = sanitize("![Important Image](data:image/gif;base64,R0lGOD)")
        assert "data:" not in result


class TestLinksPassThrough:
    def test_allows_trusted_links(self):
        result = sanitize("[Click here](https://example.com/page)")
        assert "https://example.com/page" in result
        assert "Click here" in result

    def test_links_to_evil_pass_through(self):
        result = sanitize("[Malicious](https://evil.com/steal)")
        assert "https://evil.com/steal" in result


class TestMixedContent:
    def test_handles_text_with_links_and_images(self):
        input_md = """# Title

Here is a [link](https://example.com/page) and an image ![img](https://images.com/pic.jpg).

Also a bad [link](https://evil.com) and bad ![image](https://evil.com/tracker.gif)."""
        result = sanitize(input_md)
        assert "https://example.com/page" in result
        assert "https://images.com/pic.jpg" in result
        assert "https://evil.com/tracker.gif" not in result
        assert "https://evil.com" in result


class TestEdgeCases:
    def test_handles_empty_input(self):
        assert sanitize("") == ""

    def test_handles_whitespace_only(self):
        assert sanitize("   \n   ") == ""

    def test_handles_plain_text_without_markdown(self):
        result = sanitize("Just plain text with no markdown.")
        assert "Just plain text with no markdown" in result

    def test_handles_malformed_markdown_gracefully(self):
        result = sanitize("[Incomplete link without closing paren](https://example.com")
        assert result is not None

    def test_handles_nested_brackets(self):
        result = sanitize("[[Nested] brackets](https://example.com)")
        assert "https://example.com" in result

    def test_handles_urls_with_special_characters(self):
        result = sanitize(
            "[Link](https://example.com/path?query=value&other=123#fragment)"
        )
        assert "https://example.com/path?query=value&other=123#fragment" in result


class TestReferenceStyle:
    def test_handles_reference_style_images(self):
        input_md = "![alt][ref]\n\n[ref]: https://images.com/photo.jpg"
        result = sanitize(input_md)
        assert "https://images.com/photo.jpg" in result

    def test_blocks_reference_style_untrusted_images(self):
        input_md = "![alt][ref]\n\n[ref]: https://evil.com/t.gif"
        result = sanitize(input_md)
        assert "evil.com" not in result
