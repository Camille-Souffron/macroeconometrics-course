# Macroeconometrics Online Course — Conversion and Deployment Specification

## 0. Project objective

Build a public, maintainable, academically rigorous online macroeconometrics course from the existing LaTeX/Beamer teaching material.

The existing `.tex` slides are the **academic source material**, but the target must **not** be a slide-by-slide transcription. The final product should be a continuous web textbook/course optimized for reading in a browser.

Target stack:

- **Authoring:** Quarto `.qmd`
- **Editing:** VS Code
- **Version control:** Git
- **Repository:** GitHub
- **GitHub account:** `Camille-Souffron`
- **Hosting:** GitHub Pages
- **Deployment:** GitHub Actions
- **Primary output:** HTML
- **Possible secondary output later:** PDF
- **Mathematics:** MathJax/LaTeX syntax
- **Bibliography:** BibTeX
- **Figures:** SVG whenever possible, PNG when necessary
- **Code:** displayed in language-appropriate fenced blocks; executable only when useful
- **Design principle:** academic textbook rather than presentation deck

Suggested repository name:

```text
macroeconometrics-course
```

Expected public URL:

```text
https://Camille-Souffron.github.io/macroeconometrics-course/
```

Do not configure a custom domain during the initial build. The GitHub Pages version must work correctly first.

---

# 1. Fundamental conversion principle

The source Beamer slides were designed for oral teaching. The website is designed for autonomous reading.

Therefore:

> **Do not map one Beamer `frame` to one web section.**

Instead, reconstruct the conceptual structure of the course.

For example, slides such as:

```text
Frame 1 — The VAR model
Frame 2 — The VAR model
Frame 3 — The VAR model
Frame 4 — Example
Frame 5 — Example continued
Frame 6 — Stability
Frame 7 — Stability condition
```

should become something like:

```markdown
# Vector Autoregressions

## Definition

## Reduced-form representation

## Companion form

## Stability

### Characteristic roots

### Economic interpretation

## Worked example
```

The web version must preserve the mathematical and econometric content of the slides while making implicit oral transitions explicit when necessary.

Do **not** invent new substantive economic claims merely to fill gaps.

When clarification is necessary, derive it carefully from the existing mathematics or flag it with:

```markdown
<!-- TODO: instructor clarification required -->
```

rather than guessing.

---

# 2. Preserve the original sources

Create a dedicated immutable source directory:

```text
source/
└── slides/
```

Copy all original teaching material there, including:

```text
.tex
.bib
.sty
.cls
.pdf
.png
.jpg
.jpeg
.svg
.eps
TikZ source
data files
code used to generate figures
included .tex files
```

Do not modify the original files in `source/slides/` unless explicitly instructed.

The conversion should happen in separate `.qmd` files.

This separation is essential:

```text
original Beamer source
        ↓
semantic extraction
        ↓
Quarto course
```

and not:

```text
original Beamer source
        ↓
destructive modification
```

---

# 3. Initial audit before writing any chapter

Before performing the conversion, inspect **all relevant source files**.

In particular:

1. Locate the main Beamer `.tex` files.
2. Resolve all `\input{}` and `\include{}` statements.
3. Read the LaTeX preambles.
4. Identify custom commands defined through:
   - `\newcommand`
   - `\renewcommand`
   - `\DeclareMathOperator`
   - custom `.sty` files.
5. Locate all bibliography files.
6. Locate all figures.
7. Identify generated figures, TikZ diagrams and external image dependencies.
8. Identify code snippets.
9. Identify exercises, examples and empirical applications.
10. Identify repeated material across different lectures.

Generate an internal conversion inventory such as:

```text
Lecture 1
- source: slides/lecture01.tex
- topic: introduction / time series
- figures: 5
- equations: ~20
- citations: Sims1980, Hamilton1994, ...
- custom macros: \E, \Var, \eps, ...
- proposed destination: chapters/01-introduction.qmd

Lecture 2
...
```

Do this **before** mass conversion.

The purpose is to determine the conceptual architecture of the course rather than reproducing the accidental ordering of the files.

---

# 4. Verify the local toolchain

Before creating the project, check:

```bash
git --version
quarto --version
```

