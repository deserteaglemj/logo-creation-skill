# Phase 4 — SVG Construction

The SVG is the source of truth for the whole identity. Build it with the same
discipline a designer would apply in a vector editor.

---

## Structure conventions

The validator (`scripts/validate_svg.py`) enforces these.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Brand name">
  <title>Brand name</title>
  <path d="…" fill="currentColor"/>
</svg>
```

- **`viewBox` is mandatory.** Omit `width`/`height` on the master files so the
  mark scales to its container. Fixed dimensions belong to exported PNGs, not to
  the vector source.
- **Choose a round coordinate space.** 64×64 for icons, 24-unit grid for
  ultra-simple marks. Round numbers make optical corrections easy to reason about
  and keep path data short.
- **`fill="currentColor"` on monochrome variants** so a single file inherits the
  surrounding text colour. Explicit hex only on the full-colour variants.
- **No `<text>` in final files.** Convert every glyph to paths. Text renders
  differently on every machine that lacks the font.
- **No `<image>`, no external `href`, no `<script>`, no embedded base64 rasters.**
  A logo containing a bitmap is not a logo.
- **No `filter`, no `mask` in the icon.** Filters do not survive print pipelines,
  favicon rasterisation, or embroidery.
- Include `<title>` and `role="img"` with `aria-label` for accessibility.
- Strip editor metadata, comments, and empty groups. Round coordinates to at most
  two decimals.

## Construction discipline

**Work on a grid.** Pick one construction system and hold to it — a circle grid,
a 45°/90° system, a modular unit derived from the stroke weight. Every terminal,
join, and centre should land on the system. This is what separates a mark that
feels designed from one that feels drawn.

**Path economy.** Fewer anchor points, placed at extremes (top, bottom, left,
right of each curve) with horizontal or vertical handles. A circle needs four
points, not twelve. Excess points produce lumpy curves that only become visible
when the mark is enlarged to signage size.

**Convert strokes to fills for the final icon.** A `stroke-width` scales
non-linearly against some rendering paths and cannot be non-uniformly
transformed. Outline the strokes so the shape is defined by geometry alone. If a
stroke is retained for a monoline mark, set `stroke-linecap` and
`stroke-linejoin` explicitly and never rely on the default.

**Stroke weight and the favicon floor.** At 16px, a stroke thinner than
`viewBox_width / 16` renders below one pixel and disappears. On a 64-unit grid
that means a hard floor of 4 units. Treat 5–6 units as the comfortable range for
a monoline mark. The validator flags anything under the floor.

**Counter-space must survive rasterisation.** Gaps and enclosed holes need at
least the same clearance as the stroke weight. A counter narrower than the stroke
fills in and turns the mark into a blob at small sizes. This is the single most
common cause of 16-pixel failure.

## Optical corrections

Mathematically correct is visually wrong. Apply these by eye:

- **Overshoot.** Round and pointed forms must extend slightly past the flat
  boundary they align to — roughly 1–1.5% of the height — or they read as small.
- **Horizontal/vertical weight compensation.** A horizontal stroke of the same
  measured width as a vertical one appears heavier. Thin horizontals by around
  3–5%.
- **Optical centring.** The visual centre sits slightly above the geometric
  centre. Marks centred mathematically look like they are sinking. This matters
  most for a symbol inside a circle or rounded square — the app-icon case.
- **Joint thinning.** Where two strokes meet at an acute angle, ink pools. Thin
  the stroke slightly into the join to keep the weight even.
- **Apex and vertex correction.** Sharp points read heavier than flats; blunt or
  slightly narrow them.

## Building the two components

Build the **symbol** and the **wordmark** as separate files, then compose the
lock-ups from them. Never draw a lock-up as a single monolithic path — the
components have to be reusable independently.

**The symbol** carries the identity test: cover the wordmark, and the symbol must
still be recognisable, memorable, and unique to this brand. If it is anonymous
under that cover, the design has failed and Phase 3 must be revisited. This test
is not negotiable and not something to talk your way past.

**The wordmark** is drawn, not typed. Set it, outline it, then correct the
kerning optically, adjust one or two letterforms to carry a proprietary detail,
and check it at its smallest intended size.

## Lock-ups

Compose the horizontal and stacked lock-ups from the two components with
relationships defined in units of the symbol height (call it `x`):

- Horizontal: symbol, gap of `0.5x`, wordmark. Cap height of the wordmark aligns
  optically with the symbol — usually meaning the wordmark is slightly shorter
  than the symbol, not equal to it.
- Stacked: symbol centred above wordmark, gap of `0.4x`. Centre optically on the
  wordmark's visual mass, not its bounding box — trailing punctuation and
  asymmetric letterforms will pull a bounding-box centre off.

Define **clear space** as a fixed fraction of the symbol height (`0.5x` is a
common, defensible choice) and state it in the deliverables.

## Before moving to Phase 5

Run the validator, then look at the mark at 16px in the contact sheet. Do not
proceed on the strength of how it looks at full size — that is the failure mode
this entire skill exists to prevent.
