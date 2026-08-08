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

## Lecture 4 - VAR (`chapters/03-var.qmd`)

- All 3 figures referenced in `source/slides/04_VAR/main (3).tex` migrated to `figures/var/`. No figures missing.
- Added canonical citations (Sims 1980, Lucas 1976, Sargent-Wallace 1975, Kydland-Prescott 1982, Long-Plosser 1983, Kirman 1992, Barro-Grossman 1971, Granger 1969, Zellner 1962) to `references.bib`; the slides gave author/year/journal only, standard volume/page metadata for these well-known papers was completed and should be spot-checked.
- The slide mentions "*Transforming Modern Macroeconomics: Exploring Disequilibrium Microfoundations, 1956-2003* (2012)" without an author. Kept as plain-text mention (not a formal `@citation`) rather than guessing the author, per the no-invented-metadata rule.
- The VECM / cointegration material (end of the VAR lecture, "for the 6th class") is deliberately kept brief here as a preview - full treatment is in the Cointegration and DFM chapter converted from lecture 7.