If GitHub CLI is available:

```bash
gh --version
gh auth status
```

Do not assume that `gh` is installed.

If Quarto is missing, report this clearly rather than attempting arbitrary package-manager modifications without checking the environment.

The VS Code Quarto extension is recommended for local previewing but the project must remain buildable from the command line.

---

# 5. Repository initialization

If no repository already exists, initialize one.

Suggested local directory:

```text
macroeconometrics-course/
```

Initialize Git:

```bash
git init
git branch -M main
```

If GitHub CLI is authenticated, the remote repository may be created with:

```bash
gh repo create Camille-Souffron/macroeconometrics-course \
  --public \
  --source=. \
  --remote=origin
```

Otherwise, create the repository manually on GitHub and add the remote:

```bash
git remote add origin https://github.com/Camille-Souffron/macroeconometrics-course.git
```

Before pushing anything, verify:

```bash
git remote -v
git status
```

---

# 6. Target repository structure

Use approximately the following architecture:

```text
macroeconometrics-course/
│
├── _quarto.yml
├── index.qmd
├── references.qmd
├── references.bib
├── README.md
├── LICENSE
├── .gitignore
│
├── chapters/
│   ├── 01-introduction.qmd
│   ├── 02-time-series.qmd
│   ├── 03-var.qmd
│   ├── 04-svar.qmd
│   ├── 05-identification.qmd
│   ├── 06-bvar.qmd
│   ├── 07-sign-restrictions.qmd
│   ├── 08-proxy-svar.qmd
│   ├── 09-local-projections.qmd
│   └── ...
│
├── exercises/
│   ├── ...
│
├── figures/
│   ├── introduction/
│   ├── var/
│   ├── svar/
│   └── ...
│
├── code/
│   ├── matlab/
│   ├── python/
│   ├── r/
│   └── julia/
│
├── data/
│   └── ...
│
├── styles/
│   └── custom.scss
│
├── source/
│   └── slides/
│       └── ORIGINAL LATEX MATERIAL
│
└── .github/
    └── workflows/
        └── publish.yml
```

Adapt chapter names to the actual course.

Do not create empty chapters merely because they appear in this example.

---

# 7. Quarto project type

Use a **Quarto Book** rather than a collection of independent pages.

The course behaves conceptually like an online textbook:

- ordered chapters;
- hierarchical sections;
- persistent navigation;
- previous/next chapter navigation;
- search;
- equation numbering;
- figure numbering;
- bibliography;
- cross-chapter references.

Start `_quarto.yml` approximately as follows:

```yaml
project:
  type: book

book:
  title: "Macroeconometrics"
  author: "Camille Souffron"
  search: true

  chapters:
    - index.qmd

    # Replace this example architecture by the actual course structure.

    - part: "Foundations"
      chapters:
        - chapters/01-introduction.qmd
        - chapters/02-time-series.qmd

    - part: "Vector Autoregressions"
      chapters:
        - chapters/03-var.qmd
        - chapters/04-svar.qmd
        - chapters/05-identification.qmd

    - part: "Modern Identification Methods"
      chapters:
        - chapters/06-bvar.qmd
        - chapters/07-sign-restrictions.qmd
        - chapters/08-proxy-svar.qmd
        - chapters/09-local-projections.qmd

    - references.qmd

bibliography: references.bib

format:
  html:
    theme:
      - cosmo
      - styles/custom.scss
    toc: true
    toc-depth: 3
    number-sections: true
    code-fold: true
    code-tools: true

execute:
  freeze: auto
```

Do not over-customize the visual theme during the first phase.

First obtain a structurally correct, readable and reproducible course.

Visual polishing comes afterwards.

---

# 8. Home page

`index.qmd` must function as an actual landing page rather than Chapter 1.

It should contain:

```markdown
# Macroeconometrics

Camille Souffron

## About this course

Short description.

## Course contents

Short description of the main parts of the course.

## How to use these notes

Explanation of:

- mathematical notation;
- code examples;
- exercises;
- references.

## Contents

The Quarto navigation provides access to the individual chapters.
```

Eventually, information such as institution, academic year, syllabus and downloadable material can be added.

Do not hard-code information that is absent from the source or from explicit instructions.

