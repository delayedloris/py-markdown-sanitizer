# AGENTS.md

## Cursor Cloud specific instructions

`py-markdown-sanitizer` is a single Python library (no runnable services). Tooling is [uv](https://docs.astral.sh/uv/).

- `uv` is installed to `~/.local/bin` and put on PATH via `~/.bashrc` (`. "$HOME/.local/bin/env"`); it's available in fresh login shells.
- Standard commands are in `README.md`: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`.
- Bypass suite (`tests/vercel/test_bypass_attempts.py`) is expected green; image allow-list matching is host/path based (not raw `startswith`).
