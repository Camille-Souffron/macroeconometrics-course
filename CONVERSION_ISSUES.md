# Conversion issues

Tracks problems found while converting the source slides into the Quarto book. Entries are removed once resolved or explicitly accepted.

## General

- No `.bib` file was supplied with any lecture. All citations in the source slides are given as informal prose (author, year, sometimes journal/publisher), not as `\cite{}` keys. `references.bib` is being built up manually, chapter by chapter, transcribing exactly what each slide states; where the slide omitted volume/issue/page numbers for a well-established, unambiguous reference, standard metadata has been added and should be spot-checked (flagged inline per entry in `references.bib`).
- No custom LaTeX macros (`\newcommand`, custom `.sty`) affect the mathematical notation in any lecture inspected so far - `\cmd`/`\env` (lecture 1 preamble) are decorative, unused in the body. `\newtheorem{thm}{Theorem}` is defined but never invoked in lecture 1.
- Several figures are opaque screenshots named `Capture d'écran <date>.png` with no descriptive source name. Each has been renamed to a semantic filename under `figures/` based on its frame title/caption and (where neither existed) visual inspection of the image content - see per-lecture notes below.

## Lecture 1 - Introduction to Time Series (`chapters/01-time-series.qmd`)

- `logos.png` (title-slide institution logos) was not migrated to `figures/` - it is decorative front-matter, not course content, so it is omitted from the web version rather than given a fabricated semantic name.
- All 17 figures actually referenced (via `\includegraphics`) in `source/slides/01_TS/main (1).tex` have been migrated to `figures/ts/` with descriptive names, chosen from the frame title/caption or, where neither existed, from visual inspection. No referenced figure is missing.
- `source/slides/01_TS/` also contains ~58 image files that are *not* referenced anywhere in `main (1).tex` (linear-algebra diagrams, wavelet/spectral plots, IV/judge-design figures, heteroskedasticity illustrations, etc.). These appear to be leftover assets from other courses/lectures sharing the same image folder on the instructor's machine, not material belonging to this lecture - they were intentionally not migrated.

## Lecture 3 - AR(I)MA (`chapters/02-arma.qmd`)

- All 4 figures referenced in `source/slides/03_ARMA/main (2).tex` migrated to `figures/arma/` with descriptive names. No figures missing.
- The Nishi (2021) reading assigned as homework was added to `references.bib` (`@Nishi2021`) since the slide gave full bibliographic detail (author, year, title, journal, URL).
- `\citecolor` etc. in the preamble (`hyperref` color options) are presentation-only and were dropped, as with other Beamer-only commands.
