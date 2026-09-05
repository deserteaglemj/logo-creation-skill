"""Tests for scripts/check_connectivity.py.

The tool answers one question: do a mark's parts actually touch? Each case pairs
a fixture whose answer is known by construction with the count it must report.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_connectivity.py"
DEMO = ROOT / "examples" / "demo"

sys.path.insert(0, str(ROOT / "scripts"))
import check_connectivity as C

pytestmark = pytest.mark.skipif(
    not shutil.which("rsvg-convert") or not shutil.which("sips"),
    reason="needs rsvg-convert and sips",
)

HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
        'role="img" aria-label="t"><title>t</title>')


def write(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(HEAD + body + "</svg>", encoding="utf-8")
    return p


def run(svg: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), str(svg), *args],
                          capture_output=True, text=True, check=False)


def test_two_separated_squares_report_two_components(tmp_path):
    svg = write(tmp_path, "two.svg",
                '<rect x="8" y="8" width="16" height="16" fill="#000"/>'
                '<rect x="40" y="40" width="16" height="16" fill="#000"/>')
    res = run(svg)
    assert res.returncode == 1
    assert "2 component(s)" in res.stdout


def test_touching_squares_report_one_component(tmp_path):
    # Deliberately overlapping by a unit so they are unambiguously joined.
    svg = write(tmp_path, "joined.svg",
                '<rect x="8" y="8" width="20" height="16" fill="#000"/>'
                '<rect x="27" y="8" width="20" height="16" fill="#000"/>')
    res = run(svg)
    assert res.returncode == 0
    assert "1 component(s)" in res.stdout


def test_expect_flag_accepts_a_known_multi_part_mark(tmp_path):
    """A mark can legitimately be several pieces; --expect makes that explicit."""
    svg = write(tmp_path, "three.svg",
                '<rect x="6" y="6" width="12" height="12" fill="#000"/>'
                '<rect x="26" y="26" width="12" height="12" fill="#000"/>'
                '<rect x="46" y="46" width="12" height="12" fill="#000"/>')
    assert run(svg, "--expect", "3").returncode == 0
    assert run(svg, "--expect", "1").returncode == 1


def test_bundled_demo_icon_is_one_component():
    res = run(DEMO / "icon-color.svg")
    assert res.returncode == 0, res.stdout
    assert "1 component(s)" in res.stdout


def test_sizes_flag_reports_every_requested_size(tmp_path):
    svg = write(tmp_path, "one.svg",
                '<rect x="8" y="8" width="40" height="40" fill="#000"/>')
    res = run(svg, "--sizes", "16", "128")
    assert "16px" in res.stdout
    assert "128px" in res.stdout
    assert res.returncode == 0


def test_components_helper_ignores_nothing_when_all_ink(tmp_path):
    rows = [[0] * 10 for _ in range(10)]
    assert C.components(rows) == [100]


def test_components_helper_counts_disjoint_regions():
    rows = [[255] * 10 for _ in range(10)]
    for y in (1, 2):
        for x in (1, 2):
            rows[y][x] = 0
    for y in (7, 8):
        for x in (7, 8):
            rows[y][x] = 0
    assert C.components(rows) == [4, 4]


def test_antialias_specks_are_ignored_at_small_sizes(tmp_path):
    """A hairline that survives only as stray pixels must not count as a part."""
    svg = write(tmp_path, "speck.svg",
                '<rect x="8" y="8" width="40" height="40" fill="#000"/>'
                '<rect x="60" y="60" width="1" height="1" fill="#000"/>')
    res = run(svg, "--sizes", "16")
    assert res.returncode == 0, res.stdout
