"""Port of Vercel code-blocks.test.ts — dangerous markup in code must survive."""

from py_markdown_sanitizer import MarkdownSanitizer, SanitizeOptions

sanitizer = MarkdownSanitizer(
    SanitizeOptions(
        allowed_image_prefixes=["https://example.com/images"],
        default_origin="https://example.com",
    )
)


class TestInlineCode:
    def test_inline_code_with_html_preserved(self):
        result = sanitizer.sanitize(
            'Use `<script>alert("test")</script>` in your code.'
        )
        assert "`" in result
        assert "script" in result.lower()
        assert "alert" in result

    def test_inline_code_with_markdown_image_syntax(self):
        result = sanitizer.sanitize(
            "The syntax is `![image](url)` for images and `[link](url)` for links."
        )
        assert "`![image](url)`" in result or "![image](url)" in result

    def test_inline_code_with_dangerous_protocols(self):
        result = sanitizer.sanitize(
            'Example: `<img src="javascript:alert()">` is dangerous.'
        )
        assert "javascript:alert()" in result


class TestFencedCodeBlocks:
    def test_fenced_html_not_executed_as_html(self):
        input_md = """Code example:

```html
<script>
  alert("This should not execute");
</script>
<img src="javascript:alert('xss')" onerror="alert('xss')">
```

End of example."""
        result = sanitizer.sanitize(input_md)
        assert "```" in result
        assert 'alert("This should not execute")' in result
        assert "javascript:alert('xss')" in result

    def test_fenced_markdown_examples_preserved(self):
        input_md = """Markdown examples:

```markdown
# Header
![Dangerous image](javascript:alert('xss'))
[Dangerous link](javascript:alert('xss'))
```

These are just examples."""
        result = sanitizer.sanitize(input_md)
        assert "![Dangerous image](javascript:alert('xss'))" in result
        assert "[Dangerous link](javascript:alert('xss'))" in result

    def test_outside_code_images_still_filtered(self):
        input_md = (
            "![bad](https://evil.com/t.png)\n\n"
            "```\n![still code](https://evil.com/t.png)\n```\n"
        )
        result = sanitizer.sanitize(input_md)
        # first image blocked
        assert result.count("evil.com") == 1
        assert "![still code](https://evil.com/t.png)" in result
