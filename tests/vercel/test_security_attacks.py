"""Port of Vercel security-attacks.test.ts — image / auto-load focus."""

from tests.vercel.helpers import sanitize


class TestXssImageVectors:
    def test_blocks_javascript_protocol_in_images(self):
        attacks = [
            '![img](javascript:alert("xss"))',
            '![img](JAVASCRIPT:alert("xss"))',
            '![img](Javascript:alert("xss"))',
        ]
        for attack in attacks:
            result = sanitize(attack)
            assert "javascript:" not in result.lower()
            assert "![" not in result or "javascript" not in result.lower()

    def test_blocks_data_uri_images(self):
        # Angle brackets inside the URL break MD image parse; SVG tag is stripped.
        result = sanitize("![img](data:image/svg+xml,<svg onload=\"alert('xss')\"/>)")
        assert "onload" not in result.lower()
        assert "<svg" not in result.lower()
        result2 = sanitize("![img](data:image/gif;base64,R0lGOD)")
        assert "data:" not in result2

    def test_blocks_vbscript_in_images(self):
        result = sanitize('![img](vbscript:msgbox("xss"))')
        assert "vbscript:" not in result.lower()

    def test_blocks_file_protocol_images(self):
        result = sanitize("![Local file](file:///etc/passwd)")
        assert "file:" not in result


class TestHtmlInjection:
    def test_removes_script_tags(self):
        attacks = [
            '<script>alert("xss")</script>',
            '<SCRIPT>alert("xss")</SCRIPT>',
            '<script src="https://evil.com/xss.js"></script>',
        ]
        for attack in attacks:
            result = sanitize(attack)
            assert "<script" not in result.lower()
            assert "evil.com" not in result

    def test_removes_iframe_tags(self):
        result = sanitize('<iframe src="https://evil.com/embed"></iframe>')
        assert "iframe" not in result.lower()
        assert "evil.com" not in result

    def test_removes_object_and_embed(self):
        result = sanitize('<object data="malware.swf"></object><embed src="evil.exe">')
        assert "object" not in result.lower()
        assert "embed" not in result.lower()

    def test_removes_svg(self):
        result = sanitize('<svg onload="alert(1)"></svg>')
        assert "<svg" not in result.lower()

    def test_strips_raw_untrusted_img(self):
        result = sanitize('<img src="https://evil.com/tracker.gif" alt="t">')
        assert "evil.com" not in result

    def test_keeps_trusted_raw_img(self):
        result = sanitize('<img src="https://images.com/safe.jpg" alt="Safe">')
        assert "https://images.com/safe.jpg" in result

    def test_strips_event_handlers_on_kept_images(self):
        result = sanitize(
            '<img src="https://images.com/safe.jpg" onload="alert(\'xss\')" alt="x">'
        )
        assert "onload" not in result.lower()
        assert "https://images.com/safe.jpg" in result


class TestMixedMarkdownHtml:
    def test_markdown_image_plus_html_iframe(self):
        input_md = (
            "![ok](https://images.com/a.png)\n\n"
            '<iframe src="https://evil.com"></iframe>\n\n'
            "![bad](https://evil.com/t.png)"
        )
        result = sanitize(input_md)
        assert "https://images.com/a.png" in result
        assert "iframe" not in result.lower()
        assert "evil.com" not in result
