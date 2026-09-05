---
name: logo-creation
description: |
  Design a complete logo identity system from strategy to client handoff, with
  fast parallel concept generation. Runs a 9-phase pipeline — brand brief,
  competitive differentiation, 3-5 parallel concept routes, symbol and
  typography construction, full variant set (icon, wordmark, stacked,
  horizontal, mono, inverted), the four validation tests (16-pixel, grayscale,
  blur, 5-second recall), campaign presentation, refinement, and a packaged
  brand.zip ready to send. Use when the user says logo, logomark, wordmark,
  brand mark, brand identity, visual identity, icon design, favicon, rebrand,
  logo system, brand guidelines, or asks to design/critique/refine a logo.
argument-hint: "<brand name> — or 'critique <path-to-svg>'"
user-invocable: true
license: MIT
metadata:
  version: "2.0.0"
  category: design
---

# Logo Creation

Design logos that survive contact with the real world: a 16px favicon, a grayscale
fax, a blurred glance from a moving car, a billboard. Most logo output fails not
because it is ugly but because it was never tested. This skill makes the tests
mandatory and the strategy explicit — and generates concept routes in parallel
so exploration doesn't cost a full session.

This skill is a merge of two independent MIT-licensed projects:

- **[jim788e/logo-creation-skill](https://github.com/jim788e/logo-creation-skill)**
  — the strategy-first pipeline, automated SVG validator, four perceptual tests,
  full variant matrix, and client packaging. Supplies Phases 1-2 and 4-9 below.
- **[neonwatty/logo-designer-skill](https://github.com/neonwatty/logo-designer-skill)**
  — the parallel-subagent concept generation pattern and the SVG-to-PNG export
  script (`scripts/export.sh`). Supplies the parallel-generation approach folded
  into Phase 3, and the rasterizer used in Phase 9.

See `NOTICE.md` for full attribution and both original licenses.

## Non-negotiables

Read these before anything else. They override taste, trend, and user enthusiasm.

1. **Strategy precedes pixels.** No mark is drawn before the brief in Phase 1 is
   written and confirmed. A logo that cannot state what it means is decoration.
2. **The icon must pass at 16 pixels.** If the symbol is unreadable as a favicon,
   it is not finished, regardless of how good it looks at 512px.
3. **The mark must work in pure black and pure white.** Colour is the last layer
   added, never the thing holding the design together.
4. **Vector only.** Output is hand-authored SVG with a `viewBox`, no embedded
   rasters, no `<text>` elements in final deliverables, no external references.
5. **No unearned complexity.** Every gradient, every extra path, every third
   colour must justify itself against the 16-pixel and blur tests or be removed.

## The pipeline

Nine phases. Do not skip forward. Each phase has a gate — a question that must be
answerable before moving on.

| Phase | Output | Gate |
| :-- | :-- | :-- |
| 1. Strategy | Brand brief | Can you state the brand in one sentence and one emotion? |
| 2. Differentiation | Competitive map | Do you know what everyone else in the category looks like — and what to avoid? |
| 3. Direction (parallel) | 3-5 concept routes, generated concurrently | Does each route express a *different* strategic idea, not a different decoration? |
| 4. Construction | The mark, in SVG | Does the symbol read without the wordmark? |
| 5. System | Full variant set | Does every layout and colour context have a file? |
| 6. Validation | Test report | Did it pass all four tests, honestly scored? |
| 7. Presentation | Campaign contact sheet | Would this survive a client review? |
| 8. Refine | Iterated SVGs | Did the change move a named test or brief goal, not just taste? |
| 9. Handoff | `brand.zip` | Could the client use every file without asking you a question? |

---

### Phase 1 — Strategy

Load `references/strategy-brief.md` and work through it with the user. Ask the
questions with `AskUserQuestion`, batched together; do not invent the answers.
If the user cannot or will not answer, state your assumptions explicitly in the
brief and continue — but write them down as assumptions, not facts.

The brief must end with three fixed decisions:
- **One sentence** describing the brand.
- **One primary emotion** the mark must evoke (Trust / Innovation / Play / Luxury / Craft / Speed / Care — pick one, not three).
- **One audience** the mark speaks to.

Gate: those three lines exist and the user has seen them.

### Phase 2 — Differentiation

Research the category before designing. Use web search to find the leading brands
in the industry and describe their marks concretely — shape language, colour,
type classification.

Then write the **avoid list**: the visual clichés this category is drowning in.
This is where the "generic AI logo" problem gets solved — not by prompting harder,
but by naming the tropes and refusing them. See the standing tropes list in
`references/design-execution.md`.

Gate: you can name at least three things this logo will deliberately *not* do.

### Phase 3 — Direction (parallel generation)

Produce **3-5 routes**, each a distinct strategic idea — not minor variations of
one idea:

- Route A — the literal/representational read
- Route B — the abstract/geometric read
- Route C — the typographic read (letterform, monogram, negative space)
- (optional D/E if the brief supports more angles)

**Generate all routes in parallel**, not sequentially. Dispatch one `Task`
subagent per route, all in the same message so they run concurrently. Each
agent should:

- Receive the full brand brief (Phase 1), the avoid list (Phase 2), and the
  full SVG Conventions below
- Be assigned one specific route and its rationale
- Write its SVG to a specific file path (`logos/concepts/concept-N.svg`)
- Use `subagent_type: "general-purpose"`

Agents do not share context — give each one everything it needs, inline, not
by reference to a file it can't read.

After all agents complete:

1. Generate `logos/preview.html` (template below)
2. Describe each concept in one line so the user can match descriptions to visuals
3. Ask: "Which direction do you want to explore? Pick a number, or describe what
   you like/dislike across them." A hybrid answer becomes a new route — sketch
   it and re-present rather than guessing which parts to merge.

Gate: the user picks one route (or an explicit hybrid, re-presented and confirmed).

#### Known-symbol collision check (mandatory before presenting any route)

A route can pass every structural rule and still be unusable, because it reads as
an existing symbol before it reads as the brand. Measured on a real run: of four
parallel routes, three were structurally clean and all three collided — a stack
of eight bars read as a hamburger menu, eight modules in a frame read as a dice
face, eight radial punches read as a loading spinner.

Run the detector on every concept:

```bash
python scripts/detect_symbol_collision.py logos/concepts/
```

It measures the geometric signatures that cause those readings — four-fold
rotational self-similarity, regular parallel bars, and blobs on a lattice — and
exits non-zero on a collision. Thresholds are calibrated so a known-good mark
still passes, so a flag means redesign, not tuning.

Two arrangements cause most collisions and should never be the default when the
brief supplies a count ("eight clients", "three pillars"):

- **radial around a centre point** → spinner, compass rose, wheel, sunburst
- **parallel equal bars** → hamburger menu, barcode, signal bars

An asymmetric or nested arrangement is far safer, and asymmetry with a stated
reason is a strength. Put this list in each subagent's context up front: agents
given only the category-cliché avoid-list (barbells, flames, chevrons) still walk
straight into a spinner, because a spinner is not a fitness cliché.

**The detector is necessary, not sufficient.** It cannot see semantic or
anatomical readings. Measured across two rounds of four parallel routes each —
eight routes, zero shippable — adding the full collision list to every prompt
eliminated geometric collisions entirely and did not prevent failure, it moved
it. All four second-round routes were geometrically clean and still unshippable:
one read as a plus sign, one as Pac-Man, one as a file icon, and two read
anatomically.

Anatomical reading in particular is **not** detectable by pixel geometry. The
recurring shape in both anatomical rejections was two round-capped vertical
strokes flanking a horizontal element, so that was measured directly; the
resulting detector was inverted, missing both marks it was built from while
false-positiving a known-good mark of the same topology drawn in better
proportions. The distinguishing factor is proportion and spacing, not topology. A
check that passes bad work and rejects good work is worse than no check, so it
was not shipped.

**Therefore an independent read is a mandatory gate, not a nicety.** Render every
candidate and get a description of what it actually reads as, from something that
did not design it. A pass from the automated detector means "worth a human look",
never "approved".

**Terminal shape is a suspect, not a rule.** All anatomical rejections across both
rounds used `stroke-linecap="round"`, which suggests round caps read as organic
bulbs. Tested directly on the shipped mark by switching it to square caps: it
reviewed *worse*, picking up a "stylized pelvis, somewhat unsettling" reading that
the round-cap original never drew. The correlation did not survive contact with a
single controlled test, so treat terminal shape as one variable to try when a mark
reads organically, not as a rule to apply pre-emptively. Proportion and spacing
matter more than terminal geometry.

When every route collides, say so and keep the incumbent. Never present a
colliding mark because it was expensive to generate.

#### SVG Conventions (apply to every generated mark, every phase)

The validator (`scripts/validate_svg.py`) enforces these:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Brand name">
  <title>Brand name</title>
  <path d="…" fill="currentColor"/>
</svg>
```

- **`viewBox` is mandatory.** Omit `width`/`height` on the master files so the
  mark scales to its container. 64×64 for icons, wider for wordmarks/lock-ups.
- **`fill="currentColor"` on monochrome variants** so a single file inherits the
  surrounding text colour. Explicit hex only on the full-colour variants.
- **No `<text>` in final files.** Convert every glyph to paths.
- **No `<image>`, no external `href`, no `<script>`, no embedded base64 rasters.**
- **No `filter`, no `mask` in the icon.** These don't survive print, favicon
  rasterisation, or embroidery.
- Include `<title>` and `role="img"` with `aria-label`.
- Strip editor metadata, comments, and empty groups. Round coordinates to at
  most two decimals.
- **Small-size legibility is mandatory.** At 16px, a stroke thinner than
  `viewBox_width / 16` disappears. On a 64-unit grid that's a hard floor of 4
  units; 5-6 is comfortable. Counter-space needs at least the same clearance as
  the stroke weight, or it fills in — the single most common cause of 16px failure.
- **Prefer `stroke-linecap="butt"` for letterform marks.** Round caps read as
  organic bulbs rather than typographic terminals; every anatomical rejection
  across two rounds of concept generation used round caps. Use round caps
  deliberately, for a specific reason, not as the default. **But do not apply this
  blind:** switching the shipped mark from round to square caps made its review
  worse, not better. Terminal shape is a variable to test, not a rule to assume.

For deeper construction discipline (grid systems, path economy, optical
corrections, kerning, lock-up composition), read `references/svg-craft.md`
before Phase 4.

### Preview HTML template (Phase 3 and Phase 8)

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Logo Preview — {{PHASE}}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 2rem; }
  body.light { background: #f5f5f5; color: #333; }
  body.dark { background: #1a1a1a; color: #eee; }
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; }
  .card { border: 1px solid rgba(128,128,128,0.3); border-radius: 12px; overflow: hidden; }
  .card-img { display: flex; align-items: center; justify-content: center; padding: 2rem; min-height: 240px; }
  body.light .card-img { background: #fff; } body.dark .card-img { background: #2a2a2a; }
  .card-img img { max-width: 100%; max-height: 200px; }
  .card-label { padding: 0.75rem 1rem; font-size: 0.875rem; font-weight: 500; border-top: 1px solid rgba(128,128,128,0.3); }
</style>
</head>
<body class="light">
  <div class="header"><h1>Logo Preview — {{PHASE}}</h1></div>
  <div class="grid">{{CARDS}}</div>
</body>
</html>
```

Each `{{CARDS}}` entry: `<div class="card"><div class="card-img"><img src="{{PATH}}" alt="{{LABEL}}"></div><div class="card-label">{{LABEL}}</div></div>`

### Phase 4 — Construction

Build the chosen mark properly. `references/svg-craft.md` covers construction
discipline: grid and optical alignment, path economy, stroke-to-fill conversion,
counter-space, optical corrections, and the SVG structure conventions the
validator enforces.

Two components, built separately:
- **The symbol** — must be independently recognisable.
- **The wordmark** — letterforms drawn or set, then outlined to paths.

Gate: cover the wordmark. If the symbol alone is anonymous, return to Phase 3.

### Phase 5 — System

Generate the full deliverable set per `references/deliverables.md`: icon,
wordmark, horizontal lock-up, stacked lock-up, and for each — full colour, pure
black, pure white, dark-mode. Plus clear-space and minimum-size rules.

For batch variant generation across the matrix (not single tweaks), dispatch
parallel `Task` subagents the same way as Phase 3 — one per file, each given
the finished symbol/wordmark SVG content inline.

Naming and directory layout are specified in that reference. Follow it exactly;
the contact-sheet builder reads those filenames.

Gate: every file in the deliverables table exists on disk.

### Phase 6 — Validation

Run the validator on every SVG:

```bash
python scripts/validate_svg.py out/logo/
```

It checks structure, hairline strokes that vanish at favicon size, raster
embeds, live text, external references, and path complexity. Errors block; warnings
require a written justification.

Then run the four perceptual tests from `references/validation.md` — 16-pixel,
grayscale, blur, and 5-second recall — using the contact sheet from Phase 7. Score
each honestly. A failed test means returning to Phase 4, not lowering the bar.

Gate: zero validator errors, and all four perceptual tests passed with reasoning
recorded.

### Phase 7 — Presentation

```bash
python scripts/build_contact_sheet.py out/logo/ --name "Brand Name" --out out/logo/contact-sheet.html
```

This produces a self-contained HTML sheet: every variant, every test rendered
live via CSS (favicon strip at 16/24/32px, grayscale, blur, dark mode, inverted),
plus an interactive 5-second recall timer. Open it and actually look at it — the
tests are worthless unless a pair of eyes runs them.

For the campaign layer — business card, packaging, signage, app icon, billboard —
see `references/campaign-presentation.md`. Present the logo in use, not floating
on white.

### Phase 8 — Refine

Iterate on user feedback. For single specific feedback ("make the icon bigger",
"change the blue to green"), apply directly and write the next
`out/logo/iterations/iteration-N.svg` yourself. For batch exploration ("try
different colour palettes", "show me 5 variations"), use parallel `Task` agents
the same way as Phase 3, each given the full base SVG inline plus its specific
variation to apply.

Keep SVG structure (the same `<g>` ids) consistent across iterations so changes
are traceable. Regenerate the contact sheet after each round, most recent first.
If a request isn't traceable to a named test or the brief, say so and ask which
metric it's meant to move — taste alone isn't a stopping condition, but it also
isn't a reason to burn cycles without a target.

### Phase 9 — Handoff

The work is not finished when the files exist; it is finished when someone who
was not in the room can use them correctly. Package everything into one archive:

```bash
python scripts/package_brand.py out/logo/ --name "Brand Name" --exports out/exports/
```

Generate the raster and vector exports first. `scripts/export.sh` handles the
SVG-to-PNG conversion (auto-detects `resvg`, Inkscape, or `rsvg-convert`):

```bash
bash scripts/export.sh out/logo/icon-color.svg out/exports/
```

This routes the SVG masters, PNG rasters and print formats into the folders a
recipient expects, builds a multi-resolution `favicon.ico` from the small icon
PNGs, writes a plain-text `README.txt` answering *which file do I use for this*,
and **refuses to build if the Phase 5 matrix has holes** — a missing variant is
a case someone downstream will improvise badly.

See `references/handoff.md` for the archive layout, what belongs in it, and what
deliberately does not.

Gate: the archive builds without `--force`, and every folder in it is one a
non-designer can act on.

---

## Critique mode

When invoked as `critique <path>` or when the user brings an existing logo, skip
Phases 3–5. Run Phase 1 in reverse (infer the strategy the mark currently
communicates), run the validator and all four tests, then report:

- What the mark currently says vs. what the brand needs it to say
- Test-by-test pass/fail with the specific failure mode
- The smallest set of changes that fixes the failures

Be direct about failures. A polite critique that lets a 16-pixel failure ship is
a bad critique.

## PNG export prerequisites

The export step needs one SVG-to-PNG renderer on `PATH`. In detection order:
`resvg` (`cargo install resvg`), `rsvg-convert` (`brew install librsvg` /
`apt-get install librsvg2-bin`), `inkscape` (`brew install inkscape`),
`magick` (ImageMagick), or Node with `sharp` installed. The script auto-detects
which is available and tells you plainly if none is found — it never fabricates
a successful export, and it never reaches the network to probe for one.

## Running the scripts from an installed copy

Every command in this file is written relative to the skill directory. When the
skill is installed rather than checked out, resolve that directory once and use
it:

```bash
# Claude Code plugin install
SKILL_DIR=~/.claude/plugins/*/skills/logo-creation
# manual copy
SKILL_DIR=~/.claude/skills/logo-creation
# Hermes
SKILL_DIR=~/.hermes/skills/creative/logo-creation

python3 "$SKILL_DIR/scripts/validate_svg.py" out/logo/
```

The scripts have no imports outside the standard library and read no files
outside the directory you point them at, so they run correctly from any
location.

## Reference files

| File | Load when |
| :-- | :-- |
| `references/strategy-brief.md` | Phase 1 — the brief template and questions |
| `references/design-execution.md` | Phases 2–3 — shape, colour, type, luxury cues, anti-cliché list |
| `references/svg-craft.md` | Phase 4 — construction discipline and SVG conventions |
| `references/deliverables.md` | Phase 5 — file matrix, naming, clear space |
| `references/validation.md` | Phase 6 — the four tests and how to score them |
| `references/campaign-presentation.md` | Phase 7 — mockups and client presentation |
| `references/handoff.md` | Phase 9 — the client archive: layout, contents, exclusions |

## Worked example

`examples/demo/` is a full worked demo — icon/wordmark/stacked/horizontal ×
color/black/white/darkmode, `BRAND.md`, `favicon.svg`. Use it to sanity-check
the validator and contact-sheet builder:

```bash
python scripts/validate_svg.py examples/demo/
python scripts/build_contact_sheet.py examples/demo/ --name "Demo Brand" --out /tmp/demo-contact-sheet.html
```

## Pitfalls

- Don't generate near-duplicate concepts in Phase 3 — each route must be a
  genuinely different strategic idea, not a decoration variant. Running them in
  parallel makes this cheap; don't waste the parallelism on near-duplicates.
- Don't expect a better prompt to fix a semantic failure. Measured over two
  rounds of four parallel routes: adding the full collision list eliminated
  geometric collisions and produced four geometrically clean routes that were all
  still unshippable on semantic grounds. Prompt improvements move the failure
  mode, they don't remove the need to look.
- Don't ship a detector you haven't calibrated against a known-good mark. An
  anatomical-reading detector built from two real failures turned out inverted —
  it missed both source marks and rejected the known-good demo. Always test a new
  check against something that must pass, not only against things that must fail.
- Don't fix a grayscale/blur failure by adjusting colour lightness — that hides
  the problem until the mark is engraved, faxed, embroidered, or printed in one
  colour. Fix the shape.
- Don't skip the favicon legibility check — thin details fine at 512px often
  vanish at 16-32px.
- Don't present three finished options at Phase 7 — that decision belonged to
  Phase 3; presenting three finished identities pushes the choice onto taste and
  produces a committee compromise.
- Don't fabricate PNG export success if no SVG-to-PNG tool is found — report the
  missing tool and the install command.
- Don't ship editable source files, rejected routes, or unbriefed motion in the
  client handoff.
