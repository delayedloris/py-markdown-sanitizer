"""Port of Vercel html-sanitization.test.ts — adapted expectations."""

from tests.vercel.helpers import sanitize


class TestSafeHtmlTags:
    def test_converts_strong_em_to_markdown(self):
        result = sanitize("Text with <strong>bold</strong> and <em>italic</em>")
        assert "bold" in result and "italic" in result
        assert "<strong>" not in result and "<em>" not in result

    def test_converts_code_tags(self):
        result = sanitize("Here is <code>inline code</code>")
        assert "`inline code`" in result or "inline code" in result

    def test_converts_trusted_html_images(self):
        result = sanitize('<img src="https://images.com/safe.jpg" alt="Safe image">')
        assert "https://images.com/safe.jpg" in result

    def test_sanitizes_untrusted_html_images(self):
        result = sanitize('<img src="https://evil.com/tracker.gif" alt="Tracker">')
        assert "![" not in result
        assert "[Tracker](https://evil.com/tracker.gif)" in result


class TestDangerousHtmlTags:
    def test_removes_script_completely(self):
        result = sanitize('Safe text <script>alert("xss")</script> more text')
        assert "script" not in result.lower()
        assert "Safe text" in result and "more text" in result

    def test_removes_iframe(self):
        assert sanitize('<iframe src="https://evil.com/embed"></iframe>') == ""

    def test_removes_object_embed(self):
        result = sanitize('<object data="malware.swf"></object><embed src="evil.exe">')
        assert result.strip() == ""

    def test_removes_video_audio_source(self):
        result = sanitize(
            '<video src="https://evil.com/v.mp4"></video>'
            '<audio src="https://evil.com/a.mp3"></audio>'
        )
        assert "evil.com" not in result
        assert "video" not in result.lower()
        assert "audio" not in result.lower()


class TestXssPrevention:
    def test_removes_javascript_in_images(self):
        result = sanitize('<img src="javascript:alert(\'xss\')" alt="Evil">')
        assert "javascript:" not in result.lower()

    def test_removes_data_urls_in_images(self):
        result = sanitize(
            '<img src="data:text/html,<script>alert(\'xss\')</script>" alt="x">'
        )
        assert "data:" not in result

    def test_removes_onload_handlers(self):
        result = sanitize(
            '<img src="https://images.com/safe.jpg" onload="alert(\'xss\')" alt="e">'
        )
        assert "onload" not in result.lower()
        assert "https://images.com/safe.jpg" in result
