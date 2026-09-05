#!/usr/bin/env python3
"""Local mirror of the CI plugin-manifest job.

Validates that plugin.json, marketplace.json, and the skill's frontmatter agree
with each other and with what Claude Code needs to install this repo. Reports
every problem found, not just the first, then exits non-zero if there were any.

Run it before opening a pull request:

    python3 check_manifests.py
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SKILL_MD = ROOT / "skills/logo-creation/SKILL.md"


def check_manifests(problems: list[str]) -> None:
    """plugin.json and marketplace.json exist, are valid, and do not drift."""
    mkt = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    plug = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())

    for key in ("name", "owner", "plugins"):
        if key not in mkt:
            problems.append(f"marketplace.json missing required field: {key}")
    if "name" not in mkt.get("owner", {}):
        problems.append("marketplace.json owner missing required field: name")

    entries = [p for p in mkt.get("plugins", []) if p.get("name") == plug["name"]]
    if not entries:
        problems.append(f"marketplace.json lists no entry named {plug['name']!r}")
        return

    entry = entries[0]
    if "source" not in entry:
        problems.append("marketplace plugin entry missing required field: source")
    elif isinstance(entry["source"], str) and not (ROOT / entry["source"]).exists():
        problems.append(f"marketplace source path does not exist: {entry['source']}")

    # Claude Code only offers users an update when this field changes, so a
    # mismatch means a release silently never reaches anyone.
    if entry.get("version") != plug["version"]:
        problems.append(
            f"version drift: marketplace.json says {entry.get('version')!r}, "
            f"plugin.json says {plug['version']!r}"
        )


def check_frontmatter(problems: list[str]) -> None:
    """SKILL.md carries the frontmatter every skill loader requires."""
    text = SKILL_MD.read_text(encoding="utf-8")
    if not text.startswith("---"):
        problems.append("SKILL.md missing YAML frontmatter")
        return
    frontmatter = text[3 : text.index("---", 3)]
    for key in ("name:", "description:"):
        if key not in frontmatter:
            problems.append(f"SKILL.md frontmatter missing {key}")


def main() -> int:
    problems: list[str] = []
    check_manifests(problems)
    check_frontmatter(problems)

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1

    plug = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    print(f"PASS: {plug['name']} {plug['version']} — manifests agree, frontmatter ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
