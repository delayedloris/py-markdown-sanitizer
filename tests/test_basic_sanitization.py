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
        out = sanitize("![Alt](https://images.com/photo.jpg)")
        assert "https://images.com/photo.jpg" in out
        assert "![" in out

    def test_blocks_other_hosts(self):
        out = sanitize("![Evil](https://evil.com/t.gif)")
        assert "evil.com" not in out
        assert "Evil" in out

    def test_blocks_when_allow_list_empty(self):
        out = sanitize("![x](https://images.com/a.png)", prefixes=[])
        assert "images.com" not in out
        assert "x" in out

    def test_relative_resolved(self):
        out = sanitize("![Local](/images/local.png)")
        assert "https://example.com/images/local.png" in out

    def test_data_uri_blocked(self):
        out = sanitize("![x](data:image/gif;base64,R0lGOD)")
        assert "data:" not in out


class TestZeroClickHtml:
    def test_strips_raw_img(self):
        out = sanitize('<img src="https://evil.com/t.png">')
        assert "evil.com" not in out

    def test_strips_iframe(self):
        out = sanitize('<iframe src="https://evil.com"></iframe>')
        assert "iframe" not in out.lower()
        assert "evil.com" not in out


class TestLinksUntouched:
    def test_links_pass_through(self):
        out = sanitize("[click](https://evil.com/steal)")
        assert "https://evil.com/steal" in out
        assert "click" in out
