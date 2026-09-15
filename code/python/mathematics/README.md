# Mathematical foundations: text, figures and verification

The chapter combines motivating examples with explicit abstract definitions,
propositions and proofs. The editorial reference
was the locally supplied *MFH_Ranson_Souffron.pdf*: economic motivation, explicit
distinctions, a worked argument, then qualifications. The reference PDF is not
redistributed. English is retained to match the book and reference.

## Reproduce the visual assets

From the repository root, create the optional rendering environment:

    micromamba env create -f code/python/mathematics/environment.yml
    micromamba run -n mathematics-animations python code/python/mathematics/figures.py
    micromamba run -n mathematics-animations python code/python/mathematics/render.py LinearMap MatrixComposition Stability Taylor Jacobian KKT Sampling NormalArea Fourier

Conda or mamba can also create the environment from this file. Rendering requires
FFmpeg with libx264, Cairo, Pango and DejaVu Sans, provided by the Manim
conda-forge dependency stack. No TeX installation is required: scene labels use
Pango text, while the book typesets its full formulas with MathJax.

The nine H.264 movies are 1280×720 at 30 frames per second, with browser-friendly
pixel format and fast-start metadata. Each has an informative PNG poster.
Fifteen still diagrams are SVGs with searchable text. All data are illustrative,
with fixed seeds for random figures. The generation scripts do not fetch data.

The book commits the rendered assets. Ordinary publication needs neither Manim
nor StatAnim and does not regenerate videos. This keeps deployment independent
of native graphics packages and preserves exactly the reviewed media.

## StatAnim integration

Manim Community is pinned to 0.19.0. StatAnim is pinned to Git commit
784e0bea9a3f1a1538a265b35a8b26e58d08eba8 (package version 0.1.9).
The source repository is https://github.com/rishabhbhartiya/statanim.

The Sampling and NormalArea scenes use its actual NormalCurve3D curve layer.
Upstream geometry lies in the x-z plane and normalises its sampled density peak
to a supplied height. Our adapter rotates the geometry into the chapter's 2D
axes, and sets that height to the true Normal peak times the vertical data-unit
scale. The geometry test checks this correction. Library annotation layers,
approximate CDFs and Q-Q envelopes are not used.

Sampling curves are exact transformed Gamma densities for standardised
Exponential sample means. Transitions cross-fade consecutive exact densities;
an interpolated frame is not labelled as another exact sample size.
Normal rejection boundaries use SciPy's quantile. The displayed tails truncate
at ±4; the annotated probabilities include the negligible mass beyond the frame.

## Browser figures and accessibility

The five native JavaScript explorations live in interactive/math/ and
load only in Chapter 0. They cover matrix transformations, log Taylor
approximations, a scalar KKT cap, gradient descent and Normal conjugate updating.
They do not load Pyodide.
The existing separate Interactive Lab retains its Python estimators.

The matrix explorer provides seven presets, four editable entries and a manual
progress slider. It displays (1-t)I+tA, not A raised to a power. In particular,
interpolating to a rotation is not itself a pure rotation. The input and output
grids share a coordinate scale, fixed throughout the progress slider's motion.
Column images, their sum, area change and singularity are explained in text.
Invalid entries retain the last valid figure and produce a validation message.

Chapter-local MathJax 4.0.0 and matching New Computer Modern font data provide
inline and display line breaking. Long derivations are also split explicitly in
the source. A resize observer recomputes display line breaks as the reading column
changes width. Neither inline symbols nor displayed equations are scroll controls;
there are no horizontal scrolling arrows and no clipped formulas.

Sliders have labels, keyboard operation, textual numerical output, reset and SVG
download. Curves use colour plus labels/line patterns. Videos never autoplay and
pause when they leave the viewport; their playback controls permit pausing and
seeking. The surrounding prose and poster images explain the visual content
without motion. Print styling substitutes posters and retains interactive SVGs
in the currently selected state.

## Verification

    python -m pip install -r interactive/requirements.txt -r code/python/mathematics/requirements-checks.txt
    python -m pytest code/python/mathematics/test_mathematics.py -q
    OPENBLAS_NUM_THREADS=1 python -m pytest interactive/tests -q
    python interactive/tools/check_coverage.py
    quarto render
    python interactive/tests/rendered.py
    python -m http.server 8765 --directory _book

