# Notice

This project is a merge and adaptation of two independent, MIT-licensed
open-source projects. Both are credited below, with the specific files and
concepts each contributed.

## jim788e/logo-creation-skill

Source: https://github.com/jim788e/logo-creation-skill
License: MIT (see `LICENSE-jim788e.txt`)
Copyright (c) 2026 Dimitrios Misios

Contributed to this project:

- The overall 8-phase (here, 9-phase) pipeline structure: strategy brief,
  competitive differentiation, direction, construction, system, validation,
  presentation, handoff.
- `skills/logo-creation/scripts/validate_svg.py` — the structural SVG
  validator.
- `skills/logo-creation/scripts/build_contact_sheet.py` — the HTML contact
  sheet generator with live CSS-based perceptual tests.
- `skills/logo-creation/scripts/package_brand.py` — the client archive
  packager.
- `skills/logo-creation/references/*.md` — strategy brief, design execution,
  SVG craft, deliverables, validation, campaign presentation, and handoff
  reference documents.
- `skills/logo-creation/examples/demo/` — the worked example brand system.

## neonwatty/logo-designer-skill

Source: https://github.com/neonwatty/logo-designer-skill
License: MIT (see `LICENSE-neonwatty.txt`)
Copyright (c) 2026 Jeremy Watt

Contributed to this project:

- The parallel-subagent concept generation pattern: dispatching multiple
  `Task` agents concurrently, each producing one distinct SVG concept, rather
  than generating concepts sequentially. Folded into Phase 3 (Direction) and
  Phase 8 (Refine, batch mode) of this skill's pipeline.
- `skills/logo-creation/scripts/export.sh` — the SVG-to-PNG export script
  (auto-detects resvg / Inkscape / librsvg).
- The logo preview HTML template pattern (side-by-side concept cards).

## What changed in this merge

- The pipeline spine, validation discipline, and file/directory conventions
  are jim788e's, unmodified in substance.
- Phase 3 (previously sequential concept generation in jim788e's version) now
  explicitly uses neonwatty's parallel-dispatch pattern.
- Phase 8 (Refine) gained neonwatty's single-vs-batch iteration distinction.
- Phase 9 (Handoff) gained neonwatty's `export.sh` as the concrete rasterizer
  invoked before packaging, since jim788e's packager assumes rasters already
  exist but doesn't produce them itself.
- SKILL.md is a new document combining both, not a copy of either original.

Both original projects remain independently available at the URLs above under
their own MIT licenses.
