"""Tests for scripts/package_brand.py."""

from __future__ import annotations

import struct
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "package_brand.py"

sys.path.insert(0, str(ROOT / "scripts"))
import package_brand as P

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M0 0"/></svg>'


def make_png(size: int) -> bytes:
    """A PNG header good enough for the size probe, plus a plausible tail."""
    ihdr = struct.pack(">II", size, size) + b"\x08\x06\x00\x00\x00"
    return (
        P.PNG_MAGIC
        + struct.pack(">I", 13) + b"IHDR" + ihdr + b"\x00\x00\x00\x00"
        + struct.pack(">I", 0) + b"IEND" + b"\xaeB`\x82"
    )


@pytest.fixture
def logo_dir(tmp_path: Path) -> Path:
    d = tmp_path / "logo"
    d.mkdir()
    for stem in (*P.REQUIRED_SVG, *P.RECOMMENDED_SVG):
        (d / f"{stem}.svg").write_text(SVG, encoding="utf-8")
    (d / "BRAND.md").write_text("# Brand\n", encoding="utf-8")
    (d / "contact-sheet.html").write_text("<html></html>", encoding="utf-8")
    return d


@pytest.fixture
def exports_dir(tmp_path: Path) -> Path:
    d = tmp_path / "exports"
    d.mkdir()
    for size in P.RECOMMENDED_PNG:
        (d / f"icon-color-{size}.png").write_bytes(make_png(size))
    (d / "horizontal-color.pdf").write_bytes(b"%PDF-1.4\n")
    (d / "horizontal-color.eps").write_bytes(b"%!PS-Adobe-3.0 EPSF-3.0\n")
    return d


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, check=False,
    )


# --- helpers -----------------------------------------------------------------

def test_slug_handles_punctuation_and_case():
    assert P.slug("G Point Hair Salon") == "g-point-hair-salon"
    assert P.slug("Acme, Inc.") == "acme-inc"
    assert P.slug("!!!") == "brand"


def test_png_size_reads_ihdr_and_rejects_non_png():
    assert P.png_size(make_png(48)) == (48, 48)
    assert P.png_size(b"not a png at all, really truly not") is None


def test_build_ico_wraps_pngs_with_correct_directory():
    ico = P.build_ico([make_png(48), make_png(16), make_png(32)])
    reserved, kind, count = struct.unpack("<HHH", ico[:6])
    assert (reserved, kind, count) == (0, 1, 3)
    sizes = []
    for i in range(count):
        w, h, _, _, _, _, length, offset = struct.unpack(
            "<BBBBHHII", ico[6 + 16 * i:22 + 16 * i]
        )
        sizes.append(w)
        assert w == h
        assert ico[offset:offset + 8] == P.PNG_MAGIC
        assert offset + length <= len(ico)
    assert sizes == sorted(sizes), "entries must be ordered smallest first"


def test_build_ico_encodes_256_as_zero():
    """The ICO spec stores 256 in a single byte as 0."""
    ico = P.build_ico([make_png(256)])
    assert ico[6] == 0 and ico[7] == 0


# --- gathering ---------------------------------------------------------------

def test_files_are_routed_by_extension(logo_dir: Path, exports_dir: Path):
    kit = P.Kit("Demo")
    P.gather(kit, logo_dir, [exports_dir])
    assert "logo/icon-color.svg" in kit.files
    assert "png/icon-color-16.png" in kit.files
    assert "print/horizontal-color.pdf" in kit.files
    assert "print/horizontal-color.eps" in kit.files
    assert "preview/contact-sheet.html" in kit.files
    assert "BRAND.md" in kit.files
    assert not any(a.startswith("png/") and a.endswith(".pdf") for a in kit.files)


def test_favicon_ico_built_from_small_icon_pngs(logo_dir: Path, exports_dir: Path):
    kit = P.Kit("Demo")
    P.gather(kit, logo_dir, [exports_dir])
    P.make_favicon(kit)
    assert struct.unpack("<H", kit.files["favicon.ico"][4:6])[0] == len(P.ICO_SIZES)


