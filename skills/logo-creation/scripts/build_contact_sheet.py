#!/usr/bin/env python3
"""Build a self-contained HTML contact sheet for a logo system.

Inlines every SVG in the directory and renders the full variant gallery plus the
four perceptual tests from references/validation.md: the 16-pixel test, the
grayscale / black-and-white test, the blur test, and a 5-second recall timer.

Usage:
    python build_contact_sheet.py out/logo/ --name "Brand Name"
    python build_contact_sheet.py out/logo/ --name "Acme" --out sheet.html

No network dependencies; the output opens directly in a browser.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

# Order variants sensibly rather than alphabetically.
COMPONENT_ORDER = ["favicon", "icon", "wordmark", "horizontal", "stacked"]
VARIANT_ORDER = ["color", "black", "white", "darkmode"]


def sort_key(path: Path) -> tuple[int, int, str]:
    stem = path.stem.lower()
    comp, _, var = stem.partition("-")
    c = COMPONENT_ORDER.index(comp) if comp in COMPONENT_ORDER else len(COMPONENT_ORDER)
    v = VARIANT_ORDER.index(var) if var in VARIANT_ORDER else len(VARIANT_ORDER)
    return (c, v, stem)


def clean_svg(source: str, prefix: str) -> str:
    """Strip XML preamble, drop fixed dimensions, and namespace internal ids.

    The same file gets inlined many times on one page; without namespacing, any
    gradient or clipPath id would collide across instances.
    """
    svg = re.sub(r"<\?xml.*?\?>", "", source, flags=re.DOTALL)
    svg = re.sub(r"<!DOCTYPE.*?>", "", svg, flags=re.DOTALL)
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.DOTALL)
    svg = svg.strip()

    ids = set(re.findall(r'\bid="([^"]+)"', svg))
    for i in sorted(ids, key=len, reverse=True):
        new = f"{prefix}-{i}"
        svg = svg.replace(f'id="{i}"', f'id="{new}"')
        svg = svg.replace(f"url(#{i})", f"url(#{new})")
        svg = svg.replace(f'href="#{i}"', f'href="#{new}"')

    # Let CSS drive the box; the viewBox keeps the aspect ratio. Only the root
    # tag is touched - stripping width/height globally would gut any <rect>.
    m = re.match(r"<svg\b[^>]*>", svg)
    if m:
        root_tag = re.sub(r'\s(?:width|height)="[^"]*"', "", m.group())
        root_tag = root_tag.replace("<svg", '<svg class="mark"', 1)
        svg = root_tag + svg[m.end():]
    return svg


def tile(svg: str, cls: str = "", size: str = "") -> str:
    style = f' style="{size}"' if size else ""
    return f'<div class="tile {cls}"{style}>{svg}</div>'


def build(files: list[Path], brand: str) -> str:
    marks: list[tuple[str, str]] = []
    for n, f in enumerate(files):
        try:
            marks.append((f.stem, clean_svg(f.read_text(encoding="utf-8"), f"m{n}")))
        except (OSError, UnicodeDecodeError) as exc:
            print(f"warning: skipping {f.name}: {exc}", file=sys.stderr)

    if not marks:
        raise SystemExit("error: no readable SVG files")

    # The icon is the subject of the small-size tests; fall back to the first mark.
    icon = next(
        (s for name, s in marks if name.lower().startswith(("icon", "favicon"))),
        marks[0][1],
    )
    # Prefer a horizontal lock-up for the scale ramp.
    lockup = next(
        (s for name, s in marks if name.lower().startswith("horizontal")), icon
    )

    esc = html.escape(brand)

    gallery = "\n".join(
        f'<figure class="card">'
        f'<div class="pair">{tile(svg, "light")}{tile(svg, "dark")}</div>'
        f"<figcaption>{html.escape(name)}</figcaption>"
        f"</figure>"
        for name, svg in marks
    )

    favicons = "\n".join(
        f'<div class="px"><div class="pxbox" style="width:{s}px;height:{s}px">{icon}</div>'
        f"<span>{s}px</span></div>"
        for s in (16, 24, 32, 48, 64)
    )

    # Grayscale is worth seeing on both surfaces; the single-colour variants have
    # exactly one legitimate background each, so they get one tile.
    mono = "\n".join(
        '<figure class="card"><div class="pair">'
        + "".join(tile(icon, c) for c in tiles)
        + f"</div><figcaption>{label}</figcaption></figure>"
        for label, tiles in (
            ("grayscale", ("light fx-gray", "dark fx-gray")),
            ("pure black on white", ("light fx-black",)),
            ("pure white on dark", ("dark fx-white",)),
        )
    )

    blurs = "\n".join(
        f'<figure class="card"><div class="pair">{tile(icon, f"light fx-blur{n}")}</div>'
        f"<figcaption>blur {n}px</figcaption></figure>"
        for n in (1, 2, 4)
    )

    ramp = "\n".join(
        f'<div class="px"><div class="pxbox wide" style="width:{w}px">{lockup}</div>'
        f"<span>{label}</span></div>"
        for w, label in ((32, "favicon"), (120, "app bar"), (280, "web header"), (560, "signage"))
    )

    return TEMPLATE.format(
        brand=esc,
        gallery=gallery,
        favicons=favicons,
        mono=mono,
        blurs=blurs,
        ramp=ramp,
        recall=icon,
        count=len(marks),
    )


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{brand} - logo contact sheet</title>
<style>
  :root {{
    --bg: #f6f6f4; --fg: #16161a; --muted: #6b6b73;
    --line: #dededa; --card: #ffffff; --dark: #16161a;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#121214; --fg:#eeeef0; --muted:#96969e; --line:#2a2a2e; --card:#1a1a1e; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 48px 32px 96px;
    background: var(--bg); color: var(--fg);
    font: 15px/1.55 ui-sans-serif, -apple-system, "Segoe UI", Roboto, sans-serif;
  }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  header {{ border-bottom: 1px solid var(--line); padding-bottom: 24px; margin-bottom: 48px; }}
  h1 {{ font-size: 28px; font-weight: 600; letter-spacing: -0.02em; margin: 0 0 6px; }}
  .sub {{ color: var(--muted); font-size: 14px; }}
  h2 {{
    font-size: 12px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--muted); margin: 56px 0 6px;
  }}
  .hint {{ color: var(--muted); font-size: 13px; margin: 0 0 20px; max-width: 62ch; }}
  .grid {{ display: grid; gap: 18px;
           grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }}
  .card {{ margin: 0; border: 1px solid var(--line); border-radius: 10px;
           overflow: hidden; background: var(--card); }}
  .pair {{ display: flex; }}
  .tile {{
    flex: 1; display: grid; place-items: center;
    padding: 26px; min-height: 130px;
  }}
  .tile .mark {{ width: 100%; height: auto; max-height: 78px; }}
  .light {{ background: #ffffff; color: #16161a; }}
  .dark  {{ background: var(--dark); color: #ffffff; }}
  figcaption {{
    padding: 9px 12px; font-size: 12px; color: var(--muted);
    border-top: 1px solid var(--line); font-family: ui-monospace, "Cascadia Code", monospace;
  }}
  /* Filters go on the mark, never the tile - filtering the container would
     transform its background too, turning a "pure black" test into a black
     rectangle and bleeding blur past the tile edge. */
  .fx-gray  .mark {{ filter: grayscale(1); }}
  .fx-black .mark {{ filter: brightness(0); }}
  .fx-white .mark {{ filter: brightness(0) invert(1); }}
  .fx-blur1 .mark {{ filter: blur(1px); }}
  .fx-blur2 .mark {{ filter: blur(2px); }}
  .fx-blur4 .mark {{ filter: blur(4px); }}
  .strip {{ display: flex; align-items: flex-end; gap: 30px; flex-wrap: wrap;
           background: #fff; color:#16161a; border: 1px solid var(--line);
           border-radius: 10px; padding: 30px; }}
  .px {{ display: flex; flex-direction: column; align-items: center; gap: 10px; }}
  .px span {{ font-size: 11px; color: #8a8a92; font-family: ui-monospace, monospace; }}
  .pxbox {{ display: grid; place-items: center; }}
  .pxbox .mark {{ width: 100%; height: 100%; }}
  .pxbox.wide {{ height: auto; }}
  .pxbox.wide .mark {{ height: auto; }}
  .recall {{ border: 1px solid var(--line); border-radius: 10px;
             background: var(--card); padding: 30px; }}
  .stage {{ height: 190px; display: grid; place-items: center; background: #fff;
           border-radius: 8px; margin-bottom: 18px; }}
  .stage .mark {{ width: 150px; height: 150px; color: #16161a; }}
  .stage.hidden .mark {{ visibility: hidden; }}
  button {{
    font: inherit; font-size: 14px; padding: 9px 18px; border-radius: 7px;
    border: 1px solid var(--line); background: var(--fg); color: var(--bg); cursor: pointer;
  }}
  button:disabled {{ opacity: .5; cursor: default; }}
  #timer {{ margin-left: 14px; color: var(--muted); font-size: 13px;
           font-family: ui-monospace, monospace; }}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <h1>{brand}</h1>
    <div class="sub">Logo contact sheet - {count} variants, four validation tests</div>
  </header>

  <h2>Variant gallery</h2>
  <p class="hint">Every file on light and dark. Each variant must be a real file - a
     CSS filter standing in for a white version is not a deliverable.</p>
  <div class="grid">{gallery}</div>

  <h2>Test 1 - 16 pixels</h2>
  <p class="hint">Look for the four failure modes: counters filling in, thin elements
     vanishing, adjacent shapes merging, and silhouette drift - where it stays visible
     but reads as a different shape than the full-size mark.</p>
  <div class="strip">{favicons}</div>

  <h2>Test 2 - grayscale and single colour</h2>
  <p class="hint">If forms merge here, tonal contrast is doing structural work that
     shape should be doing. Fix the shape, not the colour.</p>
  <div class="grid">{mono}</div>

  <h2>Test 3 - blur</h2>
  <p class="hint">Blur leaves silhouette and mass distribution - roughly what
     peripheral vision and distance deliver. The overall form must stay identifiable;
     details are expected to go.</p>
  <div class="grid">{blurs}</div>

  <h2>Test 4 - 5-second recall</h2>
  <p class="hint">Watch for five seconds, then describe it from memory before looking
     again. It passes if the description captures the essential form, and fails if it
     is vague or needs detail you did not retain.</p>
  <div class="recall">
    <div class="stage hidden" id="stage">{recall}</div>
    <button id="go">Show for 5 seconds</button><span id="timer"></span>
  </div>

  <h2>Scale ramp</h2>
  <p class="hint">The same lock-up from favicon to signage. Weight and spacing should
     feel constant across the range.</p>
  <div class="strip">{ramp}</div>

</div>
<script>
  (function () {{
    var stage = document.getElementById('stage');
    var go = document.getElementById('go');
    var timer = document.getElementById('timer');
    go.addEventListener('click', function () {{
      var left = 5;
      stage.classList.remove('hidden');
      go.disabled = true;
      timer.textContent = left + 's';
      var id = setInterval(function () {{
        left -= 1;
        timer.textContent = left > 0 ? left + 's' : 'now describe it from memory';
        if (left <= 0) {{
          clearInterval(id);
          stage.classList.add('hidden');
          go.disabled = false;
        }}
      }}, 1000);
    }});
  }})();
</script>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a logo contact sheet.")
    ap.add_argument("directory", type=Path, help="directory containing the logo SVGs")
    ap.add_argument("--name", default="Untitled", help="brand name for the header")
    ap.add_argument("--out", type=Path, default=None, help="output HTML path")
    args = ap.parse_args()

    if not args.directory.is_dir():
        print(f"error: {args.directory} is not a directory", file=sys.stderr)
        return 2

    files = sorted(args.directory.glob("*.svg"), key=sort_key)
    if not files:
        print(f"error: no .svg files in {args.directory}", file=sys.stderr)
        return 2

    out = args.out or args.directory / "contact-sheet.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(files, args.name), encoding="utf-8")

    print(f"{out}  ({len(files)} variants)")
    print("Open it and run the four tests by eye - the sheet only makes failures visible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
