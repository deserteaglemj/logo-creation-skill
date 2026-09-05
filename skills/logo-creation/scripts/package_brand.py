#!/usr/bin/env python3
"""Package a finished identity system into one client-ready brand.zip.

Collects the SVG masters, the raster and print exports, and the usage guide into
a single archive laid out the way a recipient expects to find it, generates a
multi-resolution favicon.ico, writes a plain-text README explaining which file to
use when, and refuses to build if the deliverable matrix has holes.

Usage:
    python package_brand.py out/logo --name "Brand Name"
    python package_brand.py out/logo --name "Brand Name" --exports out/exports
    python package_brand.py out/logo --name "Brand Name" --out dist/brand.zip --force

Standard library only. Nothing here rasterises or converts: generate the PNG,
PDF and EPS exports first (Affinity, Inkscape, or whatever renders your SVG
faithfully) and point --exports at them. A kit missing them still builds with
--force, but the missing pieces are the ones a sign shop will ask for.

Exit code 1 if a required deliverable is missing (unless --force), 0 otherwise.
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import zipfile
from pathlib import Path

# Fixed timestamp so rebuilding an unchanged kit produces an identical archive.
ZIP_DATE = (2020, 1, 1, 0, 0, 0)

# The Phase 5 matrix from references/deliverables.md. Missing any of these means
# someone downstream will improvise the case badly.
REQUIRED_SVG = (
    "icon-color", "icon-black", "icon-white",
    "wordmark-color", "wordmark-black", "wordmark-white",
    "horizontal-color", "horizontal-black", "horizontal-white",
    "stacked-color", "stacked-black", "stacked-white",
    "favicon",
)
RECOMMENDED_SVG = ("icon-darkmode", "horizontal-darkmode")

# Favicon, iOS home screen, Android/PWA, store listing.
RECOMMENDED_PNG = (16, 32, 48, 180, 192, 512, 1024)
ICO_SIZES = (16, 32, 48)
# The ICO directory stores a dimension in one byte, so 256 is written as 0.
ICO_MAX = 256

PRINT_EXT = {".pdf", ".eps"}
DOC_EXT = {".md", ".txt", ".html", ".pdf"}

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "brand"


def png_size(data: bytes) -> tuple[int, int] | None:
    """Width and height from a PNG's IHDR, or None if it is not a PNG."""
    if not data.startswith(PNG_MAGIC) or len(data) < 24:
        return None
    w, h = struct.unpack(">II", data[16:24])
    return int(w), int(h)


def build_ico(pngs: list[bytes]) -> bytes:
    """A multi-resolution .ico wrapping PNG payloads directly.

    Every browser and Windows version still in service reads PNG-in-ICO, so
    there is no need to re-encode to BMP. Sizes are read from each PNG's own
    header rather than trusted from the filename.
    """
    entries = []
    for data in pngs:
        size = png_size(data)
        if size is None:
            continue
        entries.append((size[0], size[1], data))
    entries.sort(key=lambda e: e[0])

    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = len(header) + 16 * len(entries)
    directory = b""
    payload = b""
    for w, h, data in entries:
        directory += struct.pack(
            "<BBBBHHII",
            0 if w >= ICO_MAX else w,
            0 if h >= ICO_MAX else h,
            0, 0, 1, 32,
            len(data), offset,
        )
        payload += data
        offset += len(data)
    return header + directory + payload


class Kit:
    """Everything destined for the archive, keyed by its path inside the zip."""

    def __init__(self, name: str):
        self.name = name
        self.files: dict[str, bytes] = {}
        self.missing: list[str] = []
        self.notes: list[str] = []

    def add(self, arcname: str, data: bytes) -> None:
        self.files[arcname] = data

    def add_path(self, arcname: str, path: Path) -> None:
        self.add(arcname, path.read_bytes())

    def has_prefix(self, prefix: str) -> bool:
        return any(k.startswith(prefix) for k in self.files)