---

# 9. Conversion protocol: LaTeX → Quarto

## 9.1 Text

Convert ordinary LaTeX prose into normal Markdown.

For example:

```latex
\textbf{Identification} refers to...
```

becomes:

```markdown
**Identification** refers to...
```

Do not preserve LaTeX formatting commands when native Markdown is cleaner.

---

## 9.2 Sections

Translate:

```latex
\section{}
\subsection{}
\subsubsection{}
```

into:

```markdown
#
##
###
```

but determine heading level from the **logical hierarchy of the web chapter**, not blindly from the original Beamer hierarchy.

---

## 9.3 Beamer frames

Remove:

```latex
\begin{frame}
...
\end{frame}
```

as structural objects.

Their contents should be merged into coherent web sections.

Remove presentation-only commands such as:

```latex
\pause
\only
\uncover
\visible
\onslide
```

For overlays, reconstruct the **final intended logical content**.

Do not duplicate every overlay state.

---

# 10. Mathematics

Preserve mathematical notation with extremely high fidelity.

Inline mathematics:

```markdown
$y_t$
```

Display mathematics:

```markdown
$$
y_t = A_1 y_{t-1} + \cdots + A_p y_{t-p} + u_t.
$$
```

Never rewrite mathematical expressions merely for stylistic reasons.

Check carefully:

- subscripts;
- superscripts;
- transposes;
- inverses;
- expectations;
- covariance matrices;
- lag operators;
- summation indices;
- dimensions;
- normalization assumptions;
- signs.

Custom LaTeX macros must either:

1. be supported globally in the HTML math environment; or
2. be expanded into standard LaTeX during conversion.

Prefer standard mathematical LaTeX when expansion remains readable.

---

# 11. Equation numbering and cross-references

Where an equation is conceptually important and referenced elsewhere, use Quarto equation labels.

Example:

```markdown
$$
A_0 y_t
=
A_1 y_{t-1}
+
\varepsilon_t
$$ {#eq-structural-var}
```

Then reference it as:

```markdown
Equation @eq-structural-var defines the structural VAR.
```

Use stable semantic labels.

Good:

```text
eq-var-companion
eq-svar-structural
eq-bq-long-run
eq-lp-baseline
```

Bad:

```text
eq1
eq2
equation-final
test
```

---

# 12. Figures

All figures must be stored under `figures/`.

Use meaningful filenames:

```text
figures/svar/recursive-identification.svg
figures/svar/monetary-policy-irf.png
figures/var/companion-form.svg
```

rather than:

```text
image1.png
graph_final2.png
Capture.PNG
```

A figure should normally be embedded with a caption and identifier:

```markdown
![Impulse responses to a monetary policy shock.](../figures/svar/monetary-policy-irf.svg){#fig-monetary-irf}
```

It can then be cited with:

```markdown
@fig-monetary-irf
```

---

# 13. Existing LaTeX/TikZ figures

Do **not** discard TikZ or PGFPlots figures.

For HTML output:

1. identify the original figure source;
2. preserve it under `source/`;
3. compile/export a web-compatible version;
4. prefer **SVG** for vector diagrams and plots;
5. use high-resolution PNG only when SVG is inappropriate;
6. verify labels visually after conversion.

Do not replace a mathematically meaningful figure with a screenshot if a clean vector export is feasible.

Be especially careful with:

- arrows;
- mathematical labels;
- legends;
- line types;
- axes;
- confidence intervals;
- annotations.

---

# 14. Bibliography

Reuse the existing `.bib` bibliography whenever possible.

Centralize it at:

```text
references.bib
```

Convert LaTeX citations such as:

```latex
\cite{Sims1980}
\citep{Uhlig2005}
\citet{Jorda2005}
```

to appropriate Quarto/Pandoc citations.

Examples:

```markdown
[@Sims1980]
```

or sentence-integrated references consistent with Pandoc citation syntax.

Do not manually type bibliographic references into the prose if a valid BibTeX entry exists.

Do not silently invent missing metadata.

If a citation key is used in the slides but absent from the bibliography, report it explicitly.

---

# 15. Definitions, propositions and proofs

Important formal material should receive a stable semantic structure.

For example:

