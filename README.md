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

```bash
claude plugin add <this-repo>
```

Or copy `skills/logo-creation/` into your project's `.claude/skills/` or your
global Claude Code skills directory.

## Requirements

- Python 3.9+ (standard library only — no pip installs needed for the scripts)
- One SVG-to-PNG renderer for the export step: `resvg`
  (`npm install -g @aspect-build/resvg`), Inkscape (`brew install inkscape`),
  or librsvg (`brew install librsvg`)

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
