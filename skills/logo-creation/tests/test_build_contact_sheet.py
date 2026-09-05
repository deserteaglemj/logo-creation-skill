"""Tests for scripts/build_contact_sheet.py."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_contact_sheet.py"
DEMO = ROOT / "examples" / "demo"

sys.path.insert(0, str(ROOT / "scripts"))
import build_contact_sheet as B

# --- clean_svg ---------------------------------------------------------------

def test_root_dimensions_stripped_inner_geometry_preserved():
    """Regression: stripping width/height globally used to gut inner <rect>."""
    src = ('<svg xmlns="http://www.w3.org/2000/svg" width="220" height="64" '
           'viewBox="0 0 220 64"><rect x="1" y="2" width="130" height="12"/></svg>')
    out = B.clean_svg(src, "m0")
    assert 'width="130"' in out and 'height="12"' in out
    assert 'width="220"' not in out and 'height="64"' not in out
    assert out.startswith('<svg class="mark"')


def test_ids_are_namespaced_per_instance():
    """The same file is inlined many times; ids must not collide."""
    src = ('<svg viewBox="0 0 10 10"><linearGradient id="g"/>'
           '<path fill="url(#g)" d="M0 0"/></svg>')
    out = B.clean_svg(src, "m7")
    assert 'id="m7-g"' in out and "url(#m7-g)" in out
    assert 'id="g"' not in out


def test_xml_preamble_and_comments_removed():
    src = ('<?xml version="1.0"?><!-- note --><svg viewBox="0 0 10 10">'
           '<path d="M0 0"/></svg>')
    out = B.clean_svg(src, "m1")
    assert "<?xml" not in out and "<!--" not in out


def test_svg_without_root_dimensions_is_untouched_otherwise():
    src = '<svg viewBox="0 0 64 64"><circle cx="1" cy="2" r="3"/></svg>'
    out = B.clean_svg(src, "m2")
    assert 'r="3"' in out and 'viewBox="0 0 64 64"' in out


# --- sorting -----------------------------------------------------------------

def test_variants_sort_by_component_then_variant():
    names = ["stacked-black.svg", "icon-white.svg", "favicon.svg",
             "icon-color.svg", "wordmark-color.svg"]
    ordered = [p.name for p in sorted((Path(n) for n in names), key=B.sort_key)]
    assert ordered[0] == "favicon.svg"
    assert ordered.index("icon-color.svg") < ordered.index("icon-white.svg")
    assert ordered.index("wordmark-color.svg") < ordered.index("stacked-black.svg")


# --- generated document ------------------------------------------------------

def _build() -> str:
    files = sorted(DEMO.glob("*.svg"), key=B.sort_key)
    return B.build(files, "Demo Brand")


def test_all_placeholders_filled():
    body = re.sub(r"<style>.*?</style>", "", _build(), flags=re.S)
    body = re.sub(r"<script>.*?</script>", "", body, flags=re.S)
    assert "{" not in body and "}" not in body


def test_contains_all_four_tests_and_the_gallery():
    html = _build()
    for marker in ("Variant gallery", "Test 1", "Test 2", "Test 3", "Test 4",
                   "Scale ramp", "Show for 5 seconds"):
        assert marker in html, marker


def test_brand_name_is_escaped():
    files = sorted(DEMO.glob("*.svg"), key=B.sort_key)
    html = B.build(files, '<script>x</script>')
    assert "<script>x</script>" not in html.split("<script>")[0]
    assert "&lt;script&gt;" in html


def test_filters_target_the_mark_not_the_tile():
    """Regression: filtering the tile transformed its background too, turning
    the 'pure black' test into a solid black rectangle."""
    html = _build()
    assert ".fx-black .mark" in html
    assert re.search(r"\.fx-black\s*\{", html) is None


def test_is_self_contained():
    """No network fetches. The SVG xmlns is a namespace URI, not a request, so
    it is excluded rather than matched blindly."""
    html = _build()
    stripped = html.replace('xmlns="http://www.w3.org/2000/svg"', "")
    stripped = stripped.replace('xmlns:xlink="http://www.w3.org/1999/xlink"', "")
    for bad in ('src="http', 'href="http', 'src="//', 'href="//',
                "<link", "@import", "url(http"):
        assert bad not in stripped, bad


def test_favicon_strip_includes_16px():
    assert "width:16px;height:16px" in _build().replace(" ", "")


# --- CLI ---------------------------------------------------------------------

def test_cli_writes_sheet(tmp_path):
    out = tmp_path / "sheet.html"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(DEMO), "--name", "Demo", "--out", str(out)],
        capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    assert out.exists() and out.stat().st_size > 2000


def test_cli_rejects_non_directory(tmp_path):
    f = tmp_path / "a.svg"
    f.write_text("<svg/>", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPT), str(f)],
                       capture_output=True, text=True, check=False)
    assert r.returncode == 2


def test_cli_rejects_empty_directory(tmp_path):
    r = subprocess.run([sys.executable, str(SCRIPT), str(tmp_path)],
                       capture_output=True, text=True, check=False)
    assert r.returncode == 2
