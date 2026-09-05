#!/usr/bin/env python3
"""Detect collisions between a candidate logo and well-known existing symbols.

A mark that reads as a loading spinner, a hamburger menu or a dice face before it
reads as the brand is unusable, however clean its geometry is. This measures the
geometric signatures that cause those readings, so a colliding route fails on
evidence instead of on somebody noticing.

Usage:
    python3 detect_symbol_collision.py out/logo/icon-color.svg
    python3 detect_symbol_collision.py out/logo/            # every SVG in a dir

Exit 0 if nothing collides, 1 if anything does.

WHAT THIS CANNOT DO — read before trusting a pass.

Only collisions with a *geometric* signature are detectable here: radial
symmetry, regular parallel bars, and lattices. Semantic and anatomical readings
are invisible to it. A real route passed every check in this file and was still
unshippable: its strongest reading was anatomical, and its second-strongest
resolved an accent bar as an "I" so the intended "H" never landed. No pixel
statistic catches that.

A pass means "worth a human look", never "approved". Always render the mark and
get an independent description of what it actually reads as.

Needs one SVG renderer on PATH (rsvg-convert, resvg, or inkscape) and, for the
BMP hop, `sips` on macOS. On Linux install librsvg2-bin and ImageMagick.
"""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

INK = 128           # luma below this counts as ink
RENDER_PX = 256     # analysis resolution

# Calibrated against real rejected routes AND against a known-good mark, so the
# thresholds discriminate rather than rejecting everything. Loosen only with a
# counter-example that proves the current value wrong.
ROTATION_LIMIT = 0.95   # 90-degree self-similarity: spinner / compass / wheel
BAND_LIMIT = 3          # regular parallel bars: hamburger menu / barcode
LATTICE_LIMIT = 4       # similar blobs on a grid: dice face / QR / keypad
MIN_INK_TO_JUDGE = 0.01  # below this the frame is effectively empty


def _render(svg: Path, width: int, out: Path) -> None:
    if shutil.which("rsvg-convert"):
        cmd = ["rsvg-convert", "-w", str(width), "-b", "white",
               str(svg), "-o", str(out)]
    elif shutil.which("resvg"):
        cmd = ["resvg", str(svg), str(out), "--width", str(width),
               "--background", "white"]
    elif shutil.which("inkscape"):
        cmd = ["inkscape", str(svg), "--export-type=png",
               f"--export-filename={out}", f"--export-width={width}",
               "--export-background=white"]
    else:
        sys.exit("no SVG renderer found: install librsvg2-bin, resvg, or inkscape")
    subprocess.run(cmd, check=True, capture_output=True)


