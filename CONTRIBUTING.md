# Contributing

Thanks for considering a contribution.

## Ground rules

This project is opinionated on purpose. Two rules matter more than the rest:

1. **If you change a script, the tests must still pass.** Run `pytest` before
   opening a pull request.
2. **If you change a design rule, say which real failure it prevents.** Every
   rule in `references/` exists because something broke without it. A rule that
   cannot name its failure mode is taste, and taste belongs in a fork.

## Getting set up

There is nothing to install. The scripts use only the Python standard library
(3.10+). For the test suite:

```bash
pip install pytest
pytest
```

## Running the tools

```bash
python scripts/validate_svg.py examples/demo
python scripts/build_contact_sheet.py examples/demo --name "Demo"
```

## What makes a good pull request

- **A focused change.** One idea per PR.
- **A stated reason.** Especially for the reference documents — describe the
  logo that failed and how the change would have caught it.
- **Tests for new script behaviour.** If you add a check to the validator, add a
  fixture that trips it and one that does not.
- **No new dependencies.** Dependency-free is a feature. The scripts must run on
  a bare Python install.

## Things likely to be declined

- Adding a raster pipeline, a font dependency, or a headless browser requirement
  to the core scripts.
- Loosening a validator check because it flagged something inconvenient. If a
  check produces false positives, fix its precision — do not remove it.
- Design advice that amounts to a trend. This skill targets marks that stay
  usable for a decade.

## Reporting bugs

Open an issue using the bug report template. For validator issues, please
include the SVG that triggered it — a one-line reproduction is worth more than a
description.

## Code style

Match the surrounding code. The scripts favour small pure functions, explicit
names, and comments that explain *why* a value was chosen rather than restating
what the line does.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
