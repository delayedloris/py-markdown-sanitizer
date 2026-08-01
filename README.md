# py-markdown-sanitizer

Markdown sanitizer for two things:

1. **No zero-click exfiltration** — disallowed images become links; auto-loading HTML is dropped
2. **Configurable image URL allow-list**

Pipeline: **markdown → HTML (mistune) → sanitize (BeautifulSoup) → markdown (markdownify)**.

Links are left alone (they need a click). Disallowed http(s) images are downgraded to links with the same URL. Inspired by [Vercel’s approach](https://github.com/vercel-labs/markdown-sanitizers), scoped to images only.

## Usage

```python
from py_markdown_sanitizer import sanitize_markdown

print(
    sanitize_markdown(
        "ok ![a](https://cdn.example.com/a.png) bad ![b](https://evil.com/t.png)",
        allowed_image_prefixes=["https://cdn.example.com/"],
    )
)
# → ok ![a](https://cdn.example.com/a.png) bad [b](https://evil.com/t.png)
```

Empty allow-list ⇒ all images become links (or alt text if the URL isn’t http(s)).

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