```markdown
::: {.callout-note title="Definition: covariance-stationary process"}

A process ...

:::
```

For genuinely formal propositions or theorems, use Quarto's theorem/proof system when appropriate rather than styling everything as a callout.

Distinguish carefully between:

- definition;
- assumption;
- proposition;
- theorem;
- proof;
- intuition;
- empirical result;
- warning.

Do not relabel informal slide statements as theorems.

---

# 16. Pedagogical callouts

Use callouts sparingly.

Recommended semantic conventions:

```text
Note        → useful technical information
Tip         → intuition or computational shortcut
Important   → key result
Warning     → common mistake / identification caveat
```

Example:

```markdown
::: {.callout-warning title="Identification is not estimation"}

Estimating the reduced-form VAR does not by itself identify structural shocks.

:::
```

Do not turn every paragraph into a colored box.

The main text must remain readable as continuous prose.

---

# 17. Code

Preserve useful code examples.

Organize substantial scripts under:

```text
code/
```

and show only relevant excerpts in the chapters.

Use correct fenced blocks:

````markdown
```matlab
...
```
````

````markdown
```python
...
```
````

````markdown
```r
...
```
````

````markdown
```julia
...
```
````

Do not automatically make every code block executable.

Distinguish between:

- pedagogical code displayed to students;
- code used to generate website outputs;
- full replication scripts.

If executable Python/R/Julia content is added, dependencies must eventually be pinned in an appropriate environment file.

---

# 18. MATLAB and Dynare

MATLAB and Dynare material should initially be treated as **source/display code**, unless a robust execution pipeline is explicitly available.

Do not attempt to execute MATLAB or Dynare in GitHub Actions merely to make the project appear fully reproducible.

A static website is preferable to a fragile CI pipeline.

Full replication code can be downloadable from the repository.

---

# 19. Exercises

When exercises occur in the slides, extract them into clearly marked sections.

Possible structure:

```markdown
## Exercises

### Exercise 1 — VAR stability

...

### Exercise 2 — Structural identification

...
```

If solutions exist, they can initially be placed in collapsible sections or in a dedicated solutions chapter.

Do not generate solutions to existing graded exercises without explicit authorization if the source material does not contain them.

---

# 20. Content expansion policy

The agent is allowed to perform **editorial reconstruction**, but not uncontrolled substantive expansion.

Allowed:

- turn slide fragments into complete grammatical sentences;
- make implicit notation explicit;
- connect two consecutive equations with a short explanation;
- explain what an object denotes when directly inferable;
- eliminate duplicated slide material;
- reorganize several frames into a coherent subsection.

Requires explicit flagging or later instructor validation:

- adding a theorem not present in the material;
- claiming a stronger identification result;
- modifying assumptions;
- changing notation;
- adding literature;
- adding empirical claims;
- deriving new results;
- correcting a potentially substantive error.

Use:

```markdown
<!-- REVIEW: possible substantive issue in original slides: ... -->
```

for anything requiring instructor judgment.

---

# 21. Notation consistency

Create an internal notation audit while converting.

Check, chapter by chapter:

```text
y_t
u_t
ε_t
A(L)
B(L)
Σ_u
A_0
structural shocks
reduced-form innovations
IRF notation
FEVD notation
instrument notation
```

Do not silently standardize symbols if doing so could change meaning.

If the slides use inconsistent notation, identify the conflict before normalizing it.

Once a notation convention is adopted for the website, apply it consistently.

---

# 22. Semantic links between chapters

The website should exploit hyperlinks.

Instead of writing:

```text
as seen previously
```

prefer an explicit reference:

```markdown
As discussed in @sec-var-stability, ...
```

Create section identifiers for important sections:

```markdown
## Stability {#sec-var-stability}
```

This is particularly important for concepts reused throughout the course:

- stationarity;
- Wold representation;
- VAR stability;
- structural shocks;
- identification;
- Cholesky identification;
- long-run restrictions;
- sign restrictions;
- external instruments;
- impulse responses;
- local projections.

---

# 23. First-pass visual design

Keep the initial design deliberately restrained.

Priorities:

1. typography;
2. readability of equations;
3. readable figures;
4. correct responsive layout;
5. clear sidebar;
6. useful table of contents;
7. search;
8. code folding.

