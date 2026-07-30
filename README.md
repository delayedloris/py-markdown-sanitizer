# py-markdown-sanitizer

Tiny markdown sanitizer for two things:

1. **No zero-click exfiltration** — drops disallowed images and strips auto-loading HTML (`img`, `iframe`, `script`, …)
2. **Configurable image URL allow-list** — only matching `src` / `![]()` URLs are kept

Links are left alone (they need a click). Inspired by [Vercel’s markdown-to-markdown-sanitizer](https://github.com/vercel-labs/markdown-sanitizers), not a full port.

## Usage

```python
from py_markdown_sanitizer import sanitize_markdown

print(sanitize_markdown(
    "ok ![a](https://cdn.example.com/a.png) bad ![b](https://evil.com/t.png)",
    allowed_image_prefixes=["https://cdn.example.com/"],
))
# ok ![a](https://cdn.example.com/a.png) bad b
```

Empty allow-list ⇒ all images removed (fail closed).

## License

MIT
