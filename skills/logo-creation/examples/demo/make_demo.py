#!/usr/bin/env python3
"""Generate the bundled demo variant set.

A fictional brand ("Halyard") used only so the scripts are runnable straight
after cloning. These are TOOLING FIXTURES, not a design sample - plain geometric
placeholders that exercise the naming convention, the stroke floor and the
lock-up maths.

The icon is an H monogram. An earlier version used an open ring with a vertical
bar and read unmistakably as a power button - the exact known-symbol collision
references/design-execution.md warns about. Worth leaving on the record.

Regenerate with:  python examples/demo/make_demo.py
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent

INK = "#1B2A33"
ACCENT = "#C2673B"
INK_DARK = "#EAF0F3"
ACCENT_DARK = "#DE8B5C"

SW = 7.0


def f(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def stroke(d: str, color: str, w: float, cap: str = "round") -> str:
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{f(w)}" '
            f'stroke-linecap="{cap}" stroke-linejoin="round"/>')


def icon_body(c: str) -> str:
    """An H monogram: two stems and a crossbar. Deliberately boring - a fixture
    should not compete for attention with the tool it is demonstrating."""
    return (
        stroke("M16 14 L16 50", c, SW)
        + stroke("M48 14 L48 50", c, SW)
        + stroke("M16 32 L48 32", c, SW)
    )


def icon(c: str) -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" '
            'aria-label="Halyard"><title>Halyard</title>'
            f'{icon_body(c)}</svg>')


# Wordmark: three geometric strokes standing in for a drawn logotype. Enough to
# exercise the lock-up maths and the 120px stroke floor.
WM_W, WM_H = 240.0, 64.0
WWS = 8.0


def wordmark_body(c: str, dot: str) -> str:
    bars = "".join(
        stroke(f"M{f(x)} 20 L{f(x)} 44", c, WWS)
        for x in (20.0, 52.0, 84.0, 116.0, 148.0, 180.0)
    )
    return bars + f'<circle cx="{f(212.0)}" cy="32" r="{f(WWS / 2)}" fill="{dot}"/>'


def wordmark(c: str, dot: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(WM_W)} {f(WM_H)}" '
            'role="img" aria-label="Halyard"><title>Halyard</title>'
            f'{wordmark_body(c, dot)}</svg>')


def horizontal(ic: str, wc: str, dot: str) -> str:
    gap, wm_h = 32.0, 44.0
    s = wm_h / WM_H
    wx = 64.0 + gap
    total = wx + WM_W * s
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(total)} 64" '
            'role="img" aria-label="Halyard"><title>Halyard</title>'
            f'{icon_body(ic)}'
            f'<g transform="translate({f(wx)} {f((64 - wm_h) / 2)}) scale({s:.4f})">'
            f'{wordmark_body(wc, dot)}</g></svg>')


def stacked(ic: str, wc: str, dot: str) -> str:
    wm_w, gap = 160.0, 25.6
    s = wm_w / WM_W
    total_h = 64.0 + gap + WM_H * s
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(wm_w)} {f(total_h)}" '
            'role="img" aria-label="Halyard"><title>Halyard</title>'
            f'<g transform="translate({f((wm_w - 64) / 2)} 0)">{icon_body(ic)}</g>'
            f'<g transform="translate(0 {f(64 + gap)}) scale({s:.4f})">'
            f'{wordmark_body(wc, dot)}</g></svg>')


# The packager treats a usage document as a required deliverable, so the fixture
# set needs one for `package_brand.py examples/demo` to build without --force.
BRAND_MD = f"""# Halyard — fixture brand

Placeholder usage guide for the bundled demo set. Not a real identity.

| Role | Light | Dark |
| :-- | :-- | :-- |
| Ink | `{INK}` | `{INK_DARK}` |
| Accent | `{ACCENT}` | `{ACCENT_DARK}` |

- **Clear space** — `0.5x` of symbol height on all sides.
- **Minimum size** — icon 16 px, horizontal lock-up 120 px wide.
- **Misuse** — do not stretch, rotate, recolour, or add effects.
"""


FILES = {
    "BRAND.md": lambda: BRAND_MD,
    "icon-color.svg": lambda: icon(INK),
    "icon-black.svg": lambda: icon("#000000"),
    "icon-white.svg": lambda: icon("#ffffff"),
    "icon-darkmode.svg": lambda: icon(INK_DARK),
    "favicon.svg": lambda: icon(INK),
    "wordmark-color.svg": lambda: wordmark(INK, ACCENT),
    "wordmark-black.svg": lambda: wordmark("#000000", "#000000"),
    "wordmark-white.svg": lambda: wordmark("#ffffff", "#ffffff"),
    "horizontal-color.svg": lambda: horizontal(INK, INK, ACCENT),
    "horizontal-black.svg": lambda: horizontal("#000000", "#000000", "#000000"),
    "horizontal-white.svg": lambda: horizontal("#ffffff", "#ffffff", "#ffffff"),
    "horizontal-darkmode.svg": lambda: horizontal(INK_DARK, INK_DARK, ACCENT_DARK),
    "stacked-color.svg": lambda: stacked(INK, INK, ACCENT),
    "stacked-black.svg": lambda: stacked("#000000", "#000000", "#000000"),
    "stacked-white.svg": lambda: stacked("#ffffff", "#ffffff", "#ffffff"),
}


def main() -> None:
    for name, fn in FILES.items():
        (OUT / name).write_text(fn(), encoding="utf-8")
    print(f"wrote {len(FILES)} demo files to {OUT}")


if __name__ == "__main__":
    main()