Do not begin with custom JavaScript animations, elaborate dashboards or heavy CSS.

A rigorous academic course should remain usable with minimal styling.

---

# 24. CSS customization

Put all custom styling in:

```text
styles/custom.scss
```

Avoid inline CSS scattered through the chapters.

Initial customization should be minimal.

Possible later improvements:

- slightly wider main text;
- better figure spacing;
- theorem styling;
- improved tables;
- consistent callout appearance;
- mobile layout;
- print layout.

Do not override Quarto defaults without a specific reason.

---

# 25. Local development workflow

During development, run:

```bash
quarto preview
```

Use the live preview to inspect changes.

Before any significant commit intended for deployment, run:

```bash
quarto render
```

A successful partial preview is **not** sufficient validation.

The complete book must render.

---

# 26. Git ignore policy

Create an appropriate `.gitignore`.

At minimum, exclude transient Quarto build files and the rendered book when using the `gh-pages` deployment workflow:

```gitignore
/.quarto/
/_book/
```

Do **not** ignore source figures, bibliography, course source, or `_freeze/` if frozen computations are deliberately used.

Never commit editor caches or machine-specific temporary files.

---

# 27. Development Git workflow

Use small, semantically meaningful commits.

Examples:

```text
Initialize Quarto course structure

Import original Beamer sources

Convert VAR chapter

Add structural identification figures

Migrate bibliography to BibTeX

Add cross-references to SVAR chapter

Configure GitHub Pages deployment
```

Avoid commits such as:

```text
stuff
update
changes
final
final2
test
```

Before committing:

```bash
quarto render
git status
git diff
```

Then:

```bash
git add .
git commit -m "..."
git push
```

---

# 28. Initial conversion strategy

Do **not** convert the entire course automatically before validating the method.

Proceed in stages.

## Phase A — Skeleton

Create:

```text
_quarto.yml
index.qmd
references.qmd
styles/custom.scss
chapter directory structure
```

Verify:

```bash
quarto render
quarto preview
```

---

## Phase B — Pilot chapter

Choose one representative chapter, ideally one containing:

- prose;
- mathematics;
- equations;
- citations;
- figures;
- several conceptual sections.

A VAR or SVAR chapter is a good candidate.

Convert this chapter completely.

Then validate:

- mathematical fidelity;
- typography;
- figure handling;
- bibliography;
- cross-references;
- navigation;
- chapter structure.

Only after the pilot chapter is satisfactory should the remaining lectures be converted systematically.

---

## Phase C — Full conversion

Convert the other chapters one by one.

For each chapter:

```text
1. inspect source
2. map conceptual structure
3. convert prose
4. convert mathematics
5. migrate figures
6. migrate citations
7. migrate code
8. add cross-references
9. render
10. inspect
11. commit
```

Do not accumulate the whole conversion into one massive unreviewable change.

---

# 29. GitHub Pages: first publication

Once a valid local build exists and the repository is connected to GitHub, perform an initial publication using the Quarto GitHub Pages workflow appropriate to the installed/current Quarto version.

A common command is:

```bash
quarto publish gh-pages
```

Verify the command against the installed Quarto documentation/help if necessary before execution.

The expected project URL for a repository named:

```text
macroeconometrics-course
```

is:

```text
https://Camille-Souffron.github.io/macroeconometrics-course/
```

Check specifically that:

- the home page loads;
- CSS loads;
- figures load;
- chapter links work;
- mathematical equations render;
- relative links are correct.

---

# 30. Continuous deployment with GitHub Actions

After the first successful publication, configure:

```text
.github/workflows/publish.yml
```

Use the current official Quarto GitHub Actions workflow compatible with the installed Quarto version.

A typical configuration is:

