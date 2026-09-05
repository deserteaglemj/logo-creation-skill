# Phase 5 — The Deliverable System

A logo is not a file. It is a system of files covering every layout and every
colour context the brand will meet.

---

## Directory layout

Build into `out/logo/`. The contact-sheet builder reads this structure and these
names, so follow them exactly.

```
out/logo/
  icon-color.svg          icon-black.svg      icon-white.svg
  wordmark-color.svg      wordmark-black.svg  wordmark-white.svg
  horizontal-color.svg    horizontal-black.svg horizontal-white.svg
  stacked-color.svg       stacked-black.svg   stacked-white.svg
  icon-darkmode.svg       horizontal-darkmode.svg
  favicon.svg
  BRAND.md
```

Naming is `<component>-<variant>.svg`, all lowercase, hyphen-separated.

## The file matrix

| Component | Purpose | Required variants |
| :-- | :-- | :-- |
| **Icon / symbol** | App icons, favicons, avatars, stamps, tiny use | color, black, white, darkmode |
| **Wordmark** | Where the symbol is redundant — letterheads, footers | color, black, white |
| **Horizontal lock-up** | Default. Website headers, email signatures, banners | color, black, white, darkmode |
| **Stacked lock-up** | Square and portrait spaces — merchandise, signage, social | color, black, white |
| **Favicon** | 16px-optimised icon; may be a simplified variant | single file |

**Colour variants explained:**

- **color** — the full-colour master, on light backgrounds.
- **black** — pure `#000000`, single colour. For fax, engraving, embossing,
  single-colour print, and stamps. Not "the dark grey one".
- **white** — pure `#FFFFFF`, single colour, for placement on dark or
  photographic backgrounds. Must be a real file, not a CSS filter.
- **darkmode** — the full-colour mark adjusted for dark surfaces. Often not
  identical to the light-mode version: saturated colours need lifting in
  lightness to hold contrast on dark, and a near-black element must be swapped
  for the light neutral.

The favicon may legitimately be a *simplified* version of the icon — dropping an
internal detail that fills in at 16px is correct practice, not cheating, as long
as the silhouette matches.

## Raster exports

Vector is the master; rasters are generated. Produce PNGs at:

- **Favicon:** 16, 32, 48
- **App icon:** 180 (iOS), 192, 512 (Android/PWA), 1024 (store listing)
- **Social:** 400×400 avatar, 1200×630 OG card
- **Print check:** the horizontal lock-up at 300 dpi at its intended physical width

App icons need their own treatment — a symbol placed on a full-bleed background
with the platform's safe area respected, optically centred (see the optical
centring note in `svg-craft.md`), never the horizontal lock-up shrunk down.

## Usage rules to document

Write these into `BRAND.md` alongside the files:

- **Clear space** — expressed as a fraction of symbol height (e.g. `0.5x` on all
  sides). Give it as a ratio, never in pixels, so it scales.
- **Minimum sizes** — the smallest width at which each component may be used, in
  both px and mm. State them separately: the icon's floor is far smaller than the
  horizontal lock-up's.
- **Approved backgrounds** — which variant goes on which surface, including the
  photographic case.
- **Colour values** — HEX, RGB, and CMYK for every brand colour.
- **Misuse** — the prohibitions worth writing down: do not stretch, do not
  rotate, do not recolour outside the palette, do not add effects, do not place
  the colour version on a busy photograph, do not reconstruct the lock-up with a
  different gap, do not outline the mark to force contrast.

## Gate

Every file in the matrix exists on disk before Phase 6 begins. A "system" with
gaps is a mark that will be improvised badly by whoever needs the missing case.

The Phase 8 packager enforces this same matrix when it builds the client
archive — see `handoff.md`. If the names here drift, the packaging step fails.
