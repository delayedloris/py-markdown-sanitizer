# py-markdown-sanitizer

Python port of [Vercel’s markdown-to-markdown-sanitizer](https://github.com/vercel-labs/markdown-sanitizers/tree/main/markdown-to-markdown-sanitizer).

Sanitizes markdown → markdown for cases where a third party (GitHub, GitLab, etc.) renders it. Focused on blocking unexpected link/image URLs after prompt-injection.

**Not a security guarantee.** Less safe than sanitizing final HTML. Use only when you don’t control the renderer.

## Install

```bash
pip install -e .
```

## Usage

```python
from py_markdown_sanitizer import SanitizeOptions, sanitize_markdown

options = SanitizeOptions(
    default_origin="https://example.com",
    allowed_link_prefixes=["https://example.com", "https://trusted-site.org"],
    allowed_image_prefixes=["https://example.com/images"],
)

print(sanitize_markdown(
    "[ok](https://example.com/x) [bad](https://evil.com)",
    options,
))
# [ok](https://example.com/x) [bad](#)
```

## Options

| Field | Notes |
| --- | --- |
| `default_origin` | Required. Base for relative URLs |
| `allowed_link_prefixes` | Prefix allow-list for `href` |
| `allowed_image_prefixes` | Prefix allow-list for `src` |
| `default_link_origin` / `default_image_origin` | Override base per type |
| `url_max_length` | Default `200`; `0` = no limit |
| `max_markdown_length` | Default `100000`; `0` = no limit |
| `sanitize_for_commonmark` | Backslash escapes instead of HTML entities |

## Pipeline

Same shape as upstream:

1. Markdown → HTML (`mistune`)
2. HTML sanitize (`bleach` + URL allow-list)
3. HTML → Markdown (`markdownify`) with aggressive entity escaping

## License

MIT (upstream © Vercel Inc.)
