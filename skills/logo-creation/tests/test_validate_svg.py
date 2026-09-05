"""Tests for scripts/validate_svg.py.

Each check gets a fixture that trips it and, where the distinction matters, one
that must not — a validator that flags everything is as useless as one that
flags nothing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_svg.py"
DEMO = ROOT / "examples" / "demo"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_svg as V


def write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


GOOD_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" '
    'aria-label="X"><title>X</title>'
    '<path d="M8 32 L56 32" fill="none" stroke="#000" stroke-width="8" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


def check(path: Path, icon_size: int = 16, lockup_size: int = 120) -> V.Report:
    return V.check_file(path, icon_size, lockup_size)


# --- things that must pass ---------------------------------------------------

def test_clean_icon_has_no_errors(tmp_path):
    rep = check(write(tmp_path, "icon-color.svg", GOOD_ICON))
    assert rep.errors == []
    assert rep.warnings == []


def test_bundled_demo_is_clean():
    """The shipped example must stay valid — it is the quickstart."""
    files = sorted(DEMO.glob("*.svg"))
    assert files, "demo fixtures missing"
    for f in files:
        rep = check(f)
        assert rep.errors == [], f"{f.name}: {rep.errors}"


# --- structural errors -------------------------------------------------------

def test_missing_viewbox_is_an_error(tmp_path):
    body = GOOD_ICON.replace(' viewBox="0 0 64 64"', "")
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("viewBox" in e for e in rep.errors)


def test_live_text_is_an_error(tmp_path):
    body = GOOD_ICON.replace("</svg>", '<text x="0" y="10">hi</text></svg>')
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("<text>" in e for e in rep.errors)


def test_raster_embed_is_an_error(tmp_path):
    body = GOOD_ICON.replace("</svg>", '<image href="a.png"/></svg>')
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("<image>" in e for e in rep.errors)


def test_external_reference_is_an_error(tmp_path):
    body = GOOD_ICON.replace("</svg>", '<use href="https://evil.example/x.svg"/></svg>')
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("external reference" in e for e in rep.errors)


def test_script_element_is_an_error(tmp_path):
    body = GOOD_ICON.replace("</svg>", "<script>alert(1)</script></svg>")
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("<script>" in e for e in rep.errors)


def test_filter_is_an_error(tmp_path):
    body = GOOD_ICON.replace("</svg>", '<filter id="f"></filter></svg>')
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("<filter>" in e for e in rep.errors)


def test_malformed_xml_is_an_error(tmp_path):
    rep = check(write(tmp_path, "icon-color.svg", "<svg><path></svg>"))
    assert any("not valid XML" in e for e in rep.errors)


def test_wrong_root_element_is_an_error(tmp_path):
    rep = check(write(tmp_path, "icon-color.svg", "<html></html>"))
    assert any("root element" in e for e in rep.errors)


# --- the component-aware stroke floor ----------------------------------------
# This is the regression that matters most: an early version measured every file
# against 16px and failed wide lock-ups that are never rendered that small.

def test_hairline_stroke_on_icon_is_an_error(tmp_path):
    body = GOOD_ICON.replace('stroke-width="8"', 'stroke-width="1"')
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("below the floor" in e for e in rep.errors)


def test_lockup_is_not_judged_at_favicon_size(tmp_path):
    """A 220-unit-wide lock-up with a 6-unit stroke is fine; it is never 16px wide."""
    body = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 64" role="img" '
        'aria-label="X"><title>X</title>'
        '<circle cx="32" cy="32" r="24" fill="none" stroke="#000" stroke-width="6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    rep = check(write(tmp_path, "horizontal-color.svg", body))
    assert rep.errors == []


def test_wide_aspect_falls_back_to_lockup_treatment(tmp_path):
    """Unknown filename, but a 4:1 aspect ratio implies a lock-up."""
    body = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 60" role="img" '
        'aria-label="X"><title>X</title>'
        '<path d="M10 30 L230 30" fill="none" stroke="#000" stroke-width="6" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    rep = check(write(tmp_path, "mystery.svg", body))
    assert rep.errors == []


@pytest.mark.parametrize(
    "stem,expected",
    [("icon-color", 16), ("favicon", 16), ("wordmark-black", 120),
     ("horizontal-color", 120), ("stacked-white", 120)],
)
def test_min_render_width_by_filename(tmp_path, stem, expected):
    px, _ = V.min_render_width(Path(f"{stem}.svg"), (0, 0, 64, 64), 16, 120)
    assert px == expected


# --- warnings ----------------------------------------------------------------

def test_fixed_dimensions_warn(tmp_path):
    body = GOOD_ICON.replace("<svg ", '<svg width="64" height="64" ')
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("fixed width/height" in w for w in rep.warnings)


def test_missing_title_warns(tmp_path):
    body = GOOD_ICON.replace("<title>X</title>", "").replace(' aria-label="X"', "")
    rep = check(write(tmp_path, "icon-color.svg", body))
    assert any("aria-label" in w for w in rep.warnings)


def test_offcolour_single_colour_variant_warns(tmp_path):
    """A file named -black should be pure #000000, not a near-black."""
    body = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" '
        'aria-label="X"><title>X</title>'
        '<path d="M8 8 L56 8 L56 56 L8 56Z" fill="#336699"/></svg>'
    )
    rep = check(write(tmp_path, "icon-black.svg", body))
    assert any("pure #000000" in w for w in rep.warnings)


def test_pure_black_variant_does_not_warn(tmp_path):
    body = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" '
        'aria-label="X"><title>X</title>'
        '<path d="M8 8 L56 8 L56 56 L8 56Z" fill="#000000"/></svg>'
    )
    rep = check(write(tmp_path, "icon-black.svg", body))
    assert rep.errors == [] and rep.warnings == []


# --- CLI contract ------------------------------------------------------------

def test_cli_exit_zero_on_clean_demo():
    r = subprocess.run([sys.executable, str(SCRIPT), str(DEMO)],
                       capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stdout + r.stderr


def test_cli_exit_one_on_error(tmp_path):
    write(tmp_path, "icon-color.svg", "<svg></svg>")
    r = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)],
                       capture_output=True, text=True, check=False)
    assert r.returncode == 1


def test_cli_exit_two_on_missing_path(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path / "nope")],
                       capture_output=True, text=True, check=False)
    assert r.returncode == 2


def test_cli_output_is_ascii_safe():
    """Messages must not mojibake on a cp1252 Windows console."""
    r = subprocess.run([sys.executable, str(SCRIPT), str(DEMO)],
                       capture_output=True, text=True, check=False)
    assert all(ord(c) < 128 for c in r.stdout)
