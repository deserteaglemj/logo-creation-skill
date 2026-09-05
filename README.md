# Logo Creation Skill

A Claude Code skill that designs complete logo identity systems from strategy
to client handoff — with fast, parallel concept generation.

This is a merge of two independent open-source projects, combined to keep the
best of both: a rigorous strategy-and-validation pipeline, plus a fast
parallel-exploration workflow.

## What it does

1. **Strategy** — a real brand brief (one sentence, one emotion, one audience)
   before any pixel is drawn.
2. **Differentiation** — researches the category, writes an explicit "avoid
   list" of visual clichés so the output doesn't look like every other
   AI-generated logo.
3. **Direction** — generates 3-5 *distinct* concept routes **in parallel**
   (literal, abstract, typographic), not sequentially.
4. **Construction** — builds the chosen mark as clean, hand-authored SVG.
5. **System** — the full variant matrix: icon, wordmark, horizontal and
   stacked lock-ups, each in color/black/white/dark-mode.
6. **Validation** — an automated structural validator (`scripts/validate_svg.py`)
   plus four mandatory perceptual tests: 16-pixel favicon legibility,
   grayscale/black-white, blur, and 5-second recall.
7. **Presentation** — a self-contained HTML contact sheet that renders every
   test live via CSS, plus campaign mockups (business card, app icon,
   signage, billboard).
8. **Refine** — an iteration loop, single-tweak or parallel batch variations.
9. **Handoff** — a packaged `brand.zip` (`scripts/package_brand.py`) with a
   generated README, favicon.ico, and every file a client needs — and nothing
   they don't.

## Why this exists

Two solid projects covered different halves of the problem:

- **[jim788e/logo-creation-skill](https://github.com/jim788e/logo-creation-skill)**
  had the rigor — strategy gates, an automated SVG validator that actually
  catches favicon-vanishing hairlines and embedded rasters, four honest
  perceptual tests, and a packager that refuses to ship an incomplete file set.
  It designed one concept at a time, sequentially.
- **[neonwatty/logo-designer-skill](https://github.com/neonwatty/logo-designer-skill)**
  had the speed — dispatching parallel subagents to sketch several distinct
  concepts at once instead of one after another, plus a working SVG-to-PNG
  export script.

This skill keeps jim788e's full pipeline and validation discipline, and folds
in neonwatty's parallel-generation pattern for Phase 3 (and 8's batch mode),
so exploring five real directions costs about the same wall-clock time as
exploring one.

Full attribution, including exactly which files came from which project, is
in [`NOTICE.md`](NOTICE.md).

## Install

### As a Claude Code plugin (recommended)

This repository is both a plugin and a single-plugin marketplace. From inside
Claude Code:

```
/plugin marketplace add deserteaglemj/logo-creation-skill
/plugin install logo-creation-skill@logo-creation
```

If the install summary says `Run /reload-plugins to activate.`, run that.
Then invoke it as `/logo-creation-skill:logo-creation`, or just ask for a logo
and the skill triggers on its own.

To pick up a new release later:

```
/plugin marketplace update logo-creation
```

### By hand (any agent harness)

Copy the skill directory into wherever your agent reads skills from:

```bash
git clone https://github.com/deserteaglemj/logo-creation-skill.git
cp -R logo-creation-skill/skills/logo-creation ~/.claude/skills/
# Hermes:  cp -R logo-creation-skill/skills/logo-creation ~/.hermes/skills/
```

The skill is self-contained: `SKILL.md`, `references/`, `scripts/`, and
`examples/` all live under that one directory, with no paths pointing outside
it.

## Requirements

- **Python 3.10+**, standard library only. No pip install needed to run the
  scripts. (3.10 is the floor because the code uses PEP 604 `X | Y` type
  syntax; CI tests 3.10, 3.12, and 3.13 on Linux, macOS, and Windows.)
- **One SVG-to-PNG renderer**, needed only for the Phase 9 raster export:
  librsvg (`brew install librsvg` / `apt-get install librsvg2-bin`),
  Inkscape (`brew install inkscape`), or resvg
  (`cargo install resvg`). `scripts/export.sh` detects whichever is present
  and tells you what to install if none is.

Everything before Phase 9 — strategy, concepts, construction, the full variant
matrix, the validator, and the contact sheet — runs with Python alone.

## Usage

Just ask:

- "Design a logo for [brand]"
- "Create a brand identity for my startup"
- "Critique this logo: path/to/logo.svg"

The skill will interview you for a brand brief, then generate several
distinct directions in parallel for you to choose from.

## License

MIT. See [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md) for the original
project licenses this work incorporates.