In another terminal:

    python code/python/mathematics/browser_check.py

The browser test requires Playwright Chromium and its system dependencies. The
existing LAB_TEST_INTERCEPTED_TLS flag accommodates a local inspecting proxy;
ordinary CI leaves it unset. MATH_BASE_URL can point the same tests at the public
book after deployment. Screenshots and downloaded test figures go to /tmp.

Numerical checks compare all three constrained-allocation regimes with an
independent SLSQP solution, including junctions and multiplier signs. Symbolic
checks verify the Jacobian, exact nonlinear remainder, household first-order
condition, and constrained Hessian. Other checks cover density integrals and
moments, Taylor bounds, eigenvalues, the projection exercise, posterior updating,
the Markov invariant distribution and Fourier reconstruction. A rendering-only
test checks the actual StatAnim geometry; CI skips it when Manim is absent.
Additional exact-algebra tests check span coordinates, dependence, matrix-vector
products, noncommuting compositions, scalar/matrix OLS equivalence, completed
squares, omitted-variable bias and the Gauss-Markov covariance comparison.

Browser checks cover MathJax errors, local links and anchors, movie decoding and
playback, formula fixtures, all slider endpoints, keyboard actions, downloads,
390/768/1440-pixel layouts, no-script reading, reduced motion and printing.
GitHub Actions runs the mathematical and browser checks before publishing.

These tests verify computations and delivery, not arbitrary theorem statements.
The prose audit below is a separate mathematical review.

## Mathematical review

- Vector spaces are defined by their operations and axioms, not only by arrows.
  Span, subspaces, independent/dependent/spanning families, bases and dimension
  are distinguished, including examples where only one property holds.
- Matrix multiplication is derived from column images and composition. Input,
  intermediate and output dimensions are stated; transpose is not inverse.
- Scalar OLS precedes matrix OLS. The five conditional finite-sample assumptions
  have stable anchors and a separate relaxation paragraph each. Assumption 4a
  concerns diagonal variances, 4b off-diagonal covariances; only together do they
  give spherical errors. Normality is not used in the Gauss-Markov proof.
- Limits quantify over all nearby points; multivariate path examples distinguish
  disproving a limit from proving it.
- Partial and directional derivatives are separated from total differentiability.
  Gradient/Jacobian orientation and input/output dimensions are explicit.
- Taylor formulas distinguish little-o, finite remainder bounds and analytic
  power series. The multivariate result follows from restriction to a line.
- Local inversion states openness, C1 regularity, a solution and nonsingular
  endogenous Jacobian. Unit-circle nonlinear dynamics remain inconclusive.
- Optimisation distinguishes existence, necessity, sufficiency and uniqueness.
  The minimisation convention uses inequalities g≤0 and nonnegative multipliers.
  LICQ/MFCQ, failure of qualifications, convex sufficiency, Slater, the critical
  cone and the Lagrangian Hessian are addressed separately.
- Right-hand-side shadow-value derivatives have the correct sign. Active sets
  and zero-multiplier binding constraints are explicit at both transitions.
- Expectations require integrability; multivariate integration states Tonelli,
  Fubini, change-of-variables and domination conditions.
- The i.i.d. strong LLN needs integrability, not an artificially stronger variance
  assumption; CLT statements state finite positive variance. GMM consistency
  requires uniform control and identification, beyond a pointwise LLN.
- OLS distinguishes strict conditional exogeneity from time-series moment
  arguments. HC0 scaling is for coefficients, not their sqrt(T)-scaled errors.
- Wold innovations are linear projection errors, not generally martingale
  differences. AR stationarity distinguishes stationary initialisation and
  causal/noncausal solutions. A spectral measure need not have a density.

References: Lebl, *Basic Analysis* I–II (https://www.jirka.org/ra/);
Boyd and Vandenberghe, *Convex Optimization*, chapters 2–5
(https://web.stanford.edu/~boyd/cvxbook/); Nocedal and Wright, *Numerical
Optimization*, second edition, chapter 12
(https://users.iems.northwestern.edu/~nocedal/book/); and the probability,
asymptotic and time-series references already cited in the chapter.
