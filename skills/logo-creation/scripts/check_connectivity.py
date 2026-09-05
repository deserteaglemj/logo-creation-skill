#!/usr/bin/env python3
"""Measure whether a mark's ink forms one connected shape or several.

Two reviews of the same candidate disagreed by render size: at 16px a stepped
crossbar read as "one continuous stepping form", at 300px as "separate,
disconnected pieces". Opinion cannot settle that; connectivity can be counted.

Use it to answer "do these parts actually touch" rather than debating it. Note
what it does NOT tell you: a mark can be several disconnected components and
still read as one letter. A known-good reference mark measured 3 components at
every size while reviewing well, so treat a mismatch as information about the
geometry, not an automatic defect.

Reports the number of 4-connected ink components at a given size, and the size
of each. For a letterform mark built as stems plus a crossbar, the intended
answer is 1: everything touching. More than one means the parts only appear to
join, which is what makes a viewer see fragments.

Usage:
    python3 check_connectivity.py out/logo/icon-color.svg
    python3 check_connectivity.py out/logo/icon-color.svg --sizes 16 64 300
"""

from __future__ import annotations

import argparse
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

INK = 128


def render(svg: Path, width: int, out: Path) -> None:
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-b", "white", str(svg), "-o", str(out)],
        check=True, capture_output=True,
    )


def luma(png: Path) -> list[list[int]]:
    bmp = png.with_suffix(".bmp")
    subprocess.run(["sips", "-s", "format", "bmp", str(png), "--out", str(bmp)],
                   check=True, capture_output=True)
    data = bmp.read_bytes()
    off = struct.unpack_from("<I", data, 10)[0]
    w = struct.unpack_from("<i", data, 18)[0]
    raw_h = struct.unpack_from("<i", data, 22)[0]
    depth = struct.unpack_from("<H", data, 28)[0]
    h, bottom_up = abs(raw_h), raw_h > 0
    stride = ((w * depth // 8) + 3) // 4 * 4
    step = depth // 8
    rows = []
    for y in range(h):
        src = off + (h - 1 - y if bottom_up else y) * stride
        row = []
        for x in range(w):
            p = src + x * step
            b, g, r = data[p], data[p + 1], data[p + 2]
            row.append((r * 299 + g * 587 + b * 114) // 1000)
        rows.append(row)
    return rows


def components(rows: list[list[int]]) -> list[int]:
    """Sizes of each 4-connected ink component, largest first."""
    h, w = len(rows), len(rows[0])
    seen = [[False] * w for _ in range(h)]
    sizes = []
    for y in range(h):
        for x in range(w):
            if rows[y][x] >= INK or seen[y][x]:
                continue
            stack, n = [(y, x)], 0
            seen[y][x] = True
            while stack:
                cy, cx = stack.pop()
                n += 1
                for ny, nx in ((cy+1, cx), (cy-1, cx), (cy, cx+1), (cy, cx-1)):
                    if (0 <= ny < h and 0 <= nx < w
                            and rows[ny][nx] < INK and not seen[ny][nx]):
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            sizes.append(n)
    return sorted(sizes, reverse=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("svg", type=Path)
    ap.add_argument("--sizes", type=int, nargs="+", default=[16, 64, 300])
    ap.add_argument("--expect", type=int, default=1,
                    help="expected component count (default 1: fully joined)")
    args = ap.parse_args()

    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        for size in args.sizes:
            png = Path(tmp) / f"r{size}.png"
            render(args.svg, size, png)
            sizes = components(luma(png))
            # Ignore specks under 0.2% of the canvas: those are anti-aliasing.
            floor = max(1, int(size * size * 0.002))
            real = [s for s in sizes if s >= floor]
            status = "ok" if len(real) == args.expect else "MISMATCH"
            if len(real) != args.expect:
                ok = False
            print(f"  {size:>4}px: {len(real)} component(s) {real}  {status}")

    print(f"\n{'PASS' if ok else 'FAIL'}: expected {args.expect} connected "
          f"component(s) at every size")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
