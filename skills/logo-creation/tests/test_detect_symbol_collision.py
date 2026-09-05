"""Tests for scripts/detect_symbol_collision.py.

Every detector gets a fixture that trips it and one that must not. A collision
detector that flags every mark is as useless as one that flags nothing, so the
negative cases carry as much weight as the positive ones.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "detect_symbol_collision.py"
DEMO = ROOT / "examples" / "demo"

sys.path.insert(0, str(ROOT / "scripts"))
import detect_symbol_collision as D

pytestmark = pytest.mark.skipif(
    not (shutil.which("rsvg-convert") or shutil.which("resvg")
         or shutil.which("inkscape")),
    reason="needs an SVG renderer",
)

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
        'role="img" aria-label="t"><title>t</title>')


def write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(HEAD + body + "</svg>", encoding="utf-8")
    return p


def stroke(d: str, w: float = 6) -> str:
    return (f'<path d="{d}" fill="none" stroke="#16181C" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


# --- radial / spinner ------------------------------------------------------

def radial_svg(spokes: int = 8) -> str:
    parts = []
    for i in range(spokes):
        a = 2 * math.pi * i / spokes
        x1, y1 = 32 + 11 * math.cos(a), 32 + 11 * math.sin(a)
        x2, y2 = 32 + 22 * math.cos(a), 32 + 22 * math.sin(a)
        parts.append(stroke(f"M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f}"))
    return "".join(parts)


def test_radial_spokes_collide(tmp_path):
    svg = write(tmp_path, "radial.svg", radial_svg(8))
    found = D.collisions(svg)
    assert any("spinner" in f for f in found), found


def test_asymmetric_mark_does_not_collide(tmp_path):
    # An H whose crossbar breaks and steps up: deliberately not radial.
    svg = write(tmp_path, "asym.svg",
                stroke("M18 14 L18 50") + stroke("M46 14 L46 50")
                + stroke("M18 36 L32 36") + stroke("M32 36 L32 26 L46 26"))
    assert D.collisions(svg) == []


# --- parallel bars / hamburger --------------------------------------------

def test_regular_parallel_bars_collide(tmp_path):
    bars = "".join(
        f'<rect x="14" y="{y}" width="36" height="4" fill="#16181C"/>'
        for y in (14, 24, 34, 44)
    )
    svg = write(tmp_path, "bars.svg", bars)
    found = D.collisions(svg)
    assert any("parallel bars" in f for f in found), found


def test_irregular_bars_do_not_collide(tmp_path):
    # Same element count as the hamburger fixture, but the thicknesses and the
    # gaps both vary well outside tolerance, so this must NOT be flagged.
    body = (
        '<rect x="14" y="10" width="36" height="3" fill="#16181C"/>'
        '<rect x="14" y="20" width="18" height="10" fill="#16181C"/>'
        '<rect x="30" y="46" width="20" height="4" fill="#16181C"/>'
    )
    svg = write(tmp_path, "irregular.svg", body)
    found = D.collisions(svg)
    assert not any("parallel bars" in f for f in found), found


def test_white_on_white_variant_is_not_flagged(tmp_path):
    """A blank frame is trivially symmetric; it must not report a spinner.

    This is the normal case for the *-white.svg variants in a deliverable set,
    rendered against the white analysis background.
    """
    body = ('<path d="M18 14 L18 50" fill="none" stroke="#FFFFFF" '
            'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    svg = write(tmp_path, "white.svg", body)
    assert D.collisions(svg) == []


# --- lattice / dice -------------------------------------------------------

def test_lattice_of_blobs_collides(tmp_path):
    dots = "".join(
        f'<rect x="{x}" y="{y}" width="8" height="8" fill="#16181C"/>'
        for y in (14, 28, 42) for x in (14, 28, 42)
    )
    svg = write(tmp_path, "lattice.svg", dots)
    found = D.collisions(svg)
    assert any("lattice" in f for f in found), found


def test_two_blobs_do_not_collide(tmp_path):
    body = ('<rect x="14" y="14" width="9" height="9" fill="#16181C"/>'
            '<rect x="40" y="40" width="9" height="9" fill="#16181C"/>')
    svg = write(tmp_path, "two.svg", body)
    found = D.collisions(svg)
    assert not any("lattice" in f for f in found), found


# --- the bundled demo must stay clean -------------------------------------

def test_bundled_demo_icon_is_clean():
    """Calibration guard: thresholds must not reject a known-good mark."""
    assert D.collisions(DEMO / "icon-color.svg") == []


# --- helpers behave -------------------------------------------------------

def test_rotational_symmetry_of_blank_is_total(tmp_path):
    rows = [[255] * 20 for _ in range(20)]
    assert D.rotational_symmetry(rows) == pytest.approx(1.0)


def test_horizontal_bands_counts_and_flags_regularity():
    width = 40
    rows = []
    for y in range(40):
        band = 8 <= y < 12 or 18 <= y < 22 or 28 <= y < 32
        rows.append([0 if band else 255] * width)
    count, regular = D.horizontal_bands(rows)
    assert count == 3
    assert regular is True


# --- CLI contract ---------------------------------------------------------

def test_cli_exits_zero_on_clean_directory():
    res = subprocess.run([sys.executable, str(SCRIPT), str(DEMO)],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stdout + res.stderr


def test_cli_exits_one_on_colliding_file(tmp_path):
    svg = write(tmp_path, "radial.svg", radial_svg(8))
    res = subprocess.run([sys.executable, str(SCRIPT), str(svg)],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 1
    assert "COLLIDES" in res.stdout


def test_cli_usage_error_without_argument():
    res = subprocess.run([sys.executable, str(SCRIPT)],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 2