```yaml
on:
  workflow_dispatch:
  push:
    branches: main

name: Quarto Publish

jobs:
  build-deploy:
    runs-on: ubuntu-latest

    permissions:
      contents: write

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Quarto
        uses: quarto-dev/quarto-actions/setup@v2

      - name: Render and Publish
        uses: quarto-dev/quarto-actions/publish@v2
        with:
          target: gh-pages
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Before committing this workflow, verify the current official Quarto action syntax and GitHub Pages requirements.

This means that once deployment is configured correctly, normal updates can follow:

```text
edit source
→ render locally
→ commit
→ push main
→ GitHub Action
→ updated public course
```

Ensure GitHub Actions has the repository permissions required to write the publication branch.

---

# 31. Executable computations and `freeze`

Initially use:

```yaml
execute:
  freeze: auto
```

when computational output is included.

The rationale is to separate:

```text
expensive / environment-dependent computation
```

from:

```text
HTML rendering
```

and avoid requiring GitHub Actions to reproduce every local scientific-computing environment.

If `_freeze/` is generated intentionally, commit it.

Only move towards fully executing Python/R/Julia computations in CI when:

- dependencies are pinned;
- the environment is reproducible;
- runtime is acceptable;
- no private/local data are required;
- no unavailable proprietary software is required.

---

# 32. Quality assurance

Every converted chapter must satisfy the following checks.

## Mathematical QA

- equations agree with the source;
- signs are correct;
- dimensions are coherent;
- expectations and conditional expectations are preserved;
- lag indices are correct;
- covariance notation is correct;
- matrices and vectors are not accidentally changed;
- identification assumptions are preserved.

## Editorial QA

- no slide-navigation language remains;
- no unexplained “as shown above” survives when the object is no longer above;
- bullet fragments are converted where appropriate;
- redundancies caused by Beamer overlays are removed;
- definitions appear before major uses when feasible.

## HTML QA

- headings are hierarchical;
- sidebar works;
- table of contents works;
- internal links work;
- citations resolve;
- figures load;
- equations render;
- cross-references resolve;
- code blocks display correctly;
- no raw unsupported LaTeX commands appear visibly.

## Repository QA

Run:

```bash
git status
quarto render
```

and ensure there are no accidental generated files or missing assets.

---

# 33. Broken-link and missing-resource policy

Never silently remove an unavailable figure, citation or included source.

Instead, record the problem.

For example:

```markdown
<!-- MISSING ASSET: original source refers to figures/VAR_IRF.pdf -->
```

Maintain a temporary file if necessary:

```text
CONVERSION_ISSUES.md
```

with entries such as:

```markdown
# Conversion issues

## Lecture 4

- Missing `monetaryshock.pdf`.
- Citation `StockWatson2001` absent from supplied `.bib`.
- Macro `\mycov` defined in unavailable style file.
```

This file should eventually be empty or contain only explicitly accepted limitations.

---

# 34. Prohibited shortcuts

Do **not**:

- convert the PDF pages into screenshots and call that the website;
- embed entire slide PDFs instead of converting the content;
- convert every `frame` mechanically into a section;
- rasterize equations;
- replace LaTeX equations by images;
- remove citations because conversion is inconvenient;
- invent bibliography entries;
- change economic notation without checking;
- discard figure source;
- duplicate Beamer overlays;
- rely on absolute local file paths;
- expose private file paths;
- commit credentials;
- commit GitHub tokens;
- require proprietary software merely to render ordinary HTML pages;
- substantially rewrite the academic content without flagging the changes.

---

# 35. Desired final reader experience

A student visiting the website should encounter something closer to an online textbook than a slide archive.

Example:

```text
Macroeconometrics
│
├── Foundations
│   ├── Time Series
│   └── Wold Representation
│
├── Vector Autoregressions
│   ├── Reduced-form VAR
│   ├── Companion Form
│   ├── Stability
│   ├── Forecasting
│   └── Impulse Responses
│
├── Structural VARs
│   ├── Structural Representation
│   ├── Identification Problem
│   ├── Recursive Identification
│   ├── Long-run Restrictions
│   └── Sign Restrictions
│
├── Bayesian VARs
│
├── External Instruments
│
└── Local Projections
```

Within a chapter:

```text
Chapter title
────────────────────────────────────

Short motivation

1. Main concept

   prose

   equation

   intuition

2. Identification / derivation

   derivation

   proposition

   figure

3. Empirical example

   figure

   interpretation

4. Code / implementation

