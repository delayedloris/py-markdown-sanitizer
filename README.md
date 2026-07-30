# py-markdown-sanitizer

Markdown sanitizer for two things:

1. **No zero-click exfiltration** — drops disallowed images and auto-loading HTML
2. **Configurable image URL allow-list**

Pipeline: **markdown → HTML (mistune) → sanitize (BeautifulSoup) → markdown (markdownify)**.

Links are left alone (they need a click). Inspired by [Vercel’s approach](https://github.com/vercel-labs/markdown-sanitizers), scoped to images only.

## Usage

```python
from py_markdown_sanitizer import sanitize_markdown

print(
    sanitize_markdown(
        "ok ![a](https://cdn.example.com/a.png) bad ![b](https://evil.com/t.png)",
        allowed_image_prefixes=["https://cdn.example.com/"],
    )
)
```

Empty allow-list ⇒ all images removed (fail closed).

## Develop

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format .
```

## License

MIT

