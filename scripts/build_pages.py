#!/usr/bin/env python3
"""Generate docs/index.html for GitHub Pages spot-checks.

Run: uv run python scripts/build_pages.py
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from py_markdown_sanitizer import sanitize_markdown

ROOT = Path(__file__).resolve().parents[1]
BYPASS_DIR = ROOT / "tests" / "fixtures" / "bypass-attempts"
OUT = ROOT / "docs" / "index.html"

DEFAULT_PREFIXES = [
    "https://example.com",
    "https://images.com",
    "https://prefix.com/prefix/",
]
DEFAULT_ORIGIN = "https://example.com"


@dataclass(frozen=True)
class Example:
    title: str
    markdown: str
    prefixes: tuple[str, ...] = tuple(DEFAULT_PREFIXES)
    origin: str = DEFAULT_ORIGIN
    note: str = ""


CURATED: list[Example] = [
    Example(
        "Trusted image kept",
        "![photo](https://images.com/photo.jpg)",
        note="Allow-listed host stays an image.",
    ),
    Example(
        "Untrusted image → link",
        "![tracker](https://evil.com/tracker.gif)",
        note="Disallowed http(s) image becomes a clickable link.",
    ),
    Example(
        "Mixed content",
        """# Title

A [link](https://example.com/page) and ![ok](https://images.com/pic.jpg).

Also [evil link](https://evil.com) and ![bad](https://evil.com/t.gif).""",
        note="Links pass through; only images are filtered.",
    ),
    Example(
        "Relative image resolved",
        "![local](/images/local.png)",
        note="Relative URLs resolve against default_origin.",
    ),
    Example(
        "Data URI blocked",
        "![x](data:image/gif;base64,R0lGOD)",
        note="Non-http(s) schemes are not kept as images.",
    ),
    Example(
        "Empty allow-list",
        "![a](https://images.com/a.png) ![b](https://evil.com/b.png)",
        prefixes=(),
        note="Empty allow-list ⇒ every image becomes a link.",
    ),
    Example(
        "Prefix path required",
        "![ok](https://prefix.com/prefix/a.png) ![no](https://prefix.com/other/a.png)",
        note="Host allow-list can require a path prefix.",
    ),
    Example(
        "Prefix confusion attempt",
        "![x](https://example.com.evil.com/t.png)",
        note="Lookalike host must not match the allow-list.",
    ),
]


def _run(ex: Example) -> tuple[str, str, bool]:
    out = sanitize_markdown(
        ex.markdown,
        allowed_image_prefixes=list(ex.prefixes),
        default_origin=ex.origin,
    )
    return ex.markdown, out, ex.markdown.strip() != out.strip()


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _card(
    *,
    title: str,
    inp: str,
    out: str,
    changed: bool,
    note: str = "",
    open_: bool = True,
    prefixes: tuple[str, ...] | None = None,
) -> str:
    badge = "changed" if changed else "unchanged"
    badge_cls = "badge-changed" if changed else "badge-same"
    has_img = "![" in out
    img_badge = (
        '<span class="badge badge-img">output has image</span>' if has_img else ""
    )
    note_html = f'<p class="note">{_esc(note)}</p>' if note else ""
    pref = ""
    if prefixes is not None:
        pref_txt = ", ".join(prefixes) if prefixes else "(empty)"
        pref = f'<p class="meta">allow-list: <code>{_esc(pref_txt)}</code></p>'
    body = f"""
{note_html}
{pref}
<div class="cols">
  <div>
    <h4>input</h4>
    <pre><code>{_esc(inp)}</code></pre>
  </div>
  <div>
    <h4>output</h4>
    <pre><code>{_esc(out)}</code></pre>
  </div>
</div>
"""
    if open_:
        return f"""
<article class="card">
  <h3>{_esc(title)} <span class="badge {badge_cls}">{badge}</span> {img_badge}</h3>
  {body}
</article>
"""
    return f"""
<details class="card">
  <summary>{_esc(title)}
    <span class="badge {badge_cls}">{badge}</span> {img_badge}</summary>
  {body}
</details>
"""