5. References / further reading
```

This should scroll naturally as a web document.

---

# 36. Separation between course and source slides

The repository should ultimately expose three distinct layers:

```text
SOURCE LAYER
LaTeX slides
bibliography
original figures
original code

       ↓

COURSE LAYER
Quarto chapters
web figures
cross-references
pedagogical structure

       ↓

PUBLICATION LAYER
GitHub Actions
gh-pages
HTML website
```

The source layer provides traceability.

The course layer provides readability.

The publication layer provides distribution.

Do not collapse these layers.

---

# 37. Optional later extensions

These should **not** block the initial release.

Once the complete static course is stable, possible extensions include:

- downloadable PDF version;
- downloadable lecture slides;
- exercises and solutions;
- interactive plots;
- executable Python examples;
- downloadable datasets;
- replication notebooks;
- glossary;
- index of notation;
- bibliography by chapter;
- instructor-only material in a separate/private repository;
- custom domain;
- analytics;
- quizzes;
- interactive simulations.

Treat these as Phase II.

---

# 38. Definition of done for Version 1

Version 1 is complete only when:

- the original `.tex` material is preserved;
- the course has a coherent chapter hierarchy;
- all intended core lectures are converted;
- mathematics renders correctly;
- important equations have semantic cross-references;
- figures render correctly;
- citations resolve through BibTeX;
- navigation works;
- search works;
- local `quarto render` succeeds without errors;
- the site deploys successfully through GitHub Pages;
- pushing a change to `main` triggers an automatic deployment;
- there are no known missing assets left unreported;
- no credentials or private information are committed;
- the published site is readable both on desktop and on a reasonably narrow browser window.

---

# 39. Agent workflow

When executing this specification, work sequentially.

Do not immediately mass-convert everything.

The required order is:

```text
1. Inspect environment
2. Audit all LaTeX sources
3. Produce conceptual course map
4. Initialize Quarto structure
5. Obtain a successful empty/skeleton render
6. Convert one representative pilot chapter
7. Validate pilot chapter
8. Establish bibliography + figure conventions
9. Convert remaining chapters sequentially
10. Perform global notation/cross-reference audit
11. Perform full local render
12. Initialize GitHub publication
13. Add GitHub Actions deployment
14. Validate public site
15. Clean repository
16. Report remaining conversion issues
```

At every stage, prefer a small validated change to a large speculative rewrite.

---

# 40. Final reporting required from the coding agent

At the end of each substantial conversion session, report:

```text
Completed
- ...

Validated
- ...

Files created/changed
- ...

Open issues
- ...

Substantive academic points requiring instructor review
- ...

Next recommended conversion step
- ...
```

Explicitly distinguish:

```text
technical issue
```

from:

```text
possible academic/content issue
```

Never silently resolve the latter through guesswork.

---

# 41. Recommended first execution prompt

Once this file and all source teaching material are present in the repository, begin with the following instruction:

```text
Read COURSE_BUILD_SPEC.md completely before making changes.

Then inspect the entire repository and all supplied LaTeX/Beamer source material,
including recursively included .tex files, bibliography files, custom style files,
figures, TikZ/PGFPlots sources, and code.

Execute only Phases 1–7 of the specification for now:

1. inspect the environment;
2. audit all source material;
3. propose the conceptual architecture of the online course;
4. initialize the Quarto project;
5. obtain a successful skeleton render;
6. select and fully convert one representative pilot chapter;
7. validate that pilot chapter.

Do not mass-convert the remaining lectures yet.

Preserve all original sources.
Do not change substantive econometric content without explicitly flagging it.
Do not invent missing references, equations, figures, or explanations.

After completing the pilot, report:
- repository architecture;
- source inventory;
- proposed chapter map;
- files changed;
- render/test results;
- unresolved technical issues;
- substantive points requiring instructor review;
- recommendations before full conversion.
```

This instruction is deliberately conservative. The goal is to validate the conversion architecture on one representative lecture before allowing a coding agent to transform the entire course.

---

# Core principle

> The objective is not to put Beamer slides on the internet. The objective is to use the existing slides as the authoritative source for constructing a rigorous, navigable, maintainable and eventually reproducible online macroeconometrics textbook.

Content fidelity comes first.

Web readability comes second.

Automation and visual sophistication come only after both are secured.
