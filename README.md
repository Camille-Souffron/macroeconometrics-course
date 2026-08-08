# Macroeconometrics - Course Notes

Online course notes for a graduate macroeconometrics course (M2 EPOG JM), built with [Quarto](https://quarto.org) as a book and published to GitHub Pages.

**Live site:** https://Camille-Souffron.github.io/macroeconometrics-course/

## Repository layout

```text
chapters/     Converted course content (.qmd), one file per chapter
exercises/    Extracted exercises, where present in the source material
figures/      Web-ready figures (SVG preferred, PNG when necessary), by chapter
code/         Longer code excerpts referenced from the chapters
data/         Small datasets used in examples
styles/       Custom Quarto/SCSS styling
source/slides/  Original LaTeX/Beamer lecture material (immutable; not edited)
```

See `COURSE_BUILD_SPEC.md` for the full conversion and deployment specification this repository follows, and `CONVERSION_ISSUES.md` for open issues (missing assets, uncertain citations, etc.) found during conversion.

## Local development

```bash
quarto preview      # live preview while editing
quarto render        # full build, must succeed before every commit intended for deployment
```

## Deployment

Pushes to `main` trigger `.github/workflows/publish.yml`, which renders the book and publishes it to the `gh-pages` branch.
