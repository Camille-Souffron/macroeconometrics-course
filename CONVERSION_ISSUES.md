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

## Lecture 5 - Structural VAR, Identification, and Policy Shock Assessment (`chapters/04-svar-identification.qmd`)

- All 23 figures referenced in `source/slides/05_Structural_VAR_Identification/main (4).tex` migrated to `figures/svar/`. No figures missing.
- Two forward cross-references (`@sec-nonlinear`) point to the Nonlinear Models chapter, converted next in this same session; they were left unresolved in this commit's render and will resolve once that chapter is added (Quarto reports this as a warning, not a render failure).
- The Proxy-VAR / external-instruments content originally found at the top of lecture 6's source (relocated here, see the Lecture 6 note below) has since been added as its own subsection, "External instruments: the Proxy-VAR" (`@sec-proxy-var`), placed after the narrative-approach material it naturally follows.
- Citation year discrepancy: the slide cites "Jordà, 2015" for local projections, but the well-established local-projections paper of that title is Jordà (2005), *American Economic Review* 95(1). Flagged inline in the chapter with a `REVIEW` comment rather than silently corrected; the 2005 citation is used as the best-supported match.
- `Arias, Caldara & Rubio-Ramírez (2016)` (cited in the slide re: the Uhlig 2005 critique) is included in `references.bib` as an `@unpublished` entry with author/title/year only - the exact publication venue and year (a related paper appeared in the *Journal of Monetary Economics* in 2019) was not verified with confidence, so no journal/volume/pages were invented.
- `Romer & Romer (2023)` (the revised narrative dataset extending to 2016 and adding expansionary shocks) is included with author/title/year/institution only, for the same reason.
- Several papers mentioned only in passing in the slides (Rigobon & Sack 2003/2004, Sims & Zha 2006, Lütkepohl & Netšunajev 2021, Francis/Owyang/Roush 2014, DiCecio & Owyang 2010, Baumeister & Hamilton 2015, Aruoba & Drechsel 2023) were kept as narrative mentions without formal `@citation` entries, since the slides give author/year only and full bibliographic detail was not independently verified.

## Lecture 6 - Beyond Linearity (`chapters/06-nonlinear.qmd`)

- All 11 new figures referenced in `source/slides/06_Nonlinear_specifications/main (5).tex` migrated to `figures/nonlinear/`; the lecture's opening "Cochrane abstract" figure duplicates the one already migrated for lecture 5 and was not re-copied - the chapter text does not repeat that specific figure.
- **Content relocation:** the lecture's opening frame, "A note on Proxy-VARs (SVARs with External Instruments)," appeared *before* the lecture's own `\section{Introduction}` marker and covers a linear-VAR identification method (external instruments), not a nonlinear specification. It read as a carry-over slide from lecture 5's material rather than genuinely new lecture-6 content. Per the spec's "reconstruct conceptual architecture, not accidental file ordering" principle, this content was relocated to `chapters/04-svar-identification.qmd` (`@sec-proxy-var`), alongside the other SVAR identification strategies, rather than converted in place. **Resolved.**
- `Jordà & Taylor (JEL, 2025)`, cited in the slide as a review paper, is mentioned narratively without a formal `@citation` entry - exact title not verified.
- Tong (1978) is mentioned alongside Tong & Lim (1980) in the source slide as the origin of TAR models; only the latter, better-documented reference was added to `references.bib`.

## Lecture 7 - Panel VAR, Cointegration, and Dynamic Factor Models (`chapters/05-cointegration-dfm.qmd`)

- All 8 figures referenced in `source/slides/07_Cointegration_DFM/main (6).tex` migrated to `figures/cointegration-dfm/`. No figures missing.
- The slide cites Miranda-Agrippino & Rey as "(2015/2021)"; the well-documented published version used here is Miranda-Agrippino & Rey (2020), *Review of Economic Studies* 87(6) - the 2015 date is an NBER working-paper circulation year, not verified in detail; flagged for instructor check.
- Several papers mentioned only in passing (Canova & Ciccarelli 2004, Jarociński 2010, Giraud & Kahraman 2014, Shapiro & Watson 1988, Hallin & Liška 2007, Working 1960, Boyarchenko & Elias 2024) were kept as narrative mentions without formal `@citation` entries - full bibliographic detail not independently verified.
- Barrales-Ruiz et al. (2025) and Stresing, Lindenberger & Kümmel (2008) are described from the slide's own summary (data, method, results) but not given formal `@citation` entries, since the slide does not state a publication venue for either.

## Lecture 9 - Bayesian Estimation: Foundations and Applications to VARs (`chapters/07-bvar.qmd`)

- All 6 figures referenced in `source/slides/09_BAYES/main (1).tex` migrated to `figures/bvar/`. No figures missing. (Note: this lecture's images are all synthetic/illustrative plots generated for teaching, not reproductions of a published paper's figure - no attribution issue.)
- Canova & Ciccarelli (2004), Jarociński (2010) - mentioned narratively (panel VAR hierarchical priors, in the Cointegration/DFM chapter) and Chan, Koop, Poirier & Tobias (CCMM SV taxonomy, this chapter) - kept as narrative mentions without formal `@citation` entries; full bibliographic detail not independently verified.

## Status

All 7 supplied lecture zips (01_TS, 03_ARMA, 04_VAR, 05_Structural_VAR_Identification, 06_Nonlinear_specifications, 07_Cointegration_DFM, 09_BAYES) have been converted into chapters, including the relocated Proxy-VAR material. Every piece of source material read during this conversion pass has been written into some chapter. Lectures 2, 8, and 10 referenced in the original course roadmap (`index.qmd` "Course contents") were not supplied and remain outstanding.
