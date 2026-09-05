#!/usr/bin/env python3
"""Structural validator for logo SVGs.

Checks the conventions in references/svg-craft.md: viewBox present, no raster
embeds or external references, no live text, no filters/masks, strokes above the
16-pixel floor, and reasonable path complexity.

Usage:
    python validate_svg.py out/logo/
    python validate_svg.py out/logo/icon-color.svg
    python validate_svg.py out/logo/ --icon-size 16 --lockup-size 120

The stroke floor is checked against the smallest width each component is actually
rendered at: 16px for an icon or favicon, 120px for a wordmark or lock-up (which
is never deployed at favicon width). Component type comes from the filename, with
aspect ratio as the fallback.

Exit code 1 if any error is found, 0 otherwise. Warnings never fail the run but
require a written justification per the skill's Phase 6 gate.
"""

from __future__ import annotations

import argparse
import contextlib
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Path complexity above this suggests detail that will not survive small sizes.
MAX_PATH_COMMANDS = 120
MAX_TOTAL_COMMANDS = 400
MAX_BYTES = 30_000

# Filename stems whose smallest real-world render width is the favicon size.
ICON_COMPONENTS = ("icon", "favicon", "symbol", "mark", "app")
# Above this width-to-height ratio, an unnamed file is treated as a lock-up.
LOCKUP_ASPECT = 2.5

PATH_CMD_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")
NUM_RE = re.compile(r"-?\d*\.?\d+")


