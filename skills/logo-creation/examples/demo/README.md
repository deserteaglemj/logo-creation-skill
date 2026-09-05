# Demo fixtures

**These are tooling fixtures, not a design sample.**

Plain geometric placeholders for a fictional brand ("Halyard"), here so both
scripts are runnable immediately after cloning:

```bash
python scripts/validate_svg.py examples/demo
python scripts/build_contact_sheet.py examples/demo --name "Halyard"
python scripts/package_brand.py examples/demo --name "Halyard"
```

They exist to exercise the parts of the tooling that need real files:

- the `<component>-<variant>.svg` naming convention the validator and the
  contact-sheet builder both read
- the component-aware stroke floor (icon at 16&nbsp;px, lock-ups at 120&nbsp;px)
- the lock-up composition maths and the contact sheet's sort order
- the packager's completeness check — the placeholder `BRAND.md` exists so
  `package_brand.py` builds without `--force`; it has no raster or print
  exports, so the run reports those as notes

They are deliberately boring. A fixture should not compete for attention with
the tool it demonstrates, and nothing here is meant to be an example of good
logo design — for that, see [`../../SKILL.md`](../../SKILL.md) and the reference
documents.

## Regenerating

```bash
python examples/demo/make_demo.py
```

CI checks that the committed files match the generator's output, so run this
after editing `make_demo.py`.

## One note worth keeping

The first version of the icon was an open ring with a vertical bar through it.
It read unmistakably as a **power button** — the exact known-symbol collision
that [`references/design-execution.md`](../../references/design-execution.md)
warns about, sitting in the example folder of a logo-design tool.

It is now an H monogram. The lesson generalises: a mark can be geometrically
clean, pass every automated check, and still be unusable because it already
means something else. Only rendering it and looking at it catches that.
