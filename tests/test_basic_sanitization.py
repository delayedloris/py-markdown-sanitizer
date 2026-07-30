from py_markdown_sanitizer import sanitize_markdown


def sanitize(md: str, prefixes: list[str] | None = None) -> str:
    return sanitize_markdown(
        md,
        allowed_image_prefixes=prefixes
        if prefixes is not None
        else ["https://images.com/", "https://example.com/"],
        default_origin="https://example.com",
    )


class TestImages:
    def test_allows_whitelisted(self):
        assert (
            sanitize("![Alt](https://images.com/photo.jpg)")
            == "![Alt](https://images.com/photo.jpg)"
        )

    def test_blocks_other_hosts(self):
        assert sanitize("![Evil](https://evil.com/t.gif)") == "Evil"

    def test_blocks_when_allow_list_empty(self):
        assert sanitize("![x](https://images.com/a.png)", prefixes=[]) == "x"

    def test_relative_resolved_against_origin(self):
        assert (
            sanitize("![Local](/images/local.png)")
            == "![Local](/images/local.png)"
        )

    def test_data_uri_blocked(self):
        assert sanitize("![x](data:image/gif;base64,R0lGOD)") == "x"

    def test_reference_image_blocked(self):
        md = "![Alt][id]\n\n[id]: https://evil.com/t.png\n"
        assert "evil.com" not in sanitize(md).split("[id]:")[0]
        assert sanitize(md).startswith("Alt")


class TestZeroClickHtml:
    def test_strips_img_tags(self):
        assert "<img" not in sanitize('<img src="https://evil.com/t.png">').lower()

    def test_strips_iframe(self):
        assert "iframe" not in sanitize('<iframe src="https://evil.com"></iframe>').lower()


class TestLinksUntouched:
    def test_links_pass_through(self):
        md = "[click](https://evil.com/steal)"
        assert sanitize(md) == md