def test_favicon_skipped_with_a_note_when_no_small_pngs(logo_dir: Path, tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    kit = P.Kit("Demo")
    P.gather(kit, logo_dir, [empty])
    P.make_favicon(kit)
    assert "favicon.ico" not in kit.files
    assert any("favicon.ico" in n for n in kit.notes)


# --- completeness ------------------------------------------------------------

def test_complete_set_reports_no_gaps(logo_dir: Path, exports_dir: Path):
    kit = P.Kit("Demo")
    P.gather(kit, logo_dir, [exports_dir])
    P.check(kit)
    assert kit.missing == []


def test_missing_required_variant_is_recorded(logo_dir: Path, exports_dir: Path):
    (logo_dir / "stacked-white.svg").unlink()
    kit = P.Kit("Demo")
    P.gather(kit, logo_dir, [exports_dir])
    P.check(kit)
    assert "logo/stacked-white.svg" in kit.missing


def test_missing_brand_doc_is_required_not_merely_noted(
    logo_dir: Path, exports_dir: Path
):
    (logo_dir / "BRAND.md").unlink()
    kit = P.Kit("Demo")
    P.gather(kit, logo_dir, [exports_dir])
    P.check(kit)
    assert any("BRAND.md" in m for m in kit.missing)


def test_absent_print_formats_are_noted_not_fatal(logo_dir: Path, tmp_path: Path):
    d = tmp_path / "png_only"
    d.mkdir()
    (d / "icon-color-16.png").write_bytes(make_png(16))
    kit = P.Kit("Demo")
    P.gather(kit, logo_dir, [d])
    P.check(kit)
    assert kit.missing == []
    assert any("EPS" in n for n in kit.notes)
    assert any("PDF" in n for n in kit.notes)


# --- CLI ---------------------------------------------------------------------

def test_cli_builds_expected_archive(logo_dir: Path, exports_dir: Path, tmp_path: Path):
    out = tmp_path / "kit.zip"
    r = run(str(logo_dir), "--name", "Demo Brand",
            "--exports", str(exports_dir), "--out", str(out))
    assert r.returncode == 0, r.stderr
    names = set(zipfile.ZipFile(out).namelist())
    assert {"README.txt", "BRAND.md", "favicon.ico",
            "logo/icon-color.svg"} <= names


def test_readme_names_the_brand(logo_dir: Path, exports_dir: Path, tmp_path: Path):
    out = tmp_path / "kit.zip"
    run(str(logo_dir), "--name", "Demo Brand",
        "--exports", str(exports_dir), "--out", str(out))
    readme = zipfile.ZipFile(out).read("README.txt").decode()
    assert readme.startswith("Demo Brand — brand assets")
    assert "horizontal-color.svg" in readme


def test_incomplete_set_refuses_to_build(logo_dir: Path, tmp_path: Path):
    (logo_dir / "icon-black.svg").unlink()
    out = tmp_path / "kit.zip"
    r = run(str(logo_dir), "--name", "Demo", "--out", str(out))
    assert r.returncode == 1
    assert "icon-black.svg" in r.stderr
    assert not out.exists(), "an incomplete kit must not be written"


def test_force_ships_incomplete_set(logo_dir: Path, tmp_path: Path):
    (logo_dir / "icon-black.svg").unlink()
    out = tmp_path / "kit.zip"
    r = run(str(logo_dir), "--name", "Demo", "--out", str(out), "--force")
    assert r.returncode == 0
    assert out.exists()
    assert "MISSING" in r.stdout


def test_no_ico_flag_skips_generation(logo_dir: Path, exports_dir: Path, tmp_path: Path):
    out = tmp_path / "kit.zip"
    run(str(logo_dir), "--name", "Demo", "--exports", str(exports_dir),
        "--out", str(out), "--no-ico")
    assert "favicon.ico" not in zipfile.ZipFile(out).namelist()


def test_archive_is_reproducible(logo_dir: Path, exports_dir: Path, tmp_path: Path):
    a, b = tmp_path / "a.zip", tmp_path / "b.zip"
    for out in (a, b):
        run(str(logo_dir), "--name", "Demo",
            "--exports", str(exports_dir), "--out", str(out))
    assert a.read_bytes() == b.read_bytes()


def test_missing_directory_exits_two(tmp_path: Path):
    r = run(str(tmp_path / "nope"), "--name", "Demo")
    assert r.returncode == 2
