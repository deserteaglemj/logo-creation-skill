# Phase 8 — The Client Archive

The deliverable is not a logo. It is a folder someone can open in two years,
without you, and use correctly on the first try.

Most brand handoffs fail the same way: a zip of whatever happened to be on the
designer's desktop, named `logo_final_v3_USE_THIS.zip`, containing four files
that all look identical and one the client is afraid to touch. The archive below
is the fix — not more files, but files whose purpose is obvious.

---

## Build it

```bash
python scripts/package_brand.py out/logo/ --name "Brand Name" --exports out/exports/
```

The packager collects and organises; it does not rasterise or convert. Produce
the PNG, PDF and EPS exports first, then point `--exports` at them. Pass the flag
more than once to pull from several directories.

It exits non-zero if a required deliverable is missing. That is deliberate: the
gap is cheap to close now and expensive to close after the client has started
using the kit. `--force` ships anyway and lists what is absent.

## The layout

```
brand.zip
├── README.txt          which file for which job — generated
├── BRAND.md            clear space, minimum sizes, colours, misuse
├── favicon.ico         multi-resolution, generated from the icon PNGs
├── logo/               SVG masters — the source of truth
├── png/                fixed-size rasters
├── print/              PDF + EPS
└── preview/            the contact sheet from Phase 7
```

**`logo/`** — every variant from the Phase 5 matrix. Vector, scalable, the file
every other file in the kit was generated from. This is what a developer or a
future designer needs.

**`png/`** — only sizes that are *required* by a slot, not a spread of arbitrary
exports: 16/32/48 for favicons, 180 for iOS, 192 and 512 for Android and PWA,
400 for social avatars, 1024 for store listings. A raster exists because
something demands exact pixels; anything else should be the SVG.

**`print/`** — PDF and EPS. Neither is redundant. A print shop will usually take
the PDF; sign makers, vinyl cutters and embroidery digitisers still ask for EPS,
and being unable to supply one delays a job by days. Hand over the whole folder
and let the supplier pick.

**`preview/`** — the contact sheet. It costs nothing to include and it answers
"why does the small version look different?" before the client asks.

**`README.txt`** — the single highest-leverage file in the archive. Not a brand
manual: a lookup table from *situation* to *filename*. The person opening the zip
is usually not a designer, and their question is never "what is an EPS", it is
"what do I send the printer".

## What stays out

- **Editable source files** (`.afdesign`, `.ai`, `.sketch`) unless the client has
  explicitly asked to edit the mark themselves. Including them invites someone to
  open the logo and "just tweak it", which is how identity systems die.
- **Design explorations, rejected routes, working files.** They were the process,
  not the product. Keep them; do not ship them.
- **Fonts**, unless you have verified the licence permits redistribution. Name the
  typeface in `BRAND.md` and let the client license it.
- **Motion or animated versions**, unless commissioned. An unbriefed animation
  becomes an expectation.
- **Mockups as deliverables.** They are presentation material. A client who finds
  a billboard JPEG in the assets folder will eventually use it as a logo.

## Naming the archive

`<brand-slug>-brand-kit.zip`, generated from `--name`. Never `final`, never a
version number the client has to reason about, never a date. If you reissue,
reissue the same filename with a changelog line in `BRAND.md` — the client should
never have to decide which of two zips is current.

## Gate

The archive builds without `--force`, and every folder in it is one a
non-designer can act on without asking a question.