def build() -> str:
    curated_html: list[str] = []
    for ex in CURATED:
        inp, out, changed = _run(ex)
        curated_html.append(
            _card(
                title=ex.title,
                inp=inp,
                out=out,
                changed=changed,
                note=ex.note,
                open_=True,
                prefixes=ex.prefixes,
            )
        )

    bypass_html: list[str] = []
    changed_n = 0
    files = sorted(BYPASS_DIR.glob("*.md"))
    for path in files:
        md = path.read_text(encoding="utf-8")
        out = sanitize_markdown(
            md,
            allowed_image_prefixes=list(DEFAULT_PREFIXES),
            default_origin=DEFAULT_ORIGIN,
        )
        changed = md.strip() != out.strip()
        if changed:
            changed_n += 1
        bypass_html.append(
            _card(
                title=path.name,
                inp=md,
                out=out,
                changed=changed,
                open_=False,
            )
        )

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>py-markdown-sanitizer examples</title>
<style>
  :root {{
    --bg: #f7f5f0;
    --ink: #1a1a1a;
    --muted: #5c5c5c;
    --line: #d9d4c8;
    --card: #fffef9;
    --changed: #8a2f1a;
    --same: #3d5a3d;
    --code: #f0ebe1;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font: 15px/1.45 ui-sans-serif, system-ui, sans-serif;
    color: var(--ink);
    background:
      radial-gradient(ellipse at top left, #ebe4d4 0%, transparent 55%),
      var(--bg);
  }}
  main {{ max-width: 980px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }}
  h1 {{
    font: 700 1.75rem/1.2 Georgia, "Times New Roman", serif;
    margin: 0 0 .35rem;
  }}
  h2 {{
    font: 650 1.2rem/1.3 Georgia, "Times New Roman", serif;
    margin: 2.25rem 0 .75rem;
  }}
  h3, summary {{ font: 600 1rem/1.35 ui-sans-serif, system-ui, sans-serif; }}
  h4 {{
    margin: 0 0 .35rem;
    font-size: .75rem;
    text-transform: uppercase;
    letter-spacing: .04em;
    color: var(--muted);
  }}
  .lede {{ color: var(--muted); max-width: 42rem; }}
  .meta, .note {{ color: var(--muted); font-size: .9rem; margin: .4rem 0 .75rem; }}
  code {{ font-family: ui-monospace, "Cascadia Code", monospace; font-size: .86em; }}
  pre {{
    margin: 0;
    padding: .75rem .85rem;
    background: var(--code);
    border: 1px solid var(--line);
    overflow: auto;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: ui-monospace, "Cascadia Code", monospace;
    font-size: .82rem;
    line-height: 1.4;
  }}
  .card {{
    background: var(--card);
    border: 1px solid var(--line);
    padding: 1rem 1.1rem;
    margin: 0 0 .85rem;
  }}
  details.card > summary {{ cursor: pointer; list-style: none; }}
  details.card > summary::-webkit-details-marker {{ display: none; }}
  details.card[open] > summary {{ margin-bottom: .65rem; }}
  .cols {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: .75rem;
  }}
  @media (max-width: 720px) {{ .cols {{ grid-template-columns: 1fr; }} }}
  .badge {{
    display: inline-block;
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .03em;
    text-transform: uppercase;
    padding: .1rem .4rem;
    border: 1px solid currentColor;
    vertical-align: middle;
  }}
  .badge-changed {{ color: var(--changed); }}
  .badge-same {{ color: var(--same); }}
  .badge-img {{ color: #1a4a6e; margin-left: .25rem; }}
  .toolbar {{
    display: flex; flex-wrap: wrap; gap: .5rem; align-items: center;
    margin: .75rem 0 1rem;
  }}
  .toolbar input {{
    flex: 1 1 12rem;
    padding: .45rem .6rem;
    border: 1px solid var(--line);
    background: #fff;
    font: inherit;
  }}
  .stat {{ color: var(--muted); font-size: .9rem; }}
  footer {{ margin-top: 2.5rem; color: var(--muted); font-size: .85rem; }}
  a {{ color: inherit; }}
</style>
</head>
<body>
<main>
  <h1>py-markdown-sanitizer</h1>
  <p class="lede">
    Spot-check page: input markdown vs sanitizer output.
    Generated by <code>scripts/build_pages.py</code> — do not hand-edit.
  </p>
  <p class="meta">
    Default allow-list for bypass fixtures:
    <code>{_esc(", ".join(DEFAULT_PREFIXES))}</code>
    · origin <code>{_esc(DEFAULT_ORIGIN)}</code>
  </p>

  <h2>Examples</h2>
  {"".join(curated_html)}

  <h2>Bypass fixtures</h2>
  <p class="lede">
    All files under <code>tests/fixtures/bypass-attempts/</code>, run through the
    same allow-list as the bypass suite.
  </p>
  <div class="toolbar">
    <input id="q" type="search" placeholder="Filter by filename…" autocomplete="off">
    <span class="stat" id="stat">{len(files)} files · {changed_n} changed</span>
  </div>
  <div id="bypass">
  {"".join(bypass_html)}
  </div>

  <footer>
    Generated {_esc(generated)}.
    <a href="https://github.com/delayedloris/py-markdown-sanitizer">Source</a>
  </footer>
</main>
<script>
const q = document.getElementById("q");
const items = [...document.querySelectorAll("#bypass details")];
const stat = document.getElementById("stat");
q.addEventListener("input", () => {{
  const needle = q.value.trim().toLowerCase();
  let shown = 0;
  for (const el of items) {{
    const text = el.querySelector("summary").textContent.toLowerCase();
    const ok = !needle || text.includes(needle);
    el.hidden = !ok;
    if (ok) shown++;
  }}
  stat.textContent = shown + " shown / " + items.length + " files";
}});
</script>
</body>
</html>
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
