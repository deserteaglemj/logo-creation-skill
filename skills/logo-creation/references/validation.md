# Phase 6 — Validation

Two layers: an automated structural check, and four perceptual tests that need
human eyes. Both are mandatory. Score honestly — the purpose of a test you can
fail is to fail it while there is still time to fix it.

---

## Layer 1 — Automated

```bash
python scripts/validate_svg.py out/logo/
```

Checks each SVG for: presence of `viewBox`; embedded rasters; external
references; `<script>`; live `<text>`; filters and masks; hairline strokes; path
complexity; and file size.

The stroke floor is measured against the smallest width each component is
actually deployed at — 16px for an icon or favicon, 120px for a wordmark or
lock-up, which is never rendered at favicon width. Component type is read from
the filename, so the naming convention in `deliverables.md` matters. Override
with `--icon-size` and `--lockup-size`.

**Errors block.** **Warnings require a written justification** — a warning is a
statement that something unusual is happening, and the answer "it's fine" is not
a justification.

## Layer 2 — The four perceptual tests

Run these against the contact sheet from Phase 7, which renders all four live.

### 1. The 16-pixel test

Render the icon at 16px. Is it legible and recognisable?

The four failure modes:
- **Fill-in** — counters and gaps close up into a solid blob. Cause: counter
  space narrower than the stroke weight.
- **Vanishing** — thin elements disappear entirely. Cause: strokes below the
  `viewBox_width / 16` floor.
- **Mush** — adjacent elements merge into an unreadable mass. Cause: too many
  elements for the size.
- **Silhouette drift** — it is visible but reads as a *different shape* than the
  full-size mark. The most dangerous failure, because it passes a careless look.

Fix by simplifying the symbol, not by enlarging the test.

### 2. The grayscale / black-and-white test

Render in grayscale, then in pure black and pure white. Do all forms remain
separate and the shape remain complete?

If elements merge, tonal contrast was carrying structural work that shape should
have been doing. Fix the shape. Do not fix it by adjusting colour lightness —
that only hides the problem until the mark is engraved, faxed, embroidered, or
printed in one colour.

### 3. The blur test

Apply a blur (roughly 3px at 128px render size — the contact sheet does this
live). The core shape must remain recognisable.

Blur strips detail and leaves silhouette and mass distribution — which is close
to what peripheral vision and distance actually deliver. A mark that dissolves
under blur is a mark nobody will recognise from across a room or at motorway
speed. Passing means the *overall form* is still identifiable, not that details
are still visible.

### 4. The 5-second recall test

Show the mark for five seconds, hide it, then describe it from memory. The
contact sheet has a timer button for this.

Ideally run it with someone who has not seen the mark. Failing that, be strict
with yourself. The test passes if the description captures the essential form —
"a circle with a notch cut from the upper right" — and fails if it is vague
("some kind of geometric shape") or if reconstruction requires detail that was
not retained.

This is the memorability test. Your brain stores shape and colour first, detail
last; a mark whose identity lives in its detail is a mark that is never recalled.

---

## The Golden Rules checklist

Confirm all four before signing off. These restate the tests as design
requirements.

| Principle | Requirement | Key check |
| :-- | :-- | :-- |
| **Simplicity** | Clean, free of excess detail. Minimalism removes clutter, not identity. | **Identity test:** with the brand name removed, is the mark still recognisable, memorable, and unique to this brand? |
| **Versatility** | Works across digital, print, dark mode, light mode, and motion. | **Adaptability check:** does it hold in a dark-mode UI? Can it be animated without losing its core identity? |
| **Memorability** | Simple shape and palette, instantly recallable. | **Shape focus:** does it work and feel complete as an unadorned silhouette? |
| **Scalability** | Retains clarity from favicon to billboard. | **16-pixel test:** is the simplest version legible at 16px? |

## Reporting

Report results in this form. No test is marked passed without a reason.

```
VALIDATION — <brand>

Structural:   <n> errors, <n> warnings   [justifications for each warning]

16-pixel:     PASS/FAIL — <what you actually saw>
Grayscale:    PASS/FAIL — <what you actually saw>
Blur:         PASS/FAIL — <what you actually saw>
5-second:     PASS/FAIL — <the description produced from memory>

Identity test (name removed): PASS/FAIL — <reasoning>

Outstanding: <anything unresolved>
```

A failure sends the work back to Phase 4 — or to Phase 3, if the failure is in
the concept rather than the execution. Distinguishing between those two is the
judgement call that matters most here: reworking the drawing of a fundamentally
unmemorable idea wastes the effort.
