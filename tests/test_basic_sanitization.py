from py_markdown_sanitizer import MarkdownSanitizer, SanitizeOptions


def sanitize(input_md: str, **overrides) -> str:
    opts = {
        "default_origin": "https://example.com",
        "allowed_link_prefixes": ["https://example.com", "https://trusted.org"],
        "allowed_image_prefixes": ["https://example.com", "https://images.com"],
    }
    opts.update(overrides)
    return MarkdownSanitizer(SanitizeOptions(**opts)).sanitize(input_md)


class TestLinkSanitization:
    def test_allows_hash_only_anchors(self):
        assert sanitize(
            "[Jump to section](#hero)",
            allowed_link_prefixes=["https://example.com/blog"],
        ) == "[Jump to section](#hero)\n"

    def test_allows_hash_with_no_prefixes(self):
        assert (
            sanitize("[Jump to top](#top)", allowed_link_prefixes=[])
            == "[Jump to top](#top)\n"
        )

    def test_allows_trusted_links(self):
        assert (
            sanitize("[Click here](https://example.com/page)")
            == "[Click here](https://example.com/page)\n"
        )

    def test_blocks_untrusted_links(self):
        assert sanitize("[Malicious](https://evil.com/steal)") == "[Malicious](#)\n"

    def test_relative_links_use_default_origin(self):
        assert (
            sanitize("[Relative](/path/to/page)")
            == "[Relative](https://example.com/path/to/page)\n"
        )

    def test_multiple_links(self):
        assert (
            sanitize(
                "[Good](https://example.com/good) and [Bad](https://evil.com/bad)"
            )
            == "[Good](https://example.com/good) and [Bad](#)\n"
        )

    def test_javascript_url_strips_link(self):
        result = sanitize('[Important Info](javascript:alert("xss"))')
        assert "javascript:" not in result.lower()
        assert "Important Info" in result


class TestImageSanitization:
    def test_allows_trusted_images(self):
        assert (
            sanitize("![Alt text](https://images.com/photo.jpg)")
            == "![](https://images.com/photo.jpg)\n"
        )

    def test_blocks_untrusted_images(self):
        assert sanitize("![Evil](https://evil.com/tracker.gif)") == "![](/forbidden)\n"

    def test_relative_images(self):
        assert (
            sanitize("![Local](/images/local.png)")
            == "![](https://example.com/images/local.png)\n"
        )

    def test_data_uri_blocked(self):
        assert (
            sanitize("![Important Image](data:image/gif;base64,R0lGOD)")
            == "![](/forbidden)\n"
        )


class TestEdgeCases:
    def test_empty(self):
        assert sanitize("") == ""

    def test_plain_text_entity_encodes_dot(self):
        assert (
            sanitize("Just plain text with no markdown.")
            == "Just plain text with no markdown&2e;\n"
        )

    def test_long_url_blocked(self):
        long_url = "https://example.com/" + "a" * 300
        assert sanitize(f"[Link]({long_url})") == "[Link](#)\n"

    def test_protocol_relative(self):
        assert (
            sanitize("[Link](//example.com/path)")
            == "[Link](https://example.com/path)\n"
        )

    def test_requires_default_origin(self):
        try:
            MarkdownSanitizer(SanitizeOptions(default_origin=""))
            assert False, "expected ValueError"
        except ValueError:
            pass
