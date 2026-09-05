# Phase 7 — Campaign Presentation

A logo floating on a white slide is a shape. A logo on a business card, a shop
sign, and a package is a brand. Present the second thing.

---

## The contact sheet

```bash
python scripts/build_contact_sheet.py out/logo/ --name "Brand Name" --out out/logo/contact-sheet.html
```

Self-contained HTML, no network dependencies. It inlines every SVG in the
directory and renders:

- Every variant on light and dark surfaces
- The favicon strip at 16 / 24 / 32 / 48px
- Grayscale, pure black, and pure white renderings via CSS filters
- The blur test at three intensities
- A 5-second recall timer
- A scale ramp from favicon to signage size

Open it and look at it. The sheet is a viewing instrument, not a deliverable —
its job is to make failures impossible to miss.

## The campaign layer

Present the mark in use, across the contexts the brief identified. The hero
deliverable from Phase 1 leads.

| Surface | What it proves |
| :-- | :-- |
| **Business card** | The lock-up at real scale; clear space discipline; how the mark behaves next to type |
| **App icon** | The symbol full-bleed on colour, optically centred, at 180 and 1024 |
| **Website header** | The horizontal lock-up in a live navigation context, light and dark |
| **Packaging** | The mark on a physical form — wrapping, curvature, one-colour print |
| **Signage / storefront** | The mark at architectural scale and, ideally, at a distance |
| **Billboard** | The blur test made real — legibility in three seconds at speed |
| **Merchandise** | Single-colour reproduction, embroidery, and small-area constraints |
| **Social avatar** | The symbol cropped to a circle — a very common breaking point |

Build these as HTML/CSS mock-ups rather than fabricated photographs. A clean
geometric mock-up communicates the design decision; a fake photorealistic render
communicates a fake photograph, and invites feedback about the photograph.

**The circle crop deserves specific attention.** Social platforms crop avatars
to circles without asking. A square-optimised icon loses its corners. Test it.

## Presenting to a client

Lead with the strategy, not the shape. The order that works:

1. **The brief** — restate the sentence, the emotion, the audience. This is the
   contract the design is being judged against.
2. **The category** — what everyone else looks like, and the avoid list.
3. **The mark** — large, alone, on a neutral field. Silence beats explanation.
4. **The rationale** — one paragraph on why this form carries that emotion.
   Every element traced to a decision in the brief.
5. **The system** — the variant set, showing every context is covered.
6. **The tests** — the validation report, failures included. Showing the tests
   is what distinguishes a designed mark from a generated one.
7. **The campaign** — the mark in the world.

Do not present three finished options at this stage. Three finished routes
belonged to Phase 3, where the strategic choice was made. Presenting three
finished identities pushes the decision onto taste and produces a committee
compromise.

## Motion

If the brand will use motion, define the mark's behaviour: how it builds, how it
resolves, and what its resting state is. Motion should reveal the construction
logic established in Phase 4 — a mark built on a circle grid should resolve
circularly. Keep it to under one second and ensure the mark is fully legible in
its resting frame, because that is the frame most people will actually see.