def local(tag: str) -> str:
    """Strip the namespace from an element tag."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


class Report:
    def __init__(self, path: Path):
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def parse_viewbox(value: str) -> tuple[float, float, float, float] | None:
    parts = re.split(r"[,\s]+", value.strip())
    if len(parts) != 4:
        return None
    try:
        return tuple(float(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        return None


def stroke_widths(root: ET.Element) -> list[float]:
    """Collect every explicit stroke-width, from attributes and inline styles."""
    widths: list[float] = []
    for el in root.iter():
        raw = el.get("stroke-width")
        if raw is None:
            style = el.get("style", "")
            m = re.search(r"stroke-width\s*:\s*([\d.]+)", style)
            raw = m.group(1) if m else None
        if raw is None:
            continue
        m = NUM_RE.match(raw.strip())
        if m:
            with contextlib.suppress(ValueError):
                widths.append(float(m.group()))
    return widths


def has_stroked_geometry(root: ET.Element) -> bool:
    for el in root.iter():
        stroke = el.get("stroke") or ""
        if "stroke:" in el.get("style", ""):
            return True
        if stroke and stroke.lower() != "none":
            return True
    return False


def min_render_width(
    path: Path, vb: tuple[float, float, float, float] | None,
    icon_size: int, lockup_size: int,
) -> tuple[int, str]:
    """Smallest width in px this component is actually deployed at.

    An icon has to survive 16px; a horizontal lock-up never appears that small,
    so measuring its strokes against a favicon floor produces false failures.
    """
    comp = path.stem.lower().partition("-")[0]
    if comp in ICON_COMPONENTS:
        return icon_size, f"{comp} rendered at {icon_size}px"
    if comp in ("wordmark", "horizontal", "stacked", "lockup"):
        return lockup_size, f"{comp} rendered at {lockup_size}px"
    if vb and vb[3] > 0 and (vb[2] / vb[3]) > LOCKUP_ASPECT:
        return lockup_size, f"wide aspect, treated as a lock-up at {lockup_size}px"
    return icon_size, f"treated as an icon at {icon_size}px"


def check_file(path: Path, icon_size: int, lockup_size: int) -> Report:  # noqa: PLR0912, PLR0915
    """Run every structural check against one SVG.

    Deliberately one flat sequence rather than a chain of small helpers: the
    checks are independent, order-insensitive, and easiest to audit when the
    whole list is readable top to bottom. Splitting it would scatter the rules
    this file exists to document.
    """
    rep = Report(path)

    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        rep.warn(
            f"file is {len(raw):,} bytes (over {MAX_BYTES:,}) - likely carrying "
            f"editor cruft or excessive detail"
        )

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        rep.error(f"not valid XML: {exc}")
        return rep

    if local(root.tag) != "svg":
        rep.error(f"root element is <{local(root.tag)}>, expected <svg>")
        return rep

    # --- viewBox -----------------------------------------------------------
    vb_raw = root.get("viewBox")
    vb = None
    if not vb_raw:
        rep.error("missing viewBox - the mark will not scale to its container")
    else:
        vb = parse_viewbox(vb_raw)
        if vb is None:
            rep.error(f"malformed viewBox: {vb_raw!r}")

    if root.get("width") or root.get("height"):
        rep.warn(
            "fixed width/height on the master file - remove them so the mark "
            "scales; fixed dimensions belong to raster exports"
        )

    # --- forbidden content -------------------------------------------------
    tag_counts: dict[str, int] = {}
    total_cmds = 0

    for el in root.iter():
        name = local(el.tag)
        tag_counts[name] = tag_counts.get(name, 0) + 1

        if name == "image":
            rep.error("contains <image> - a logo must not embed a raster")
        elif name == "script":
            rep.error("contains <script> - remove it")
        elif name in ("text", "tspan"):
            rep.error(
                f"contains live <{name}> - convert glyphs to paths so the mark "
                f"renders identically without the font"
            )
        elif name == "filter":
            rep.error(
                "contains <filter> - filters do not survive print, favicon "
                "rasterisation, or embroidery"
            )
        elif name in ("mask", "clipPath"):
            rep.warn(
                f"contains <{name}> - flatten to geometry if this is the icon; "
                f"masks are unreliable across rasterisers"
            )
        elif name == "foreignObject":
            rep.error("contains <foreignObject> - remove it")

        for attr, value in el.attrib.items():
            attr_local = local(attr)
            if attr_local in ("href", "src") or attr == f"{{{XLINK_NS}}}href":
                if value.strip().startswith(("http://", "https://", "//")):
                    rep.error(f"external reference: {value[:60]}")
                elif value.strip().startswith("data:image"):
                    rep.error("embedded base64 raster in href")
            if attr_local == "style" and "url(" in value and "http" in value:
                rep.error("external url() in style attribute")

        if name == "path":
            d = el.get("d", "")
            n = len(PATH_CMD_RE.findall(d))
            total_cmds += n
            if n > MAX_PATH_COMMANDS:
                rep.warn(
                    f"a path has {n} commands (over {MAX_PATH_COMMANDS}) - likely "
                    f"auto-traced or over-detailed; redraw with points at curve extremes"
                )

    render_px, render_why = min_render_width(path, vb, icon_size, lockup_size)

    if total_cmds > MAX_TOTAL_COMMANDS:
        rep.warn(
            f"{total_cmds} total path commands - detail at this level will not "
            f"survive the {render_px}px test"
        )

    # --- accessibility -----------------------------------------------------
    if not tag_counts.get("title") and not root.get("aria-label"):
        rep.warn("no <title> or aria-label - add one for accessibility")

    # --- stroke floor ------------------------------------------------------
    if vb and has_stroked_geometry(root):
        vb_w = vb[2]
        widths = stroke_widths(root)
        if not widths:
            rep.warn(
                "geometry is stroked but no explicit stroke-width is set - the "
                "default of 1 unit will vanish at small sizes"
            )
        else:
            floor = vb_w / render_px
            thinnest = min(widths)
            if thinnest < floor:
                rep.error(
                    f"thinnest stroke is {thinnest:g} units; below the floor of "
                    f"{floor:.2f} units for {render_why} "
                    f"(viewBox width {vb_w:g}) - it will render under one pixel"
                )
            elif thinnest < floor * 1.25:
                rep.warn(
                    f"thinnest stroke is {thinnest:g} units, only just above the "
                    f"{floor:.2f}-unit floor - verify it visually at {render_px}px"
                )

        for el in root.iter():
            stroke = el.get("stroke") or ""
            if (stroke and stroke.lower() != "none"
                    and (not el.get("stroke-linecap") or not el.get("stroke-linejoin"))):
                rep.note(
                    "stroked geometry without explicit linecap/linejoin - set "
                    "them rather than relying on renderer defaults, or outline "
                    "the strokes to fills"
                )
                break

    # --- colour handling ---------------------------------------------------
    stem = path.stem.lower()
    fills = {el.get("fill", "").lower() for el in root.iter()}
    if stem.endswith(("-black", "-white")) and "currentcolor" not in fills:
        hexes = {f for f in fills if f.startswith("#")}
        expected = "#000000" if stem.endswith("-black") else "#ffffff"
        off = {h for h in hexes if h not in (expected, expected[:4])}
        if off:
            rep.warn(
                f"single-colour variant uses {sorted(off)} - it should be pure "
                f'{expected} or fill="currentColor"'
            )

    return rep


def collect(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(p for p in target.rglob("*.svg"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate logo SVGs.")
    ap.add_argument("target", type=Path, help="an .svg file or a directory of them")
    ap.add_argument(
        "--icon-size",
        type=int,
        default=16,
        help="smallest render width in px for icons/favicons (default: 16)",
    )
    ap.add_argument(
        "--lockup-size",
        type=int,
        default=120,
        help="smallest render width in px for wordmarks/lock-ups (default: 120)",
    )
    args = ap.parse_args()

    if not args.target.exists():
        print(f"error: {args.target} does not exist", file=sys.stderr)
        return 2

    files = collect(args.target)
    if not files:
        print(f"error: no .svg files found in {args.target}", file=sys.stderr)
        return 2

    total_err = total_warn = 0

    for f in files:
        rep = check_file(f, args.icon_size, args.lockup_size)
        total_err += len(rep.errors)
        total_warn += len(rep.warnings)

        if rep.errors or rep.warnings or rep.notes:
            print(f"\n{f}")
            for m in rep.errors:
                print(f"  ERROR  {m}")
            for m in rep.warnings:
                print(f"  WARN   {m}")
            for m in rep.notes:
                print(f"  note   {m}")
        else:
            print(f"\n{f}\n  ok")

    print(
        f"\n{len(files)} file(s): {total_err} error(s), {total_warn} warning(s)"
    )
    if total_warn and not total_err:
        print("Warnings require a written justification before Phase 6 passes.")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