def _luma(png: Path) -> list[list[int]]:
    """Rows of 0-255 luma. Goes via BMP so no imaging dependency is needed."""
    bmp = png.with_suffix(".bmp")
    if shutil.which("sips"):
        subprocess.run(["sips", "-s", "format", "bmp", str(png), "--out", str(bmp)],
                       check=True, capture_output=True)
    elif shutil.which("magick"):
        subprocess.run(["magick", str(png), "BMP3:" + str(bmp)],
                       check=True, capture_output=True)
    else:
        sys.exit("need `sips` (macOS) or `magick` (ImageMagick) to read pixels")

    data = bmp.read_bytes()
    offset = struct.unpack_from("<I", data, 10)[0]
    width = struct.unpack_from("<i", data, 18)[0]
    raw_h = struct.unpack_from("<i", data, 22)[0]
    depth = struct.unpack_from("<H", data, 28)[0]
    height, bottom_up = abs(raw_h), raw_h > 0
    stride = ((width * depth // 8) + 3) // 4 * 4
    step = depth // 8

    rows = []
    for y in range(height):
        src = offset + (height - 1 - y if bottom_up else y) * stride
        row = []
        for x in range(width):
            p = src + x * step
            b, g, r = data[p], data[p + 1], data[p + 2]
            row.append((r * 299 + g * 587 + b * 114) // 1000)
        rows.append(row)
    return rows


def _binary(rows: list[list[int]]) -> list[list[int]]:
    return [[1 if v < INK else 0 for v in row] for row in rows]


def _similarity(a: list[list[int]], b: list[list[int]]) -> float:
    cells = sum(len(r) for r in a)
    if not cells:
        return 0.0
    same = sum(1 for ra, rb in zip(a, b, strict=True)
               for va, vb in zip(ra, rb, strict=True) if va == vb)
    return same / cells


def _rotate90(grid: list[list[int]]) -> list[list[int]]:
    return [list(col) for col in zip(*grid[::-1], strict=True)]


def rotational_symmetry(rows: list[list[int]]) -> float:
    """Self-similarity under a 90-degree turn.

    High four-fold symmetry is what makes a mark read as a spinner, compass rose,
    ship's wheel or sunburst: a hub with identical arms in every direction.
    """
    grid = _binary(rows)
    size = min(len(grid), len(grid[0]))
    grid = [row[:size] for row in grid[:size]]
    return _similarity(grid, _rotate90(grid))


def horizontal_bands(rows: list[list[int]]) -> tuple[int, bool]:
    """Count horizontal ink bands, and whether they are regular parallel bars."""
    width = len(rows[0])
    inked = [y for y, row in enumerate(rows)
             if sum(v < INK for v in row) >= width * 0.25]
    if not inked:
        return 0, False

    bands: list[list[int]] = [[inked[0]]]
    for y in inked[1:]:
        if y - bands[-1][-1] <= 1:
            bands[-1].append(y)
        else:
            bands.append([y])

    if len(bands) < 3:
        return len(bands), False

    thick = [len(b) for b in bands]
    gaps = [bands[i + 1][0] - bands[i][-1] for i in range(len(bands) - 1)]
    regular = (max(thick) - min(thick) <= max(2, min(thick))
               and max(gaps) - min(gaps) <= max(2, min(gaps)))
    return len(bands), regular


def lattice_blobs(rows: list[list[int]]) -> int:
    """Count similar ink blobs arranged on a regular 2D lattice."""
    grid = _binary(rows)
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    blobs: list[tuple[float, float, int]] = []

    for y in range(h):
        for x in range(w):
            if not grid[y][x] or seen[y][x]:
                continue
            stack, cells = [(y, x)], []
            seen[y][x] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            if len(cells) >= 4:
                ys = [c[0] for c in cells]
                xs = [c[1] for c in cells]
                blobs.append((sum(ys) / len(ys), sum(xs) / len(xs), len(cells)))

    if len(blobs) < 4:
        return 0
    sizes = [b[2] for b in blobs]
    similar = max(sizes) <= min(sizes) * 2.5
    rows_used = len({round(b[0] / max(1, h * 0.12)) for b in blobs})
    cols_used = len({round(b[1] / max(1, w * 0.12)) for b in blobs})
    return len(blobs) if (similar and rows_used >= 2 and cols_used >= 2) else 0


def collisions(svg: Path) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "render.png"
        _render(svg, RENDER_PX, png)
        rows = _luma(png)

    # A near-empty frame is trivially symmetric in every direction, so the
    # detectors would report a spinner for it. This is the normal case for a
    # white-on-white variant rendered against a white background, and for any
    # mark whose colour matches the render background. Nothing to judge.
    total = sum(len(r) for r in rows)
    inked = sum(1 for r in rows for v in r if v < INK)
    if total == 0 or inked / total < MIN_INK_TO_JUDGE:
        return []

    found = []
    symmetry = rotational_symmetry(rows)
    if symmetry >= ROTATION_LIMIT:
        found.append(f"four-fold rotational symmetry {symmetry:.1%} "
                     f"(limit {ROTATION_LIMIT:.0%}) - reads as a spinner / "
                     f"compass rose / ship's wheel / sunburst")

    bands, regular = horizontal_bands(rows)
    if regular and bands >= BAND_LIMIT:
        found.append(f"{bands} regular parallel bars - reads as a hamburger "
                     f"menu / barcode / signal bars")

    blobs = lattice_blobs(rows)
    if blobs >= LATTICE_LIMIT:
        found.append(f"{blobs} similar blobs on a lattice - reads as a dice "
                     f"face / QR code / keypad")
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2

    target = Path(argv[1])
    files = sorted(target.glob("*.svg")) if target.is_dir() else [target]
    if not files:
        print(f"no SVG files at {target}")
        return 2

    clean = True
    for svg in files:
        found = collisions(svg)
        if found:
            clean = False
            print(f"{svg.name}: COLLIDES")
            for f in found:
                print(f"    - {f}")
        else:
            print(f"{svg.name}: no geometric collision "
                  f"(still needs a human read)")

    if not clean:
        print("\nRedesign rather than tuning thresholds. Two arrangements cause "
              "most collisions when a brief supplies a count:\n"
              "  - radial around a centre point\n"
              "  - parallel equal bars\n"
              "An asymmetric or nested arrangement is far safer.")
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