def gather(kit: Kit, logo_dir: Path, export_dirs: list[Path]) -> None:
    """Route every source file to its folder in the archive.

    Extension decides the destination, not the source directory: exports land in
    one folder in practice, and a client should never have to know that.
    """
    for path in sorted(logo_dir.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext == ".svg":
            kit.add_path(f"logo/{path.name}", path)
        elif path.name.lower().startswith("brand") and ext in DOC_EXT:
            kit.add_path(path.name, path)
        elif path.name.lower().startswith("contact-sheet"):
            kit.add_path(f"preview/{path.name}", path)

    for d in export_dirs:
        for path in sorted(d.rglob("*")):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            if ext == ".png":
                kit.add_path(f"png/{path.name}", path)
            elif ext in PRINT_EXT:
                kit.add_path(f"print/{path.name}", path)
            elif ext == ".svg":
                kit.add_path(f"logo/{path.name}", path)


def make_favicon(kit: Kit) -> None:
    """Assemble favicon.ico from the small icon PNGs already in the kit."""
    by_size: dict[int, bytes] = {}
    for arc, data in kit.files.items():
        if not arc.startswith("png/"):
            continue
        stem = Path(arc).stem.lower()
        if not (stem.startswith(("icon", "favicon"))):
            continue
        size = png_size(data)
        if size and size[0] == size[1] and size[0] in ICO_SIZES:
            by_size.setdefault(size[0], data)

    if not by_size:
        kit.notes.append(
            "no favicon.ico generated - needs square icon PNGs at "
            f"{'/'.join(str(s) for s in ICO_SIZES)}px in the exports"
        )
        return
    kit.add("favicon.ico", build_ico([by_size[k] for k in sorted(by_size)]))


def check(kit: Kit) -> None:
    """Compare what was gathered against the deliverable matrix."""
    for stem in REQUIRED_SVG:
        if f"logo/{stem}.svg" not in kit.files:
            kit.missing.append(f"logo/{stem}.svg")

    for stem in RECOMMENDED_SVG:
        if f"logo/{stem}.svg" not in kit.files:
            kit.notes.append(f"no {stem}.svg - dark surfaces will use the light mark")

    png_widths = {
        s[0] for arc, data in kit.files.items()
        if arc.startswith("png/") and (s := png_size(data)) and s[0] == s[1]
    }
    absent = [str(s) for s in RECOMMENDED_PNG if s not in png_widths]
    if absent:
        kit.notes.append(
            f"no square PNG at {', '.join(absent)}px - favicon, app-icon and "
            f"store-listing slots will be rasterised by whoever needs them"
        )

    for ext in sorted(PRINT_EXT):
        if not any(a.endswith(ext) for a in kit.files if a.startswith("print/")):
            kit.notes.append(
                f"no {ext.upper()[1:]} in print/ - print and signage suppliers "
                f"routinely require one before they will quote"
            )

    if not any(a.lower().startswith("brand") for a in kit.files):
        kit.missing.append("BRAND.md (clear space, minimum sizes, colours, misuse)")


README = """{name} — brand assets
{rule}

WHICH FILE DO I USE?

  Website, email signature, most things   logo/horizontal-color.svg
  Square or portrait space                logo/stacked-color.svg
  Avatar, app icon, favicon               logo/icon-color.svg
  On a dark background or a photo         any -white variant
  One-colour print, engraving, stamps     any -black variant
  Dark-mode interfaces                    any -darkmode variant
  Browser tab                             favicon.ico
  Anything a printer or sign shop touches print/ (PDF or EPS)
  Social profile, store listing           png/ at the size you need


FOLDERS

  logo/     Vector masters (SVG). The source of truth - every other file in
            this kit was generated from these. Scales to any size without
            loss. Send these to a designer or developer.

  png/      Fixed-size rasters for slots that require exact pixel dimensions:
            favicons, iOS and Android home-screen icons, social avatars,
            store listings. Do not scale a PNG up - go back to the SVG.

  print/    PDF and EPS. Vector formats that print shops, sign makers, vinyl
            cutters and embroidery digitisers accept. Hand over the whole
            folder; they will pick what their workflow needs.

  preview/  A self-contained page showing every variant and how the mark
            behaves small, blurred, and in one colour. Open it in a browser.

  favicon.ico   Multi-resolution browser-tab icon.

  BRAND.md  Clear space, minimum sizes, colour values, and what not to do.
            Read this before using the mark anywhere.


THE RULES THAT MATTER MOST

  - Do not stretch, squash, or rotate the mark.
  - Do not recolour it outside the documented palette.
  - Do not add shadows, glows, bevels, or outlines.
  - Do not rebuild a lock-up by moving the pieces - use the supplied file.
  - Do not place the colour version on a busy photograph; use the white one.
  - Respect the minimum sizes in BRAND.md. Below them the mark stops reading.

Full detail in BRAND.md.
"""


def write_zip(kit: Kit, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for arc in sorted(kit.files):
            info = zipfile.ZipInfo(arc, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, kit.files[arc])


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Package a finished logo system into a client-ready brand.zip."
    )
    ap.add_argument("logo_dir", type=Path, help="the SVG master directory (out/logo/)")
    ap.add_argument("--name", required=True, help="brand name, used in the README")
    ap.add_argument(
        "--exports", type=Path, action="append", default=[],
        help="directory of PNG/PDF/EPS exports (repeatable)",
    )
    ap.add_argument("--out", type=Path, help="output .zip (default: <slug>-brand-kit.zip)")
    ap.add_argument(
        "--force", action="store_true",
        help="build even if required deliverables are missing",
    )
    ap.add_argument("--no-ico", action="store_true", help="skip favicon.ico generation")
    args = ap.parse_args()

    if not args.logo_dir.is_dir():
        print(f"error: {args.logo_dir} is not a directory", file=sys.stderr)
        return 2
    for d in args.exports:
        if not d.is_dir():
            print(f"error: {d} is not a directory", file=sys.stderr)
            return 2

    kit = Kit(args.name)
    gather(kit, args.logo_dir, args.exports)
    if not args.no_ico:
        make_favicon(kit)
    check(kit)

    kit.add("README.txt", README.format(
        name=args.name, rule="=" * (len(args.name) + 16)
    ).encode("utf-8"))

    if kit.missing and not args.force:
        print("Missing required deliverables:", file=sys.stderr)
        for m in kit.missing:
            print(f"  {m}", file=sys.stderr)
        print(
            "\nThe kit was not written. Complete Phase 5, or pass --force to ship "
            "an incomplete set deliberately.",
            file=sys.stderr,
        )
        return 1

    out = args.out or Path(f"{slug(args.name)}-brand-kit.zip")
    write_zip(kit, out)

    print(f"{out}  ({out.stat().st_size / 1024:.0f} KB, {len(kit.files)} files)")
    for folder in ("logo/", "png/", "print/", "preview/"):
        n = sum(1 for a in kit.files if a.startswith(folder))
        print(f"  {folder:<10} {n} file(s)")

    if kit.missing:
        print("\nShipped with gaps (--force):")
        for m in kit.missing:
            print(f"  MISSING  {m}")
    for n in kit.notes:
        print(f"  note     {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
