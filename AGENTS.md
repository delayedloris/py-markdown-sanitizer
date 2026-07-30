# AGENTS.md

## Cursor Cloud specific instructions

`py-markdown-sanitizer` is a single Python library (no runnable services). Tooling is [uv](https://docs.astral.sh/uv/).

- `uv` is installed to `~/.local/bin` and put on PATH via `~/.bashrc` (`. "$HOME/.local/bin/env"`); it's available in fresh login shells.
- Standard commands are in `README.md`: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`.
- Known state: `tests/vercel/test_bypass_attempts.py` has ~14 pre-existing failures (unpatched image-exfiltration bypasses). These are not environment problems; the rest of the suite passes.
